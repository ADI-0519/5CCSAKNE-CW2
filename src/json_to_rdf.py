# Code to convert normalised JSON data to RDF format

import re

from rdflib import RDF, XSD, Graph, Literal, Namespace

EX = Namespace("http://example.org/news/")
SCHEMA = Namespace("http://schema.org/")

# Maps controlled predicate names to RDF predicate URIs
PREDICATE_URI_MAP = {
    "mentions": EX.mentions,
    "developed_by": EX.developedBy,
    "announced": EX.announced,
    "located_in": EX.locatedIn,
    "authored_by": EX.authoredBy,
    "published_by": EX.publishedBy,
    "uses_technology": EX.usesTechnology,
    "involved_in": EX.involvedIn,
    "part_of": EX.partOf,
}


def _slug(text):
    """Convert arbitrary text to a URI-safe slug."""
    return re.sub(r"[^a-zA-Z0-9_-]", "_", text.strip())


def _entity_uri(name, entities_sets):
    """Return the typed entity URI for a name by checking which entity list it belongs to."""
    if name in entities_sets["organizations"]:
        return EX[f"org/{_slug(name)}"]
    if name in entities_sets["people"]:
        return EX[f"person/{_slug(name)}"]
    if name in entities_sets["locations"]:
        return EX[f"location/{_slug(name)}"]
    if name in entities_sets["technologies"]:
        return EX[f"tech/{_slug(name)}"]
    if name in entities_sets["topics"]:
        return EX[f"topic/{_slug(name)}"]
    return EX[f"entity/{_slug(name)}"]


def convert_json_to_rdf(normalised_data):
    print("[RDF] Starting RDF conversion stage...")

    if not normalised_data:
        raise ValueError("[RDF] No normalised data to convert.")

    g = Graph()
    g.bind("ex", EX)
    g.bind("schema", SCHEMA)

    for record in normalised_data:
        article_uri = EX[f"article/{record['id']}"]

        # --- Article node ---
        g.add((article_uri, RDF.type, SCHEMA.NewsArticle))
        g.add((article_uri, SCHEMA.headline, Literal(record["title"])))
        g.add((article_uri, SCHEMA.url, Literal(record["url"])))
        g.add(
            (
                article_uri,
                SCHEMA.datePublished,
                Literal(record["published_at"], datatype=XSD.dateTime),
            )
        )
        g.add((article_uri, SCHEMA.publisher, Literal(record["source_name"])))

        if record.get("author"):
            g.add((article_uri, SCHEMA.author, Literal(record["author"])))
        if record.get("summary"):
            g.add((article_uri, SCHEMA.description, Literal(record["summary"])))

        entities = record.get("entities", {})

        # Pre-compute sets for fast lookup when resolving relation URIs
        entities_sets = {k: set(v) for k, v in entities.items()}

        # --- Entity nodes ---
        for org in entities.get("organizations", []):
            org_uri = EX[f"org/{_slug(org)}"]
            g.add((org_uri, RDF.type, SCHEMA.Organization))
            g.add((org_uri, SCHEMA.name, Literal(org)))

        for person in entities.get("people", []):
            person_uri = EX[f"person/{_slug(person)}"]
            g.add((person_uri, RDF.type, SCHEMA.Person))
            g.add((person_uri, SCHEMA.name, Literal(person)))

        for loc in entities.get("locations", []):
            loc_uri = EX[f"location/{_slug(loc)}"]
            g.add((loc_uri, RDF.type, SCHEMA.Place))
            g.add((loc_uri, SCHEMA.name, Literal(loc)))

        for tech in entities.get("technologies", []):
            tech_uri = EX[f"tech/{_slug(tech)}"]
            g.add((tech_uri, RDF.type, EX.Technology))
            g.add((tech_uri, SCHEMA.name, Literal(tech)))

        for topic in entities.get("topics", []):
            topic_uri = EX[f"topic/{_slug(topic)}"]
            g.add((topic_uri, RDF.type, EX.Topic))
            g.add((topic_uri, SCHEMA.name, Literal(topic)))

        # --- Relation triples ---
        for rel in record.get("relations", []):
            pred_name = rel["predicate"]
            pred_uri = PREDICATE_URI_MAP.get(pred_name)
            if pred_uri is None:
                raise ValueError(f"[RDF] Unknown predicate: {pred_name!r}")

            subj = rel["subject"]
            obj = rel["object"]

            subj_uri = article_uri if subj == record["id"] else _entity_uri(subj, entities_sets)
            obj_uri = _entity_uri(obj, entities_sets)

            g.add((subj_uri, pred_uri, obj_uri))

    print(f"[RDF] Graph contains {len(g)} triples.")
    return g
