import argparse
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from rdflib import RDF, XSD, Graph, Literal

from src.build_ontology import NEWS, SCHEMA
from src.run_queries import choose_default_kg, load_kg

DEFAULT_OUTPUT_PATH = Path("kg/generated/completed_kg.ttl")

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

SECTION_RULES = {
    "Politics": {"politics", "government", "policy", "regulation", "election"},
    "Business": {"finance", "economy", "investment", "funding", "ipo", "merger"},
    "Climate": {"climate", "energy", "sustainability"},
    "Technology": {
        "ai",
        "artificial intelligence",
        "machine learning",
        "deep learning",
        "gpt",
        "robotics",
        "automation",
        "technology",
    },
}

OPINION_KEYWORDS = {"analysis", "comment", "editorial", "opinion", "view"}
BREAKING_KEYWORDS = {"breaking", "developing", "live", "urgent", "just in"}

ADDITIONAL_TOPIC_RULES = {
    "innovation": {"ai", "artificial intelligence", "machine learning", "deep learning", "gpt", "robotics", "automation"},
    "research": {"openai", "research", "model", "breakthrough"},
    "economy": {"market", "economy", "investment", "funding", "ipo"},
}


def _normalize_whitespace(text):
    return " ".join(text.split())


def _slug(text):
    return re.sub(r"[^a-zA-Z0-9_-]", "_", text.strip())


def _text_terms(text):
    return {term.lower() for term in re.findall(r"[A-Za-z][A-Za-z\\-]+", text)}


def _get_first_literal(graph, subject, predicate):
    for value in graph.objects(subject, predicate):
        return value
    return None


def _get_text(graph, subject, predicate):
    literal = _get_first_literal(graph, subject, predicate)
    return "" if literal is None else str(literal)


def _get_named_entities(graph, subject, predicate):
    names = []
    for obj in graph.objects(subject, predicate):
        name = _get_first_literal(graph, obj, SCHEMA.name)
        if name is not None:
            names.append(str(name))
    return names


def infer_sentiment(text):
    terms = _text_terms(text)
    positive_hits = len(terms & POSITIVE_KEYWORDS)
    negative_hits = len(terms & NEGATIVE_KEYWORDS)

    if positive_hits > negative_hits:
        return NEWS.Positive
    if negative_hits > positive_hits:
        return NEWS.Negative
    return NEWS.Neutral


def infer_section(article_text, topic_names, technology_names):
    topic_terms = {topic.lower() for topic in topic_names}
    tech_terms = {technology.lower() for technology in technology_names}
    terms = _text_terms(article_text) | topic_terms | tech_terms

    for section, keywords in SECTION_RULES.items():
        if keywords & terms:
            return section
    return "General"


def infer_article_subtypes(article_text, section):
    terms = _text_terms(article_text)
    subtypes = set()

    if OPINION_KEYWORDS & terms:
        subtypes.add(NEWS.OpinionArticle)
    if BREAKING_KEYWORDS & terms:
        subtypes.add(NEWS.BreakingNewsArticle)
    if "live" in terms and section == "Politics":
        subtypes.add(NEWS.BreakingNewsArticle)

    return subtypes


def infer_additional_topics(article_text, topic_names, technology_names, organization_names):
    existing_topics = {topic.lower() for topic in topic_names}
    joined_terms = _text_terms(article_text)
    joined_terms.update(technology.lower() for technology in technology_names)
    joined_terms.update(org.lower() for org in organization_names)

    inferred = set()
    for topic_label, triggers in ADDITIONAL_TOPIC_RULES.items():
        if topic_label in existing_topics:
            continue
        if joined_terms & triggers:
            inferred.add(topic_label)

    return sorted(inferred)


def _parse_datetime(value):
    return datetime.fromisoformat(str(value).replace("Z", "+00:00"))


