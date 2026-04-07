import argparse
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from rdflib import RDF, XSD, Graph, Literal

from src.build_ontology import NEWS, SCHEMA
from src.config import CONFIG
from src.openai_client import maybe_complete_article_with_openai
from src.run_queries import load_kg

DEFAULT_OUTPUT_PATH = Path("kg/generated/completed_kg.ttl")
DEFAULT_INPUT_KG_CANDIDATES = (
    Path("kg/generated/prototype_kg.ttl"),
    Path("kg/generated/new_kg.ttl"),
)

POSITIVE_KEYWORDS = {
    "advance",
    "advances",
    "breakthrough",
    "boost",
    "growth",
    "improve",
    "improved",
    "innovation",
    "launch",
    "launched",
    "released",
    "success",
    "surge",
    "win",
}

NEGATIVE_KEYWORDS = {
    "attack",
    "ban",
    "breach",
    "concern",
    "concerns",
    "crisis",
    "decline",
    "declines",
    "drop",
    "dropped",
    "lawsuit",
    "layoff",
    "loss",
    "risk",
    "warning",
}

FOLLOW_UP_STOPWORDS = {
    "a",
    "after",
    "analysis",
    "and",
    "bill",
    "budget",
    "comment",
    "commentary",
    "debate",
    "different",
    "government",
    "minister",
    "ministers",
    "new",
    "officials",
    "on",
    "opinion",
    "plan",
    "policy",
    "proposal",
    "response",
    "review",
    "separate",
    "the",
    "today",
    "transport",
    "treasury",
    "update",
}

SECTION_RULES = {
    "Politics": {
        "politics",
        "government",
        "policy",
        "regulation",
        "election",
        "parliament",
        "westminster",
    },
    "Business": {"finance", "economy", "budget", "tax", "treasury", "spending"},
    "Health": {"health", "healthcare", "hospital", "nhs"},
    "Energy": {"climate", "energy", "net zero", "gas", "renewable"},
}

OPINION_KEYWORDS = {"analysis", "comment", "editorial", "opinion", "view"}
BREAKING_KEYWORDS = {"breaking", "developing", "live", "urgent", "just in"}

ADDITIONAL_TOPIC_RULES = {
    "Economic Policy": {"budget", "fiscal", "inflation", "interest rates", "growth"},
    "Public Spending": {"public spending", "spending review", "funding", "spending cuts"},
    "Government Policy": {"policy", "bill", "legislation", "white paper", "proposal"},
    "Election": {"election", "campaign", "polling", "ballot"},
}


def normalize_whitespace(text):
    return " ".join(text.split())


def slug_text(text):
    return re.sub(r"[^a-zA-Z0-9_-]", "_", text.strip())


def text_terms(text):
    return {term.lower() for term in re.findall(r"[A-Za-z][A-Za-z\\-]+", text)}


def contains_any(text, patterns):
    lowered = text.lower()
    return any(pattern in lowered for pattern in patterns)


def first_literal(graph, subject, predicate):
    for value in graph.objects(subject, predicate):
        return value
    return None


def text_value(graph, subject, predicate):
    literal = first_literal(graph, subject, predicate)
    return "" if literal is None else str(literal)


def named_entities(graph, subject, predicate):
    names = []
    for obj in graph.objects(subject, predicate):
        name = first_literal(graph, obj, SCHEMA.name)
        if name is not None:
            names.append(str(name))
    return names


def infer_sentiment(text):
    terms = text_terms(text)
    positive_hits = len(terms & POSITIVE_KEYWORDS)
    negative_hits = len(terms & NEGATIVE_KEYWORDS)

    if positive_hits > negative_hits:
        return NEWS.Positive
    if negative_hits > positive_hits:
        return NEWS.Negative
    return NEWS.Neutral


def infer_section(article_text, topic_names):
    combined_text = normalize_whitespace(" ".join([article_text, *topic_names]))

    for section, keywords in SECTION_RULES.items():
        if contains_any(combined_text, keywords):
            return section
    return "General"


def infer_article_subtypes(article_text, section):
    terms = text_terms(article_text)
    subtypes = set()

    if OPINION_KEYWORDS & terms:
        subtypes.add(NEWS.OpinionArticle)
    if BREAKING_KEYWORDS & terms:
        subtypes.add(NEWS.BreakingNewsArticle)
    if "live" in terms and section == "Politics":
        subtypes.add(NEWS.BreakingNewsArticle)

    return subtypes


