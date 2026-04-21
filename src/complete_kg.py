import argparse
import re
from datetime import date
from pathlib import Path

from rdflib import RDF, Graph

from src.build_ontology import NEWS, SCHEMA
from src.data_normalisation import normalise_name
from src.openai_client import (
    build_cache_path,
    load_cache_payload,
    request_structured_output,
    save_cache_payload,
)
from src.config import CONFIG
from src.run_queries import load_kg

DEFAULT_OUTPUT_PATH = Path("kg/generated/completed_kg.ttl")
DEFAULT_INPUT_KG_CANDIDATES = (
    Path("kg/generated/prototype_kg.ttl"),
    Path("kg/generated/new_kg.ttl"),
)

OFFICIAL_PUBLISHERS = {"UK Parliament", "GOV.UK"}
EVENT_MATCH_STOPWORDS = {
    "a",
    "an",
    "and",
    "announcement",
    "bill",
    "debate",
    "event",
    "for",
    "government",
    "in",
    "ministerial",
    "of",
    "on",
    "parliamentary",
    "policy",
    "review",
    "statement",
    "the",
    "to",
    "update",
}

RAG_RESPONSE_FORMAT = {
    "type": "json_schema",
    "name": "rag_completion",
    "strict": True,
    "schema": {
        "type": "object",
        "properties": {
            "proposed_actors": {"type": "array", "items": {"type": "string"}},
            "proposed_departments": {"type": "array", "items": {"type": "string"}},
            "proposed_topics": {
                "type": "array",
                "items": {"type": "string", "enum": sorted(CONFIG["TOPIC_GROUPS"].keys())},
            },
        },
        "required": ["proposed_actors", "proposed_departments", "proposed_topics"],
        "additionalProperties": False,
    },
}

RAG_INSTRUCTIONS = (
    "You are completing a UK politics knowledge graph. Given a policy event and "
    "retrieved source context, propose missing property values using only the "
    "declared vocabulary. Do not invent names not supported by the context. "
    "proposed_actors must be named individual politicians or political parties only, "
    "not departments, roles, or generic labels such as 'UK Government'. "
    "proposed_departments must be named UK government departments or official bodies only. "
    "proposed_topics must be chosen only from this list: "
    + str(sorted(CONFIG["TOPIC_GROUPS"].keys())) + ". "
    "Prefer specific topics over Government Policy, which should only be used "
    "when no other topic applies. "
    "Example of correct output: "
    '{"proposed_actors": ["Keir Starmer", "Labour Party"], '
    '"proposed_departments": ["Home Office"], '
    '"proposed_topics": ["Housing", "Government Policy"]}. '
    "Example of incorrect output: "
    '{"proposed_actors": ["UK Government", "Secretary of State"], '
    '"proposed_departments": [], "proposed_topics": []}. '
    "Return only JSON."
)

ACTOR_BLOCKLIST = {
    "agency", "authority", "board", "cabinet", "chair", "commission",
    "committee", "council", "department", "director", "government",
    "minister", "ministry", "office", "regulator", "secretary",
}

# retrieves articles, topics and sources linked to event through KG neighbourhood
RAG_CONTEXT_QUERY = """
SELECT DISTINCT ?headline ?publisherName ?topicName ?sourceTitle WHERE {
    OPTIONAL {
        ?event news:reportedByArticle ?article .
        ?article schema:headline ?headline .
        OPTIONAL {
            ?article news:publishedBy ?pub .
            ?pub schema:name ?publisherName .
        }
    }
    OPTIONAL {
        ?event news:concernsPolicyTopic ?topic .
        ?topic schema:name ?topicName .
    }
    OPTIONAL {
        ?event news:matchedToSourceRecord ?rec .
        ?rec news:sourceTitle ?sourceTitle .
    }
}
LIMIT 10
"""


def normalized_text(value):
    return normalise_name(value)


def slug_terms(text):
    cleaned = normalized_text(text).lower()
    return {
        term
        for term in re.findall(r"[a-z][a-z0-9'-]+", cleaned)
        if len(term) >= 3 and term not in EVENT_MATCH_STOPWORDS
    }


def first_literal(graph, subject, predicate):
    for value in graph.objects(subject, predicate):
        return value
    return None


