import re
from datetime import date as _date

from rdflib import RDF, RDFS, XSD, Graph, Literal, Namespace, URIRef

from src.domain_knowledge import (
    canonicalise_government_body_name,
    canonicalise_political_party_name,
    classify_official_body_kind,
)

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
    name = record.get("name")
    if not name:
        return

    uri = person_uri(name)
    graph.add((uri, RDF.type, NEWS.PoliticalActor))
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
            try:
                _date.fromisoformat(dob)
                add_literal(graph, uri, SCHEMA.birthDate, dob, XSD.date)
            except ValueError:
                pass

    # link politician to their party
    party_name = canonicalise_political_party_name(record.get("party"))
    if party_name:
        party_uri = organisation_uri(party_name)
        graph.add((party_uri, RDF.type, NEWS.PoliticalParty))
        graph.add((party_uri, RDF.type, SCHEMA.Organization))
        add_literal(graph, party_uri, SCHEMA.name, party_name)
        graph.add((uri, NEWS.memberOfParty, party_uri))
        graph.add((uri, SCHEMA.memberOf, party_uri))

    # link politician to their constituency
    constituency_name = record.get("constituency")
    if constituency_name:
        const_uri = location_uri(constituency_name)
        graph.add((const_uri, RDF.type, NEWS.Location))
        graph.add((const_uri, RDF.type, SCHEMA.Place))
        add_literal(graph, const_uri, SCHEMA.name, constituency_name)


def add_party(graph, record):
    name = canonicalise_political_party_name(record.get("name"))
    if not name:
        return

    uri = organisation_uri(name)
    graph.add((uri, RDF.type, NEWS.PoliticalParty))
    graph.add((uri, RDF.type, SCHEMA.Organization))
    add_literal(graph, uri, SCHEMA.name, name)

    if record.get("description"):
        add_literal(graph, uri, SCHEMA.description, record["description"])

    if record.get("wikidata_uri"):
        graph.add((uri, RDFS.seeAlso, URIRef(record["wikidata_uri"])))

    if record.get("inception"):
        inception = record["inception"][:10]
        if len(inception) == 10 and inception[4] == "-":
            try:
                _date.fromisoformat(inception)
                add_literal(graph, uri, SCHEMA.foundingDate, inception, XSD.date)
            except ValueError:
                pass

    if record.get("dissolved"):
        dissolved = record["dissolved"][:10]
        if len(dissolved) == 10 and dissolved[4] == "-":
            try:
                _date.fromisoformat(dissolved)
                add_literal(graph, uri, SCHEMA.dissolutionDate, dissolved, XSD.date)
            except ValueError:
                pass

    if record.get("headquarters"):
        hq_uri = location_uri(record["headquarters"])
        graph.add((hq_uri, RDF.type, NEWS.Location))
        graph.add((hq_uri, RDF.type, SCHEMA.Place))
        add_literal(graph, hq_uri, SCHEMA.name, record["headquarters"])
        graph.add((uri, SCHEMA.location, hq_uri))

    if record.get("leader"):
        leader_uri = person_uri(record["leader"])
        graph.add((leader_uri, RDF.type, NEWS.PoliticalActor))
        graph.add((leader_uri, RDF.type, SCHEMA.Person))
        add_literal(graph, leader_uri, SCHEMA.name, record["leader"])


def add_government_body(graph, record):
    name = canonicalise_government_body_name(record.get("name"))
    if not name:
        return

    uri = organisation_uri(name)
    graph.add((uri, RDF.type, NEWS.OfficialBody))
    body_kind = classify_official_body_kind(name)
    if body_kind == "parliamentary_body":
        graph.add((uri, RDF.type, NEWS.ParliamentaryBody))
    elif body_kind == "government_department":
        graph.add((uri, RDF.type, NEWS.GovernmentDepartment))
        graph.add((uri, RDF.type, NEWS.GovernmentBody))
    else:
        graph.add((uri, RDF.type, NEWS.GovernmentBody))
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