def infer_additional_topics(article_text, topic_names, organization_names):
    existing_topics = {topic.lower() for topic in topic_names}
    combined_text = normalize_whitespace(" ".join([article_text, *organization_names]))

    inferred = set()
    for topic_label, triggers in ADDITIONAL_TOPIC_RULES.items():
        if topic_label in existing_topics:
            continue
        if contains_any(combined_text, triggers):
            inferred.add(topic_label)

    return sorted(inferred)


def choose_default_input_kg():
    for candidate in DEFAULT_INPUT_KG_CANDIDATES:
        if candidate.exists():
            return candidate
    raise FileNotFoundError(
        "No source KG file found. Expected one of: "
        + ", ".join(str(candidate) for candidate in DEFAULT_INPUT_KG_CANDIDATES)
    )


def parse_datetime_value(value):
    return datetime.fromisoformat(str(value).replace("Z", "+00:00"))


def article_metadata(graph, article_uri):
    publisher = next(graph.objects(article_uri, NEWS.publishedBy), None)
    published_date = first_literal(graph, article_uri, NEWS.publishedDate)
    organizations = set(graph.objects(article_uri, NEWS.mentionsOrganisation))
    topics = set(graph.objects(article_uri, NEWS.hasTopic))
    events = set(graph.objects(article_uri, NEWS.coversEvent))
    article_types = set(graph.objects(article_uri, RDF.type))
    headline = text_value(graph, article_uri, SCHEMA.headline)
    headline_terms = {
        term for term in text_terms(headline) if term not in FOLLOW_UP_STOPWORDS and len(term) >= 4
    }

    return {
        "article": article_uri,
        "publisher": publisher,
        "published_date": None if published_date is None else parse_datetime_value(published_date),
        "organizations": organizations,
        "topics": topics,
        "events": events,
        "article_types": article_types,
        "headline_terms": headline_terms,
    }


def infer_follow_up_links(graph, max_gap_days=7):
    article_nodes = sorted(
        graph.subjects(RDF.type, NEWS.NewsArticle),
        key=lambda uri: (article_metadata(graph, uri)["published_date"], str(uri)),
    )
    metadata = {article_uri: article_metadata(graph, article_uri) for article_uri in article_nodes}
    follow_ups = []

    for earlier in article_nodes:
        earlier_data = metadata[earlier]
        if earlier_data["published_date"] is None:
            continue

        candidates = []
        for later in article_nodes:
            if later == earlier:
                continue

            later_data = metadata[later]
            if later_data["published_date"] is None:
                continue
            if later_data["published_date"] <= earlier_data["published_date"]:
                continue

            day_gap = (later_data["published_date"] - earlier_data["published_date"]).days
            if day_gap > max_gap_days:
                continue

            shared_orgs = earlier_data["organizations"] & later_data["organizations"]
            shared_topics = earlier_data["topics"] & later_data["topics"]
            shared_events = earlier_data["events"] & later_data["events"]
            shared_headline_terms = earlier_data["headline_terms"] & later_data["headline_terms"]
            same_publisher = (
                earlier_data["publisher"] is not None
                and later_data["publisher"] is not None
                and earlier_data["publisher"] == later_data["publisher"]
            )
            earlier_is_opinion = NEWS.OpinionArticle in earlier_data["article_types"]
            later_is_opinion = NEWS.OpinionArticle in later_data["article_types"]
            earlier_is_breaking = NEWS.BreakingNewsArticle in earlier_data["article_types"]
            later_is_breaking = NEWS.BreakingNewsArticle in later_data["article_types"]

            # Follow-up links should represent editorial progression, not just broad topical overlap.
            # We therefore require either a shared event, or a stricter combination of same publisher,
            # shared organisations, and shared topics.
            if shared_events:
                score = (len(shared_events) * 5) + len(shared_orgs) + len(shared_topics)
                candidates.append((score, later_data["published_date"], later))
                continue

            if not same_publisher:
                continue
            if earlier_is_opinion:
                continue
            if not shared_orgs or not shared_topics:
                continue
            if not shared_headline_terms and not shared_events:
                continue
            if not (earlier_is_breaking or later_is_breaking):
                continue
            if len(shared_topics) < 2 and not (later_is_opinion and not earlier_is_opinion):
                continue

            score = (len(shared_orgs) * 3) + (len(shared_topics) * 2) + len(shared_headline_terms)
            if later_is_opinion and not earlier_is_opinion:
                score += 1
            candidates.append((score, later_data["published_date"], later))

        if candidates:
            _, _, best_later = max(candidates, key=lambda item: (item[0], item[1]))
            follow_ups.append((earlier, best_later))

    return follow_ups


