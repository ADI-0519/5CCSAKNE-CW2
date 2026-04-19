import re
from datetime import date as _date

from rdflib import RDF, XSD, Graph, Literal, Namespace

NEWS = Namespace("http://example.org/news#")
SCHEMA = Namespace("https://schema.org/")


def slugify(text):
    return re.sub(r"[^a-zA-Z0-9_-]", "_", str(text).strip())


def article_uri(article_id):
    return NEWS[f"article/{slugify(article_id)}"]


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


def event_uri(event_name, event_date=None, event_location=None):
    key_parts = [slugify(event_name)]
    normalized_date = normalise_event_date(event_date)
    if normalized_date:
        key_parts.append(slugify(normalized_date))
    if event_location:
        key_parts.append(slugify(event_location))
    return NEWS[f"event/{'_'.join(key_parts)}"]


def sentiment_uri(name):
    return NEWS[slugify(name)]


def add_literal(graph, subject, predicate, value, datatype=None):
    if value is None or value == "":
        return
    if datatype is not None:
        graph.add((subject, predicate, Literal(value, datatype=datatype)))
    else:
        graph.add((subject, predicate, Literal(value)))


def add_name(graph, subject, name):
    add_literal(graph, subject, SCHEMA.name, name)


def event_name_keywords(text):
    return {token.lower() for token in re.findall(r"[A-Za-z][A-Za-z'-]+", str(text or ""))}


def canonical_event_name(event, record):
    raw_name = str(event.get("name") or "").strip()
    if not raw_name:
        return ""

    lowered_name = raw_name.lower()
    event_type = str(event.get("type") or "NewsEvent").strip()
    topics = {str(topic).strip() for topic in (record.get("entities", {}) or {}).get("topics", [])}
    headline = str(record.get("title") or "")
    summary = str(record.get("summary") or "")
    keywords = event_name_keywords(" ".join([raw_name, headline, summary]))

    if "spending review" in lowered_name:
        return "Spending Review"
    if "spring statement" in lowered_name:
        return "Spring Statement"
    if "budget" in keywords or "budget" in lowered_name:
        return "Budget"
    if (
        "election" in keywords
        or "campaign" in keywords
        or "poll" in keywords
        or "Election" in topics
    ):
        return "Election"
    if (
        "vote" in keywords
        or "pmqs" in keywords
        or "parliamentary" in keywords
        or "debate" in keywords
        or "Parliament" in topics
    ):
        return "Parliamentary Vote"
    if event_type == "EconomicEvent" and (
        {"Economic Policy", "Public Spending", "Taxation"} & topics
    ):
        return "Budget"
    if event_type == "PoliticalEvent" and (
        {"Government Policy", "Parliament", "Immigration", "Healthcare"} & topics
    ):
        return "Policy Announcement"

    return raw_name


def bind_namespaces(graph):
    graph.bind("news", NEWS)
    graph.bind("schema", SCHEMA)


def add_sentiment_scheme(graph):
    for label in ("Positive", "Negative", "Neutral"):
        uri = sentiment_uri(label)
        graph.add((uri, RDF.type, NEWS.Sentiment))
        add_name(graph, uri, label)


def add_article_node(graph, record):
    uri = article_uri(record["id"])
    article_type = record.get("article_type") or "NewsArticle"

    graph.add((uri, RDF.type, NEWS.NewsArticle))
    if article_type != "NewsArticle":
        graph.add((uri, RDF.type, NEWS[article_type]))

    add_literal(graph, uri, SCHEMA.headline, record.get("title"))
    add_literal(graph, uri, NEWS.articleURL, record.get("url"))
    add_literal(graph, uri, SCHEMA.url, record.get("url"))
    add_literal(graph, uri, NEWS.publishedDate, record.get("published_at"), XSD.dateTime)
    add_literal(graph, uri, SCHEMA.datePublished, record.get("published_at"), XSD.dateTime)
    add_literal(graph, uri, NEWS.hasUpdateTimestamp, record.get("updated_at"), XSD.dateTime)
    add_literal(graph, uri, SCHEMA.dateModified, record.get("updated_at"), XSD.dateTime)
    add_literal(graph, uri, NEWS.hasSection, record.get("section"))
    add_literal(graph, uri, SCHEMA.articleSection, record.get("section"))
    add_literal(graph, uri, SCHEMA.description, record.get("summary"))
    add_literal(graph, uri, NEWS.wordCount, record.get("word_count"), XSD.integer)
    add_literal(graph, uri, SCHEMA.wordCount, record.get("word_count"), XSD.integer)
    return uri


def add_publisher(graph, article, record):
    source_name = record.get("source_name")
    if not source_name:
        return None

    publisher = organisation_uri(source_name)
    graph.add((publisher, RDF.type, NEWS.Organisation))
    graph.add((publisher, RDF.type, NEWS.NewsOrganisation))
    add_name(graph, publisher, source_name)
    graph.add((article, NEWS.publishedBy, publisher))
    graph.add((article, SCHEMA.publisher, publisher))
    return publisher


