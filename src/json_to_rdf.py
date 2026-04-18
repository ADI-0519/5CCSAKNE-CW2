import re
from datetime import date as _date

from rdflib import RDF, XSD, Graph, Literal, Namespace

NEWS = Namespace("http://example.org/news#")
SCHEMA = Namespace("https://schema.org/")

OFFICIAL_SOURCE_SYSTEMS = {"parliament", "hansard", "govuk", "gov.uk"}
GENERIC_EVENT_NAMES = {
    "Budget",
    "Election",
    "Policy Announcement",
    "Parliamentary Debate",
    "Ministerial Statement",
}
DEPARTMENT_KEYWORDS = {
    "department",
    "office",
    "treasury",
    "ministry",
    "cabinet",
    "home office",
    "foreign office",
    "department for",
}
PARLIAMENTARY_BODY_KEYWORDS = {
    "commons",
    "lords",
    "parliament",
    "committee",
    "house of commons",
    "house of lords",
}


def slugify(text):
    return re.sub(r"[^a-zA-Z0-9_-]", "_", str(text).strip())


def article_uri(article_id):
    return NEWS[f"article/{slugify(article_id)}"]


def source_record_uri(source_system, record_id):
    return NEWS[f"source-record/{slugify(source_system)}/{slugify(record_id)}"]


def person_uri(name):
    return NEWS[f"person/{slugify(name)}"]


def organisation_uri(name):
    return NEWS[f"organisation/{slugify(name)}"]


def location_uri(name):
    return NEWS[f"location/{slugify(name)}"]


def topic_uri(name):
    return NEWS[f"topic/{slugify(name)}"]


def normalise_event_date(value):
    if not value:
        return None
    value = str(value).strip()
    candidate = (
        value
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", value)
        else (value[:10] if len(value) >= 10 else value)
    )
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", candidate):
        return None
    try:
        _date.fromisoformat(candidate)
    except ValueError:
        return None
    return candidate


def event_uri(event_name, event_date=None, event_location=None, article_id=None):
    key_parts = [slugify(event_name)]
    normalised_date = normalise_event_date(event_date)
    if normalised_date:
        key_parts.append(slugify(normalised_date))
    if event_location:
        key_parts.append(slugify(event_location))
    if article_id and event_name in GENERIC_EVENT_NAMES:
        key_parts.append(str(article_id)[:8])
    return NEWS[f"event/{'_'.join(key_parts)}"]


def add_literal(graph, subject, predicate, value, datatype=None):
    if value is None or value == "":
        return
    if datatype is not None:
        graph.add((subject, predicate, Literal(value, datatype=datatype)))
    else:
        graph.add((subject, predicate, Literal(value)))


def add_name(graph, subject, name):
    add_literal(graph, subject, SCHEMA.name, name)


def bind_namespaces(graph):
    graph.bind("news", NEWS)
    graph.bind("schema", SCHEMA)


def event_name_keywords(text):
    return {token.lower() for token in re.findall(r"[A-Za-z][A-Za-z'-]+", str(text or ""))}


def canonical_event_name(event, record):
    raw_name = str(event.get("name") or "").strip()
    if not raw_name:
        return ""

    lowered_name = raw_name.lower()
    raw_keywords = event_name_keywords(raw_name)
    event_type = str(event.get("type") or "").strip()
    topics = {str(topic).strip() for topic in ((record.get("entities") or {}).get("topics") or [])}
    headline = str(record.get("title") or "")
    summary = str(record.get("summary") or "")
    context_keywords = event_name_keywords(" ".join([headline, summary]))

    if "spending review" in lowered_name:
        return "Spending Review"
    if "spring statement" in lowered_name:
        return "Spring Statement"
    if (
        "debate" in raw_keywords
        or "pmqs" in raw_keywords
        or "commons" in raw_keywords
        or "lords" in raw_keywords
    ):
        return "Parliamentary Debate"
    if "statement" in raw_keywords and (
        "ministerial" in raw_keywords or "minister" in raw_keywords or "department" in raw_keywords
    ):
        return "Ministerial Statement"
    if "budget" in raw_keywords or "budget" in lowered_name:
        return "Budget"
    if "election" in raw_keywords or "campaign" in raw_keywords or "poll" in raw_keywords:
        return "Election"

    # use broader article context only as a fallback when the event label itself is generic
    if raw_name in {"Policy Announcement", "News Event", "Event"}:
        if "budget" in context_keywords:
            return "Budget"
        if (
            "election" in context_keywords
            or "campaign" in context_keywords
            or "poll" in context_keywords
        ):
            return "Election"
        if (
            "debate" in context_keywords
            or "pmqs" in context_keywords
            or "commons" in context_keywords
            or "lords" in context_keywords
        ):
            return "Parliamentary Debate"
        if "statement" in context_keywords and (
            "ministerial" in context_keywords
            or "minister" in context_keywords
            or "department" in context_keywords
        ):
            return "Ministerial Statement"

    if raw_name in {"Policy Announcement", "News Event"}:
        if {"Government Policy", "Parliament", "Immigration", "Healthcare"} & topics:
            return "Policy Announcement"

    if event_type == "EconomicEvent" and (
        {"Economic Policy", "Public Spending", "Taxation"} & topics
    ):
        return "Budget"

    return raw_name