def apply_openai_completion(article_key, article_payload, heuristic_result):
    llm_result = maybe_complete_article_with_openai(article_key, article_payload, heuristic_result)
    if not llm_result:
        return heuristic_result

    merged = dict(heuristic_result)

    sentiment = llm_result.get("sentiment")
    if sentiment in {"Positive", "Negative", "Neutral"}:
        merged["sentiment"] = sentiment

    section = str(llm_result.get("section") or "").strip()
    if section:
        merged["section"] = section

    article_types = set(merged["article_types"])
    article_types.update(
        article_type
        for article_type in llm_result.get("article_types", [])
        if article_type in {"NewsArticle", "OpinionArticle", "BreakingNewsArticle"}
    )
    merged["article_types"] = sorted(article_types)

    additional_topics = set(merged["additional_topics"])
    additional_topics.update(
        topic
        for topic in llm_result.get("additional_topics", [])
        if topic in CONFIG["TOPIC_GROUPS"]
    )
    merged["additional_topics"] = sorted(additional_topics)

    return merged


def enrich_graph(graph):
    enriched = Graph()
    for prefix, namespace in graph.namespace_manager.namespaces():
        enriched.bind(prefix, namespace)
    for triple in graph:
        enriched.add(triple)

    article_nodes = set(enriched.subjects(RDF.type, NEWS.NewsArticle))
    topic_nodes = defaultdict(lambda: None)

    for article_uri in article_nodes:
        headline = text_value(enriched, article_uri, SCHEMA.headline)
        description = text_value(enriched, article_uri, SCHEMA.description)
        article_text = normalize_whitespace(
            " ".join(part for part in (headline, description) if part)
        )

        topic_names = named_entities(enriched, article_uri, NEWS.hasTopic)
        organization_names = named_entities(enriched, article_uri, NEWS.mentionsOrganisation)
        existing_word_count = first_literal(enriched, article_uri, NEWS.wordCount)
        existing_section = first_literal(enriched, article_uri, NEWS.hasSection)

        if article_text:
            if existing_word_count is None:
                inferred_word_count = len(re.findall(r"\b\w+\b", article_text))
                enriched.set(
                    (
                        article_uri,
                        NEWS.wordCount,
                        Literal(inferred_word_count, datatype=XSD.integer),
                    )
                )

            heuristic_completion = apply_openai_completion(
                str(article_uri),
                {
                    "headline": headline,
                    "description": description,
                    "existing_topics": topic_names,
                    "organizations": organization_names,
                },
                {
                    "sentiment": str(infer_sentiment(article_text).split("#")[-1]),
                    "section": infer_section(article_text, topic_names),
                    "article_types": sorted(
                        str(article_type).split("#")[-1]
                        for article_type in infer_article_subtypes(
                            article_text, infer_section(article_text, topic_names)
                        )
                    ),
                    "additional_topics": infer_additional_topics(
                        article_text, topic_names, organization_names
                    ),
                },
            )

            sentiment_uri = NEWS[heuristic_completion["sentiment"]]
            enriched.set((article_uri, NEWS.hasSentiment, sentiment_uri))

            if existing_section is None:
                section = heuristic_completion["section"]
                if section:
                    enriched.set((article_uri, NEWS.hasSection, Literal(section)))

            for article_type_name in heuristic_completion["article_types"]:
                article_type = NEWS[article_type_name]
                enriched.add((article_uri, RDF.type, article_type))

        published_date = first_literal(enriched, article_uri, NEWS.publishedDate)
        if (
            published_date is not None
            and (article_uri, NEWS.hasUpdateTimestamp, None) not in enriched
        ):
            enriched.set((article_uri, NEWS.hasUpdateTimestamp, published_date))

        inferred_topics = []
        if article_text:
            inferred_topics = heuristic_completion["additional_topics"]
        for topic_label in inferred_topics:
            topic_uri = topic_nodes[topic_label]
            if topic_uri is None:
                topic_uri = NEWS[f"topic/{slug_text(topic_label)}"]
                topic_nodes[topic_label] = topic_uri
                enriched.add((topic_uri, RDF.type, NEWS.Topic))
                enriched.add((topic_uri, RDF.type, SCHEMA.Thing))
                enriched.set((topic_uri, SCHEMA.name, Literal(topic_label)))

            enriched.add((article_uri, NEWS.hasTopic, topic_uri))
            enriched.add((article_uri, SCHEMA.about, topic_uri))

    for earlier, later in infer_follow_up_links(enriched):
        enriched.add((earlier, NEWS.hasFollowUp, later))

    return enriched


def save_graph(graph, output_path):
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    graph.serialize(destination=str(output_file), format="turtle")


def build_arg_parser():
    parser = argparse.ArgumentParser(description="Complete or enrich a KG with inferred triples.")
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