def add_author(graph, article, record, publisher):
    author_name = record.get("author")
    if not author_name:
        return None

    author = person_uri(author_name)
    graph.add((author, RDF.type, NEWS.Journalist))
    add_name(graph, author, author_name)
    graph.add((article, NEWS.hasAuthor, author))
    graph.add((article, SCHEMA.author, author))
    if publisher is not None:
        graph.add((author, NEWS.worksFor, publisher))
        graph.add((author, SCHEMA.worksFor, publisher))
    return author


def add_person_entities(graph, article, entities):
    politicians = set(entities.get("politicians", []))
    all_people = set(entities.get("people", []))

    for name in sorted(all_people):
        uri = person_uri(name)
        graph.add((uri, RDF.type, SCHEMA.Person))
        if name in politicians:
            graph.add((uri, RDF.type, NEWS.Politician))
        add_name(graph, uri, name)
        graph.add((article, NEWS.mentionsPerson, uri))
        graph.add((article, SCHEMA.mentions, uri))


def add_organisation_entities(graph, article, entities):
    parties = set(entities.get("political_parties", []))
    bodies = set(entities.get("government_bodies", []))
    organisations = set(entities.get("organizations", []))

    for name in sorted(organisations):
        uri = organisation_uri(name)
        graph.add((uri, RDF.type, NEWS.Organisation))
        if name in parties:
            graph.add((uri, RDF.type, NEWS.PoliticalParty))
        if name in bodies:
            graph.add((uri, RDF.type, NEWS.GovernmentBody))
        add_name(graph, uri, name)
        graph.add((article, NEWS.mentionsOrganisation, uri))
        graph.add((article, SCHEMA.mentions, uri))


def add_location_entities(graph, article, entities):
    for name in sorted(set(entities.get("locations", []))):
        uri = location_uri(name)
        graph.add((uri, RDF.type, NEWS.Location))
        graph.add((uri, RDF.type, SCHEMA.Place))
        add_name(graph, uri, name)
        graph.add((article, NEWS.mentionsLocation, uri))
        graph.add((article, SCHEMA.mentions, uri))


def add_topic_entities(graph, article, entities):
    for name in sorted(set(entities.get("topics", []))):
        uri = topic_uri(name)
        graph.add((uri, RDF.type, NEWS.Topic))
        add_name(graph, uri, name)
        graph.add((article, NEWS.hasTopic, uri))
        graph.add((article, SCHEMA.about, uri))


def add_sentiment(graph, article, record):
    sentiment_name = record.get("sentiment") or "Neutral"
    sentiment = sentiment_uri(sentiment_name)
    graph.add((article, NEWS.hasSentiment, sentiment))


def add_events(graph, article, record):
    created_events = []
    for event in record.get("event_candidates", []):
        event_name = event.get("name")
        if not event_name:
            continue

        uri = event_uri(event_name, event.get("date"), event.get("location"))
        event_type = event.get("type") or "NewsEvent"
        canonical_name = canonical_event_name(event, record) or event_name

        graph.add((uri, RDF.type, NEWS.NewsEvent))
        if event_type != "NewsEvent":
            graph.add((uri, RDF.type, NEWS[event_type]))
        add_name(graph, uri, canonical_name)
        if canonical_name != event_name:
            add_literal(graph, uri, SCHEMA.alternateName, event_name)
        graph.add((article, NEWS.coversEvent, uri))

        if event.get("date"):
            add_literal(
                graph,
                uri,
                NEWS.eventDate,
                normalise_event_date(event["date"]),
                XSD.date,
            )

        if event.get("location"):
            loc_uri = location_uri(event["location"])
            graph.add((loc_uri, RDF.type, NEWS.Location))
            graph.add((loc_uri, RDF.type, SCHEMA.Place))
            add_name(graph, loc_uri, event["location"])
            graph.add((uri, NEWS.eventLocation, loc_uri))

        created_events.append(uri)

    return created_events


def build_follow_up_links(graph, records):
    groups = {}
    for record in records:
        for candidate in record.get("follow_up_candidates", []):
            match_key = candidate.get("match_key")
            if not match_key:
                continue
            groups.setdefault(match_key, []).append(record)

    for records_with_key in groups.values():
        ordered = sorted(records_with_key, key=lambda item: item.get("published_at") or "")
        for current, follow_up in zip(ordered, ordered[1:]):
            current_uri = article_uri(current["id"])
            follow_uri = article_uri(follow_up["id"])
            graph.add((current_uri, NEWS.hasFollowUp, follow_uri))


def convert_json_to_rdf(normalised_data):
    print("[RDF] Starting RDF conversion stage...")

    if not normalised_data:
        raise ValueError("[RDF] No normalised data to convert.")

    graph = Graph()
    bind_namespaces(graph)
    add_sentiment_scheme(graph)

    for record in normalised_data:
        article = add_article_node(graph, record)
        publisher = add_publisher(graph, article, record)
        add_author(graph, article, record, publisher)
        entities = record.get("entities", {})
        add_person_entities(graph, article, entities)
        add_organisation_entities(graph, article, entities)
        add_location_entities(graph, article, entities)
        add_topic_entities(graph, article, entities)
        add_sentiment(graph, article, record)
        add_events(graph, article, record)

    build_follow_up_links(graph, normalised_data)

    print(f"[RDF] Graph contains {len(graph)} triples.")
    return graph