def _article_metadata(graph, article_uri):
    publisher = next(graph.objects(article_uri, NEWS.publishedBy), None)
    published_date = _get_first_literal(graph, article_uri, NEWS.publishedDate)
    organizations = set(graph.objects(article_uri, NEWS.mentionsOrganisation))
    topics = set(graph.objects(article_uri, NEWS.hasTopic))

    return {
        "article": article_uri,
        "publisher": publisher,
        "published_date": None if published_date is None else _parse_datetime(published_date),
        "organizations": organizations,
        "topics": topics,
    }


def infer_follow_up_links(graph, max_gap_days=7):
    article_nodes = sorted(
        graph.subjects(RDF.type, NEWS.NewsArticle),
        key=lambda uri: (_article_metadata(graph, uri)["published_date"], str(uri)),
    )
    metadata = {article_uri: _article_metadata(graph, article_uri) for article_uri in article_nodes}
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
            same_publisher = (
                earlier_data["publisher"] is not None
                and later_data["publisher"] is not None
                and earlier_data["publisher"] == later_data["publisher"]
            )

            if shared_orgs and (shared_topics or same_publisher):
                score = (len(shared_orgs) * 2) + len(shared_topics) + (1 if same_publisher else 0)
                candidates.append((score, later_data["published_date"], later))

        if candidates:
            _, _, best_later = max(candidates, key=lambda item: (item[0], item[1]))
            follow_ups.append((earlier, best_later))

    return follow_ups


def enrich_graph(graph):
    enriched = Graph()
    for prefix, namespace in graph.namespace_manager.namespaces():
        enriched.bind(prefix, namespace)
    for triple in graph:
        enriched.add(triple)

    article_nodes = set(enriched.subjects(RDF.type, NEWS.NewsArticle))
    topic_nodes = defaultdict(lambda: None)

    for article_uri in article_nodes:
        headline = _get_text(enriched, article_uri, SCHEMA.headline)
        description = _get_text(enriched, article_uri, SCHEMA.description)
        article_text = _normalize_whitespace(" ".join(part for part in (headline, description) if part))

        topic_names = _get_named_entities(enriched, article_uri, NEWS.hasTopic)
        technology_names = _get_named_entities(enriched, article_uri, NEWS.mentionsTechnology)
        organization_names = _get_named_entities(enriched, article_uri, NEWS.mentionsOrganisation)

        if article_text:
            word_count = len(re.findall(r"\b\w+\b", article_text))
            enriched.set((article_uri, NEWS.wordCount, Literal(word_count, datatype=XSD.integer)))

            sentiment_uri = infer_sentiment(article_text)
            enriched.set((article_uri, NEWS.hasSentiment, sentiment_uri))

            section = infer_section(article_text, topic_names, technology_names)
            enriched.set((article_uri, NEWS.hasSection, Literal(section)))

            article_types = infer_article_subtypes(article_text, section)
            for article_type in article_types:
                enriched.add((article_uri, RDF.type, article_type))

        published_date = _get_first_literal(enriched, article_uri, NEWS.publishedDate)
        if published_date is not None and (article_uri, NEWS.hasUpdateTimestamp, None) not in enriched:
            enriched.set((article_uri, NEWS.hasUpdateTimestamp, published_date))

        inferred_topics = infer_additional_topics(
            article_text, topic_names, technology_names, organization_names
        )
        for topic_label in inferred_topics:
            topic_uri = topic_nodes[topic_label]
            if topic_uri is None:
                topic_uri = NEWS[f"topic/{_slug(topic_label)}"]
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

    kg_path = args.kg or choose_default_kg()
    graph = load_kg(kg_path)
    enriched = enrich_graph(graph)
    save_graph(enriched, args.output)

    print(f"[COMPLETE] Source KG: {kg_path}")
    print(f"[COMPLETE] Input triples: {len(graph)}")
    print(f"[COMPLETE] Output triples: {len(enriched)}")
    print(f"[COMPLETE] Saved enriched KG to {args.output}")


if __name__ == "__main__":
    main()