def text_value(graph, subject, predicate):
    literal = first_literal(graph, subject, predicate)
    return "" if literal is None else normalized_text(str(literal))


def parse_date_literal(value):
    if value is None:
        return None

    text = str(value).strip()
    candidates = [text[:10], text]
    for candidate in candidates:
        try:
            return date.fromisoformat(candidate)
        except ValueError:
            continue
    return None


def choose_default_input_kg():
    for candidate in DEFAULT_INPUT_KG_CANDIDATES:
        if candidate.exists():
            return candidate
    raise FileNotFoundError(
        "No source KG file found. Expected one of: "
        + ", ".join(str(candidate) for candidate in DEFAULT_INPUT_KG_CANDIDATES)
    )


def event_metadata(graph, event_uri):
    article_uris = set(graph.objects(event_uri, NEWS.reportedByArticle))
    article_headlines = {
        text_value(graph, article_uri, SCHEMA.headline) for article_uri in article_uris
    }
    article_headlines.discard("")
    event_name = text_value(graph, event_uri, SCHEMA.name)
    topic_names = {
        text_value(graph, topic_uri, SCHEMA.name)
        for topic_uri in graph.objects(event_uri, NEWS.concernsPolicyTopic)
    }
    topic_names.discard("")

    return {
        "uri": event_uri,
        "name": event_name,
        "event_date": parse_date_literal(first_literal(graph, event_uri, NEWS.occursOnDate)),
        "reported_articles": article_uris,
        "article_headlines": article_headlines,
        "topics": topic_names,
        "already_represented": set(graph.objects(event_uri, NEWS.representedInOfficialSource)),
    }


def official_article_metadata(graph, article_uri):
    publisher_uri = first_literal(graph, article_uri, NEWS.publishedBy)
    publisher_name = (
        text_value(graph, publisher_uri, SCHEMA.name) if publisher_uri is not None else ""
    )
    return {
        "uri": article_uri,
        "headline": text_value(graph, article_uri, SCHEMA.headline),
        "publisher": publisher_name,
        "published_date": parse_date_literal(first_literal(graph, article_uri, NEWS.publishedDate)),
    }


def source_record_metadata(graph, record_uri):
    title = text_value(graph, record_uri, NEWS.sourceTitle) or text_value(
        graph, record_uri, SCHEMA.name
    )
    system = text_value(graph, record_uri, NEWS.sourceSystem).lower()
    return {"uri": record_uri, "title": title, "system": system}


def score_event_to_official_match(event_data, official_article, source_record):
    event_terms = slug_terms(event_data["name"])
    headline_terms = slug_terms(official_article["headline"])
    shared_terms = event_terms & headline_terms

    headline_score = 0
    if event_data["name"] and official_article["headline"]:
        if event_data["name"].lower() == official_article["headline"].lower():
            headline_score += 5
        elif event_data["name"].lower() in official_article["headline"].lower():
            headline_score += 3

    if event_data["article_headlines"]:
        exact_headline_overlap = any(
            article_headline.lower() == official_article["headline"].lower()
            for article_headline in event_data["article_headlines"]
        )
        if exact_headline_overlap:
            headline_score += 6

    source_title_score = 0
    if source_record["title"]:
        if event_data["name"] and event_data["name"].lower() == source_record["title"].lower():
            source_title_score += 5

    date_score = 0
    if event_data["event_date"] and official_article["published_date"]:
        day_gap = abs((event_data["event_date"] - official_article["published_date"]).days)
        if day_gap == 0:
            date_score += 3
        elif day_gap <= 2:
            date_score += 1
        else:
            return -1

    topic_bonus = 0
    if event_data["topics"]:
        headline_lower = official_article["headline"].lower()
        topic_bonus = sum(1 for topic in event_data["topics"] if topic.lower() in headline_lower)

    if not shared_terms and headline_score == 0 and source_title_score == 0:
        return -1

    return (len(shared_terms) * 2) + headline_score + source_title_score + date_score + topic_bonus


