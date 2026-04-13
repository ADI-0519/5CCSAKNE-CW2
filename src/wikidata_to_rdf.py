"""Map Wikidata structured records directly to RDF triples.

This module performs direct structured-to-RDF mapping without any NLP.
Each Wikidata record has typed fields that map to ontology classes and
properties through explicit field-to-property rules.

This contrasts with the Guardian textual pipeline, which requires NLP
extraction (regex NER, keyword matching, LLM-assisted extraction) to
produce the same kinds of triples from unstructured article body text.
"""

import re

from rdflib import RDF, RDFS, XSD, Graph, Literal, Namespace, URIRef

NEWS = Namespace("http://example.org/news#")
SCHEMA = Namespace("https://schema.org/")
WD = Namespace("http://www.wikidata.org/entity/")


def slugify(text):
    return re.sub(r"[^a-zA-Z0-9_-]", "_", str(text).strip())


def person_uri(name):
    return NEWS[f"person/{slugify(name)}"]


def organisation_uri(name):
    return NEWS[f"organisation/{slugify(name)}"]


def location_uri(name):
    return NEWS[f"location/{slugify(name)}"]


def add_literal(graph, subject, predicate, value, datatype=None):
    if value is None or value == "":
        return
    if datatype is not None:
        graph.add((subject, predicate, Literal(value, datatype=datatype)))
    else:
        graph.add((subject, predicate, Literal(value)))


def add_politician(graph, record):
    """Map a Wikidata politician record to RDF triples."""
    name = record.get("name")
    if not name:
        return

    uri = person_uri(name)
    graph.add((uri, RDF.type, NEWS.Politician))
    graph.add((uri, RDF.type, SCHEMA.Person))
    add_literal(graph, uri, SCHEMA.name, name)

    if record.get("description"):
        add_literal(graph, uri, SCHEMA.description, record["description"])

    if record.get("wikidata_uri"):
        graph.add((uri, RDFS.seeAlso, URIRef(record["wikidata_uri"])))

    if record.get("gender"):
        add_literal(graph, uri, SCHEMA.gender, record["gender"])

    if record.get("date_of_birth"):
        dob = record["date_of_birth"][:10]
        if len(dob) == 10 and dob[4] == "-":
            add_literal(graph, uri, SCHEMA.birthDate, dob, XSD.date)

    # Link politician to their party
    party_name = record.get("party")
    if party_name:
        party_uri = organisation_uri(party_name)
        graph.add((party_uri, RDF.type, NEWS.PoliticalParty))
        graph.add((party_uri, RDF.type, NEWS.Organisation))
        graph.add((party_uri, RDF.type, SCHEMA.Organization))
        add_literal(graph, party_uri, SCHEMA.name, party_name)
        graph.add((uri, SCHEMA.memberOf, party_uri))

    # Link politician to their constituency
    constituency_name = record.get("constituency")
    if constituency_name:
        const_uri = location_uri(constituency_name)
        graph.add((const_uri, RDF.type, NEWS.Location))
        graph.add((const_uri, RDF.type, SCHEMA.Place))
        add_literal(graph, const_uri, SCHEMA.name, constituency_name)


def add_party(graph, record):
    """Map a Wikidata political party record to RDF triples."""
    name = record.get("name")
    if not name:
        return

    uri = organisation_uri(name)
    graph.add((uri, RDF.type, NEWS.PoliticalParty))
    graph.add((uri, RDF.type, NEWS.Organisation))
    graph.add((uri, RDF.type, SCHEMA.Organization))
    add_literal(graph, uri, SCHEMA.name, name)

    if record.get("description"):
        add_literal(graph, uri, SCHEMA.description, record["description"])

    if record.get("wikidata_uri"):
        graph.add((uri, RDFS.seeAlso, URIRef(record["wikidata_uri"])))

    if record.get("inception"):
        inception = record["inception"][:10]
        if len(inception) == 10 and inception[4] == "-":
            add_literal(graph, uri, SCHEMA.foundingDate, inception, XSD.date)

    if record.get("dissolved"):
        dissolved = record["dissolved"][:10]
        if len(dissolved) == 10 and dissolved[4] == "-":
            add_literal(graph, uri, SCHEMA.dissolutionDate, dissolved, XSD.date)

    if record.get("headquarters"):
        hq_uri = location_uri(record["headquarters"])
        graph.add((hq_uri, RDF.type, NEWS.Location))
        graph.add((hq_uri, RDF.type, SCHEMA.Place))
        add_literal(graph, hq_uri, SCHEMA.name, record["headquarters"])
        graph.add((uri, SCHEMA.location, hq_uri))

    if record.get("leader"):
        leader_uri = person_uri(record["leader"])
        graph.add((leader_uri, RDF.type, NEWS.Politician))
        graph.add((leader_uri, RDF.type, SCHEMA.Person))
        add_literal(graph, leader_uri, SCHEMA.name, record["leader"])


def add_government_body(graph, record):
    """Map a Wikidata government body record to RDF triples."""
    name = record.get("name")
    if not name:
        return

    uri = organisation_uri(name)
    graph.add((uri, RDF.type, NEWS.GovernmentBody))
    graph.add((uri, RDF.type, NEWS.Organisation))
    graph.add((uri, RDF.type, SCHEMA.Organization))
    add_literal(graph, uri, SCHEMA.name, name)

    if record.get("description"):
        add_literal(graph, uri, SCHEMA.description, record["description"])

    if record.get("wikidata_uri"):
        graph.add((uri, RDFS.seeAlso, URIRef(record["wikidata_uri"])))

    if record.get("headquarters"):
        hq_uri = location_uri(record["headquarters"])
        graph.add((hq_uri, RDF.type, NEWS.Location))
        graph.add((hq_uri, RDF.type, SCHEMA.Place))
        add_literal(graph, hq_uri, SCHEMA.name, record["headquarters"])
        graph.add((uri, SCHEMA.location, hq_uri))


def convert_wikidata_to_rdf(wikidata_payload):
    """Convert a full Wikidata payload to an RDF graph.

    This is a direct structured mapping: each JSON field maps to a specific
    ontology class or property without NLP processing.
    """
    print("[WIKIDATA-RDF] Starting structured-to-RDF mapping...")

    graph = Graph()
    graph.bind("news", NEWS)
    graph.bind("schema", SCHEMA)

    politicians = wikidata_payload.get("politicians", [])
    parties = wikidata_payload.get("political_parties", [])
    bodies = wikidata_payload.get("government_bodies", [])

    for record in politicians:
        add_politician(graph, record)

    for record in parties:
        add_party(graph, record)

    for record in bodies:
        add_government_body(graph, record)

    print(
        f"[WIKIDATA-RDF] Mapped {len(politicians)} politicians, "
        f"{len(parties)} parties, {len(bodies)} government bodies"
    )
    print(f"[WIKIDATA-RDF] Graph contains {len(graph)} triples.")
    return graph
