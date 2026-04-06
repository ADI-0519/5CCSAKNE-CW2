import re

from rdflib import RDF, XSD, Graph, Literal

from src.build_ontology import CORE, NEWS, SCHEMA

EX = NEWS

PREDICATE_URI_MAP = {
    "developed_by": EX.developedBy,
    "announced": EX.announced,
    "authored_by": EX.hasAuthor,
    "published_by": EX.publishedBy,
    "uses_technology": EX.usesTechnology,
    "involved_in": EX.involvedIn,
    "part_of": EX.partOf,
}

SUPERPROPERTY_URI_MAP = {
    EX.hasAuthor: SCHEMA.author,
    EX.publishedBy: SCHEMA.publisher,
    EX.hasTopic: SCHEMA.about,
    EX.mentionsPerson: SCHEMA.mentions,
    EX.mentionsOrganisation: SCHEMA.mentions,
    EX.mentionsLocation: SCHEMA.mentions,
    EX.mentionsTechnology: SCHEMA.mentions,
    EX.publishedDate: SCHEMA.datePublished,
    EX.articleURL: SCHEMA.url,
}


def _slug(text):
    """Convert arbitrary text to a URI-safe slug."""
    return re.sub(r"[^a-zA-Z0-9_-]", "_", text.strip())


def _add_relation(graph, subject_uri, predicate_uri, object_value):
    graph.add((subject_uri, predicate_uri, object_value))
    superproperty = SUPERPROPERTY_URI_MAP.get(predicate_uri)
    if superproperty is not None:
        graph.add((subject_uri, superproperty, object_value))


def _add_typed_entity(graph, entity_uri, label, rdf_types):
    for rdf_type in dict.fromkeys(rdf_types):
        graph.add((entity_uri, RDF.type, rdf_type))
    graph.add((entity_uri, SCHEMA.name, Literal(label)))


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


def _entity_types(name, entities_sets):
    if name in entities_sets["organizations"]:
        return (EX.Organisation, SCHEMA.Organization)
    if name in entities_sets["people"]:
        return (SCHEMA.Person,)
    if name in entities_sets["locations"]:
        return (EX.Location, CORE.Place)
    if name in entities_sets["technologies"]:
        return (EX.Technology, SCHEMA.Thing)
    if name in entities_sets["topics"]:
        return (EX.Topic, SCHEMA.Thing)
    return (SCHEMA.Thing,)


def _relation_uri(predicate_name, subject_is_article, object_name, entities_sets):
    if predicate_name == "mentions":
        if subject_is_article:
            if object_name in entities_sets["organizations"]:
                return EX.mentionsOrganisation
            if object_name in entities_sets["people"]:
                return EX.mentionsPerson
            if object_name in entities_sets["locations"]:
                return EX.mentionsLocation
            if object_name in entities_sets["technologies"]:
                return EX.mentionsTechnology
            if object_name in entities_sets["topics"]:
                return EX.hasTopic
        return SCHEMA.mentions

    if predicate_name == "located_in":
        return EX.mentionsLocation if subject_is_article else EX.locatedIn

    return PREDICATE_URI_MAP.get(predicate_name)