def build_official_indexes(graph):
    record_by_title = {}
    for record_uri in graph.subjects(RDF.type, NEWS.SourceRecord):
        record_data = source_record_metadata(graph, record_uri)
        if record_data["title"]:
            record_by_title.setdefault(record_data["title"].lower(), []).append(record_data)

    official_articles = []
    for article_uri in graph.subjects(RDF.type, NEWS.NewsArticle):
        article_data = official_article_metadata(graph, article_uri)
        if article_data["publisher"] in OFFICIAL_PUBLISHERS:
            official_articles.append(article_data)

    return official_articles, record_by_title


def add_reports_on_inverse(graph):
    added = 0
    for event_uri, _, article_uri in graph.triples((None, NEWS.reportedByArticle, None)):
        if (article_uri, NEWS.reportsOn, event_uri) not in graph:
            graph.add((article_uri, NEWS.reportsOn, event_uri))
            added += 1
    return added


def enrich_cross_source_links(graph):
    official_articles, record_by_title = build_official_indexes(graph)
    added_matched = 0
    added_represented = 0

    for event_uri in graph.subjects(RDF.type, NEWS.PolicyEvent):
        event_data = event_metadata(graph, event_uri)
        for source_record in event_data["already_represented"]:
            if (event_uri, NEWS.matchedToSourceRecord, source_record) not in graph:
                graph.add((event_uri, NEWS.matchedToSourceRecord, source_record))
                added_matched += 1

        if not event_data["name"]:
            continue

        best_match = None
        best_score = -1
        for official_article in official_articles:
            candidate_records = record_by_title.get(official_article["headline"].lower(), [])
            if not candidate_records:
                continue
            for source_record in candidate_records:
                score = score_event_to_official_match(event_data, official_article, source_record)
                if score > best_score:
                    best_score = score
                    best_match = source_record["uri"]

        if best_match is None or best_score < 4:
            continue

        if (event_uri, NEWS.matchedToSourceRecord, best_match) not in graph:
            graph.add((event_uri, NEWS.matchedToSourceRecord, best_match))
            added_matched += 1

        if (
            best_score >= 8
            and (event_uri, NEWS.representedInOfficialSource, best_match) not in graph
        ):
            graph.add((event_uri, NEWS.representedInOfficialSource, best_match))
            added_represented += 1

    return added_matched, added_represented