def classify_government_body(name):
    lowered = str(name or "").strip().lower()
    if any(keyword in lowered for keyword in PARLIAMENTARY_BODY_KEYWORDS):
        return NEWS.ParliamentaryBody
    if any(keyword in lowered for keyword in DEPARTMENT_KEYWORDS):
        return NEWS.GovernmentDepartment
    return NEWS.GovernmentBody


def classify_source_record_class(source_system):
    lowered = str(source_system or "").strip().lower()
    if lowered in {"parliament", "hansard"}:
        return NEWS.ParliamentSourceRecord
    if lowered in {"govuk", "gov.uk"}:
        return NEWS.GovernmentSourceRecord
    return NEWS.SourceRecord


def is_official_source_system(source_system):
    return str(source_system or "").strip().lower() in OFFICIAL_SOURCE_SYSTEMS


def classify_event(record, event):
    raw_name = str(event.get("name") or "").strip()
    lowered_name = raw_name.lower()
    topics = {str(topic).strip() for topic in ((record.get("entities") or {}).get("topics") or [])}
    government_bodies = {
        str(name).strip()
        for name in ((record.get("entities") or {}).get("government_bodies") or [])
    }
    source_system = str(record.get("source_system") or "").strip().lower()
    keywords = event_name_keywords(
        " ".join([raw_name, str(record.get("title") or ""), str(record.get("summary") or "")])
    )

    event_class = NEWS.PolicyEvent

    if source_system in {"parliament", "hansard"}:
        event_class = NEWS.ParliamentaryEvent
    elif source_system in {"govuk", "gov.uk"}:
        event_class = NEWS.GovernmentPolicyEvent
    elif (
        "debate" in keywords
        or "pmqs" in keywords
        or "commons" in keywords
        or "lords" in keywords
        or "Parliament" in topics
    ):
        event_class = NEWS.ParliamentaryEvent
    elif government_bodies or {"Government Policy", "Public Spending", "Economic Policy"} & topics:
        event_class = NEWS.GovernmentPolicyEvent

    if "debate" in keywords or "pmqs" in keywords:
        return NEWS.ParliamentaryDebate
    if (
        "statement" in keywords
        and ("ministerial" in keywords or "minister" in keywords or government_bodies)
    ) or "ministerial statement" in lowered_name:
        return NEWS.MinisterialStatement

    return event_class


def add_article_node(graph, record):
    uri = article_uri(record["id"])
    graph.add((uri, RDF.type, NEWS.NewsArticle))
    add_literal(graph, uri, SCHEMA.headline, record.get("title"))
    add_literal(graph, uri, NEWS.articleURL, record.get("url"), XSD.anyURI)
    add_literal(graph, uri, SCHEMA.url, record.get("url"), XSD.anyURI)
    add_literal(graph, uri, NEWS.publishedDate, record.get("published_at"), XSD.dateTime)
    add_literal(graph, uri, SCHEMA.datePublished, record.get("published_at"), XSD.dateTime)
    return uri


def add_publisher(graph, article, record):
    source_name = record.get("source_name")
    if not source_name:
        return None

    publisher = organisation_uri(source_name)
    graph.add((publisher, RDF.type, NEWS.NewsOrganisation))
    add_name(graph, publisher, source_name)
    graph.add((article, NEWS.publishedBy, publisher))
    graph.add((article, SCHEMA.publisher, publisher))
    return publisher


def add_author(graph, article, record):
    author_name = record.get("author")
    if not author_name:
        return None

    author = person_uri(author_name)
    graph.add((author, RDF.type, NEWS.Journalist))
    add_name(graph, author, author_name)
    graph.add((article, NEWS.hasAuthor, author))
    graph.add((article, SCHEMA.author, author))
    return author


def add_political_actors(graph, record):
    actor_uris = []
    for name in sorted(set((record.get("entities") or {}).get("politicians", []))):
        uri = person_uri(name)
        graph.add((uri, RDF.type, NEWS.PoliticalActor))
        graph.add((uri, RDF.type, SCHEMA.Person))
        add_name(graph, uri, name)
        actor_uris.append(uri)
    return actor_uris


def add_political_parties(graph, record):
    party_uris = []
    for name in sorted(set((record.get("entities") or {}).get("political_parties", []))):
        uri = organisation_uri(name)
        graph.add((uri, RDF.type, NEWS.PoliticalParty))
        add_name(graph, uri, name)
        party_uris.append(uri)
    return party_uris


def add_government_bodies(graph, record):
    body_uris = []
    for name in sorted(set((record.get("entities") or {}).get("government_bodies", []))):
        uri = organisation_uri(name)
        graph.add((uri, RDF.type, NEWS.GovernmentBody))
        body_type = classify_government_body(name)
        if body_type != NEWS.GovernmentBody:
            graph.add((uri, RDF.type, body_type))
        add_name(graph, uri, name)
        body_uris.append(uri)
    return body_uris