def convert_json_to_rdf(normalised_data):
    print("[RDF] Starting RDF conversion stage...")

    if not normalised_data:
        raise ValueError("[RDF] No normalised data to convert.")

    g = Graph()
    g.bind("news", EX)
    g.bind("schema", SCHEMA)
    g.bind("core", CORE)

    for record in normalised_data:
        article_uri = EX[f"article/{record['id']}"]
        url_literal = Literal(record["url"], datatype=XSD.anyURI)
        published_literal = Literal(record["published_at"], datatype=XSD.dateTime)
        publisher_uri = EX[f"org/{_slug(record['source_name'])}"]

        # --- Article node ---
        g.add((article_uri, RDF.type, EX.NewsArticle))
        g.add((article_uri, RDF.type, SCHEMA.NewsArticle))
        g.add((article_uri, SCHEMA.headline, Literal(record["title"])))
        _add_relation(g, article_uri, EX.articleURL, url_literal)
        _add_relation(g, article_uri, EX.publishedDate, published_literal)
        if record.get("updated_at"):
            g.add(
                (
                    article_uri,
                    EX.hasUpdateTimestamp,
                    Literal(record["updated_at"], datatype=XSD.dateTime),
                )
            )
        if record.get("section"):
            g.add((article_uri, EX.hasSection, Literal(record["section"])))
            g.add((article_uri, SCHEMA.articleSection, Literal(record["section"])))
        if record.get("word_count") is not None:
            g.add((article_uri, EX.wordCount, Literal(record["word_count"], datatype=XSD.integer)))

        article_type_hint = (record.get("raw_article_type_hint") or "").lower()
        if article_type_hint == "breaking":
            g.add((article_uri, RDF.type, EX.BreakingNewsArticle))
        elif article_type_hint == "opinion":
            g.add((article_uri, RDF.type, EX.OpinionArticle))

        _add_typed_entity(
            g,
            publisher_uri,
            record["source_name"],
            (EX.NewsOrganisation, EX.Organisation, SCHEMA.Organization),
        )
        _add_relation(g, article_uri, EX.publishedBy, publisher_uri)

        if record.get("author"):
            author_uri = EX[f"person/{_slug(record['author'])}"]
            _add_typed_entity(g, author_uri, record["author"], (EX.Journalist, SCHEMA.Person))
            _add_relation(g, article_uri, EX.hasAuthor, author_uri)

        if record.get("summary"):
            g.add((article_uri, SCHEMA.description, Literal(record["summary"])))

        entities = record.get("entities", {})
        entities_sets = {k: set(v) for k, v in entities.items()}

        # --- Entity nodes ---
        for org in entities.get("organizations", []):
            org_uri = EX[f"org/{_slug(org)}"]
            _add_typed_entity(g, org_uri, org, (EX.Organisation, SCHEMA.Organization))

        for person in entities.get("people", []):
            person_uri = EX[f"person/{_slug(person)}"]
            _add_typed_entity(g, person_uri, person, (SCHEMA.Person,))

        for loc in entities.get("locations", []):
            loc_uri = EX[f"location/{_slug(loc)}"]
            _add_typed_entity(g, loc_uri, loc, (EX.Location, CORE.Place))

        for tech in entities.get("technologies", []):
            tech_uri = EX[f"tech/{_slug(tech)}"]
            _add_typed_entity(g, tech_uri, tech, (EX.Technology, SCHEMA.Thing))

        for topic in entities.get("topics", []):
            topic_uri = EX[f"topic/{_slug(topic)}"]
            _add_typed_entity(g, topic_uri, topic, (EX.Topic, SCHEMA.Thing))

        # --- Relation triples ---
        for rel in record.get("relations", []):
            pred_name = rel["predicate"]
            subj = rel["subject"]
            obj = rel["object"]
            subject_is_article = subj == record["id"]

            pred_uri = _relation_uri(pred_name, subject_is_article, obj, entities_sets)
            if pred_uri is None:
                raise ValueError(f"[RDF] Unknown predicate: {pred_name!r}")

            if subject_is_article:
                subj_uri = article_uri
            elif pred_name == "published_by" and subj == record["source_name"]:
                subj_uri = publisher_uri
            elif pred_name == "authored_by" and subj == record.get("author"):
                subj_uri = EX[f"person/{_slug(subj)}"]
            else:
                subj_uri = _entity_uri(subj, entities_sets)

            if pred_name == "published_by" and obj == record["source_name"]:
                obj_uri = publisher_uri
            elif pred_name == "authored_by" and obj == record.get("author"):
                obj_uri = EX[f"person/{_slug(obj)}"]
                _add_typed_entity(g, obj_uri, obj, (EX.Journalist, SCHEMA.Person))
            else:
                obj_uri = _entity_uri(obj, entities_sets)
                if obj_uri not in g.subjects():
                    _add_typed_entity(g, obj_uri, obj, _entity_types(obj, entities_sets))

            _add_relation(g, subj_uri, pred_uri, obj_uri)

    print(f"[RDF] Graph contains {len(g)} triples.")
    return g