def enrich_with_rag(graph):
    added_actors = 0
    added_depts = 0
    added_topics = 0
    topic_index = {
        text_value(graph, t, SCHEMA.name): t
        for t in graph.subjects(RDF.type, NEWS.PolicyTopic)
    }

    for event_uri in graph.subjects(RDF.type, NEWS.PolicyEvent):
        has_actor = next(graph.objects(event_uri, NEWS.involvesActor), None) is not None
        has_body = next(graph.objects(event_uri, NEWS.involvesGovernmentBody), None) is not None
        has_topic = next(graph.objects(event_uri, NEWS.concernsPolicyTopic), None) is not None
        if has_actor and has_body and has_topic:
            continue

        event_name = text_value(graph, event_uri, SCHEMA.name)
        if not event_name:
            continue

        # retrieve: SPARQL query over KG to get triples linked to event
        rows = list(graph.query(
            RAG_CONTEXT_QUERY,
            initNs={"news": NEWS, "schema": SCHEMA},
            initBindings={"event": event_uri},
        ))

        headlines = {str(r.headline) for r in rows if r.headline}
        publishers = {str(r.publisherName) for r in rows if r.publisherName}
        topic_names = {str(r.topicName) for r in rows if r.topicName}
        source_titles = {str(r.sourceTitle) for r in rows if r.sourceTitle}

        if not any([headlines, publishers, topic_names, source_titles]):
            continue

        cache_path = build_cache_path("rag_completion", str(event_uri))
        result = load_cache_payload(cache_path)

        if result is None:
            event_type = "PolicyEvent"
            for rdf_type in graph.objects(event_uri, RDF.type):
                local = str(rdf_type).split("#")[-1]
                if local != "PolicyEvent":
                    event_type = local
                    break

            event_date = first_literal(graph, event_uri, NEWS.occursOnDate)

            # verbalise retrieved triples as natural language sentences
            parts = [f"'{event_name}' is a {event_type}"]
            if event_date:
                parts[0] += f" that occurred on {event_date}"
            if headlines:
                hl_str = ", ".join(f"'{h}'" for h in list(headlines)[:3])
                pub = next(iter(publishers), None)
                if pub:
                    parts.append(f"reported by '{pub}' via headlines: {hl_str}")
                else:
                    parts.append(f"reported via headlines: {hl_str}")
            if topic_names:
                parts.append(f"concerns the topics: {', '.join(sorted(topic_names))}")
            if source_titles:
                titles_str = ", ".join(f"'{t}'" for t in list(source_titles)[:2])
                parts.append(f"linked to official sources: {titles_str}")
            user_input = ". ".join(parts) + "."

            try:
                result = request_structured_output(RAG_INSTRUCTIONS, user_input, RAG_RESPONSE_FORMAT)
            except Exception as exc:
                print(f"[COMPLETE] RAG request failed for {event_uri}: {exc}")
                continue

            if result is None:
                continue
            save_cache_payload(cache_path, result)

        context_terms = set()
        for s in (headlines | publishers | topic_names | source_titles):
            context_terms |= slug_terms(s)

        for name in result.get("proposed_actors", []):
            if not name or not (slug_terms(name) & context_terms):
                continue
            if slug_terms(name) & ACTOR_BLOCKLIST:
                continue
            actor_slug = re.sub(r"[^a-z0-9]+", "_", normalise_name(name).lower()).strip("_")
            actor_uri = NEWS[actor_slug]
            if (event_uri, NEWS.involvesActor, actor_uri) not in graph:
                graph.add((event_uri, NEWS.involvesActor, actor_uri))
                added_actors += 1

        for name in result.get("proposed_departments", []):
            if not name or not (slug_terms(name) & context_terms):
                continue
            dept_slug = re.sub(r"[^a-z0-9]+", "_", normalise_name(name).lower()).strip("_")
            dept_uri = NEWS[dept_slug]
            if (event_uri, NEWS.involvesGovernmentBody, dept_uri) not in graph:
                graph.add((event_uri, NEWS.involvesGovernmentBody, dept_uri))
                added_depts += 1

        for name in result.get("proposed_topics", []):
            topic_uri = topic_index.get(name)
            if topic_uri is None:
                continue
            if (event_uri, NEWS.concernsPolicyTopic, topic_uri) not in graph:
                graph.add((event_uri, NEWS.concernsPolicyTopic, topic_uri))
                added_topics += 1

    return added_actors, added_depts, added_topics


def enrich_graph(graph):
    enriched = Graph()
    for prefix, namespace in graph.namespace_manager.namespaces():
        enriched.bind(prefix, namespace)
    for triple in graph:
        enriched.add(triple)

    inverse_count = add_reports_on_inverse(enriched)
    matched_count, represented_count = enrich_cross_source_links(enriched)
    actor_count, dept_count, topic_count = enrich_with_rag(enriched)

    if inverse_count:
        print(f"[COMPLETE] Added {inverse_count} reportsOn inverse links.")
    if matched_count:
        print(f"[COMPLETE] Added {matched_count} matchedToSourceRecord links.")
    if represented_count:
        print(f"[COMPLETE] Added {represented_count} representedInOfficialSource links.")
    print(f"[COMPLETE] RAG: added {actor_count} actor links, {dept_count} department links, {topic_count} topic links.")

    return enriched


def save_graph(graph, output_path):
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    graph.serialize(destination=str(output_file), format="turtle")


def build_arg_parser():
    parser = argparse.ArgumentParser(
        description="Enrich a KG with ontology-aligned completion links."
    )
    parser.add_argument(
        "--kg",
        type=Path,
        default=None,
        help="Path to the source KG file. Defaults to prototype_kg.ttl or new_kg.ttl if present.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_PATH,
        help="Path to the enriched Turtle output.",
    )
    return parser


def main():
    parser = build_arg_parser()
    args = parser.parse_args()

    kg_path = args.kg or choose_default_input_kg()
    graph = load_kg(kg_path)
    enriched = enrich_graph(graph)
    save_graph(enriched, args.output)

    print(f"[COMPLETE] Source KG: {kg_path}")
    print(f"[COMPLETE] Input triples: {len(graph)}")
    print(f"[COMPLETE] Output triples: {len(enriched)}")
    print(f"[COMPLETE] Saved enriched KG to {args.output}")


if __name__ == "__main__":
    main()