def add_policy_topics(graph, record):
    topic_uris = []
    for name in sorted(set((record.get("entities") or {}).get("topics", []))):
        uri = topic_uri(name)
        graph.add((uri, RDF.type, NEWS.PolicyTopic))
        add_name(graph, uri, name)
        topic_uris.append(uri)
    return topic_uris


def add_locations(graph, record):
    location_uris = {}
    for name in sorted(set((record.get("entities") or {}).get("locations", []))):
        uri = location_uri(name)
        graph.add((uri, RDF.type, NEWS.Location))
        add_name(graph, uri, name)
        location_uris[name] = uri
    return location_uris


def add_source_record(graph, record):
    source_system = record.get("source_system")
    if not source_system:
        return None

    uri = source_record_uri(source_system, record["id"])
    graph.add((uri, RDF.type, NEWS.SourceRecord))
    source_class = classify_source_record_class(source_system)
    if source_class != NEWS.SourceRecord:
        graph.add((uri, RDF.type, source_class))
    # SPARQL needs explicit superclass types since there is no reasoner
    if source_class in (NEWS.ParliamentSourceRecord, NEWS.GovernmentSourceRecord):
        graph.add((uri, RDF.type, NEWS.OfficialSourceRecord))

    add_literal(graph, uri, NEWS.sourceIdentifier, record.get("id"), XSD.string)
    add_literal(graph, uri, NEWS.sourceSystem, source_system, XSD.string)
    add_literal(graph, uri, NEWS.sourceTitle, record.get("title"), XSD.string)
    add_name(graph, uri, record.get("title") or record.get("id"))
    return uri


def add_events(
    graph,
    article,
    record,
    actor_uris,
    body_uris,
    topic_uris,
    location_uris,
    source_record,
):
    for event in record.get("event_candidates", []):
        raw_name = event.get("name")
        if not raw_name:
            continue

        canonical_name = canonical_event_name(event, record) or raw_name
        event_date = normalise_event_date(event.get("date")) or normalise_event_date(
            record.get("published_at")
        )
        event_location = event.get("location")
        uri = event_uri(canonical_name, event_date, event_location, record.get("id"))
        event_class = classify_event(record, event)

        graph.add((uri, RDF.type, NEWS.PolicyEvent))
        if event_class != NEWS.PolicyEvent:
            graph.add((uri, RDF.type, event_class))
        add_name(graph, uri, canonical_name)

        graph.add((uri, NEWS.reportedByArticle, article))
        for actor_uri in actor_uris:
            graph.add((uri, NEWS.involvesActor, actor_uri))
        for body_uri in body_uris:
            graph.add((uri, NEWS.involvesGovernmentBody, body_uri))
            if (
                event_class == NEWS.MinisterialStatement
                and (body_uri, RDF.type, NEWS.GovernmentDepartment) in graph
            ):
                graph.add((uri, NEWS.issuedByDepartment, body_uri))
        for topic_uri_value in topic_uris:
            graph.add((uri, NEWS.concernsPolicyTopic, topic_uri_value))

        if event_date:
            add_literal(graph, uri, NEWS.occursOnDate, event_date, XSD.date)
        if event_location:
            location_uri_value = location_uris.get(event_location)
            if location_uri_value is None:
                location_uri_value = location_uri(event_location)
                graph.add((location_uri_value, RDF.type, NEWS.Location))
                add_name(graph, location_uri_value, event_location)
            graph.add((uri, NEWS.occursInLocation, location_uri_value))

        if event_class in {NEWS.ParliamentaryEvent, NEWS.ParliamentaryDebate}:
            for body_uri in body_uris:
                if (body_uri, RDF.type, NEWS.ParliamentaryBody) in graph:
                    graph.add((uri, NEWS.occursInParliamentaryBody, body_uri))

        if source_record is not None and is_official_source_system(record.get("source_system")):
            graph.add((uri, NEWS.representedInOfficialSource, source_record))


def convert_json_to_rdf(normalised_data):
    print("[RDF] Starting RDF conversion stage...")

    if not normalised_data:
        raise ValueError("[RDF] No normalised data to convert.")

    graph = Graph()
    bind_namespaces(graph)

    for record in normalised_data:
        article = add_article_node(graph, record)
        add_publisher(graph, article, record)
        add_author(graph, article, record)
        actor_uris = add_political_actors(graph, record)
        add_political_parties(graph, record)
        body_uris = add_government_bodies(graph, record)
        topic_uris = add_policy_topics(graph, record)
        location_uris = add_locations(graph, record)
        source_record = add_source_record(graph, record)
        add_events(
            graph,
            article,
            record,
            actor_uris,
            body_uris,
            topic_uris,
            location_uris,
            source_record,
        )

    print(f"[RDF] Graph contains {len(graph)} triples.")
    return graph
