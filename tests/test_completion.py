"""Tests for KG completion/enrichment."""

from rdflib import RDF, Literal
from rdflib.namespace import XSD

from src.build_ontology import NEWS, SCHEMA, build_ontology
from src.complete_kg import enrich_graph


def add_named_entity(graph, entity_uri, label, rdf_types):
    for rdf_type in rdf_types:
        graph.add((entity_uri, RDF.type, rdf_type))
    graph.add((entity_uri, SCHEMA.name, Literal(label)))


def test_enrich_graph_adds_article_completion_metadata():
    graph = build_ontology()
    article_uri = NEWS["article/completion_a"]
    graph.add((article_uri, RDF.type, NEWS.NewsArticle))
    graph.add((article_uri, RDF.type, SCHEMA.NewsArticle))
    graph.add((article_uri, SCHEMA.headline, Literal("Treasury faces pressure over budget plan")))
    graph.add(
        (
            article_uri,
            SCHEMA.description,
            Literal("Ministers defended public spending decisions after the spring budget."),
        )
    )
    graph.add(
        (article_uri, NEWS.publishedDate, Literal("2026-03-12T10:00:00Z", datatype=XSD.dateTime))
    )

    enriched = enrich_graph(graph)
    article_nodes = list(enriched.subjects(RDF.type, NEWS.NewsArticle))

    assert article_nodes
    for article_uri in article_nodes:
        assert (article_uri, NEWS.wordCount, None) in enriched
        assert (article_uri, NEWS.hasSentiment, None) in enriched
        assert (article_uri, NEWS.hasSection, None) in enriched
        assert (article_uri, NEWS.hasUpdateTimestamp, None) in enriched


def test_enrich_graph_infers_additional_topics():
    graph = build_ontology()
    article_uri = NEWS["article/completion_topics"]
    graph.add((article_uri, RDF.type, NEWS.NewsArticle))
    graph.add((article_uri, RDF.type, SCHEMA.NewsArticle))
    graph.add(
        (article_uri, SCHEMA.headline, Literal("Treasury outlines new public spending plans"))
    )
    graph.add(
        (
            article_uri,
            SCHEMA.description,
            Literal("The government defended funding choices in its latest spending review."),
        )
    )
    graph.add(
        (article_uri, NEWS.publishedDate, Literal("2026-03-18T10:00:00Z", datatype=XSD.dateTime))
    )

    enriched = enrich_graph(graph)
    topic_uri = NEWS["topic/Public_Spending"]
    assert (topic_uri, RDF.type, NEWS.Topic) in enriched
    assert (article_uri, NEWS.hasTopic, topic_uri) in enriched


def test_enrich_graph_classifies_articles_and_adds_follow_up():
    graph = build_ontology()
    publisher_uri = NEWS["org/Daily_News"]
    org_uri = NEWS["org/City_Council"]

    add_named_entity(
        graph,
        publisher_uri,
        "Daily News",
        (NEWS.NewsOrganisation, NEWS.Organisation, SCHEMA.Organization),
    )
    add_named_entity(graph, org_uri, "City Council", (NEWS.Organisation, SCHEMA.Organization))

    article_1 = NEWS["article/a1"]
    article_2 = NEWS["article/a2"]

    for article_uri, headline, description, published in (
        (
            article_1,
            "Breaking policy update from city hall",
            "Government officials announced a new policy today.",
            "2024-01-01T10:00:00Z",
        ),
        (
            article_2,
            "Opinion: analysis of the city policy response",
            "Commentary on how the policy may develop next week.",
            "2024-01-03T08:00:00Z",
        ),
    ):
        graph.add((article_uri, RDF.type, NEWS.NewsArticle))
        graph.add((article_uri, RDF.type, SCHEMA.NewsArticle))
        graph.add((article_uri, SCHEMA.headline, Literal(headline)))
        graph.add((article_uri, SCHEMA.description, Literal(description)))
        graph.add((article_uri, NEWS.publishedDate, Literal(published, datatype=XSD.dateTime)))
        graph.add((article_uri, NEWS.publishedBy, publisher_uri))
        graph.add((article_uri, NEWS.mentionsOrganisation, org_uri))

    enriched = enrich_graph(graph)

    assert (article_1, RDF.type, NEWS.BreakingNewsArticle) in enriched
    assert (article_2, RDF.type, NEWS.OpinionArticle) in enriched
    assert (article_1, NEWS.hasFollowUp, article_2) in enriched


def test_enrich_graph_uses_openai_completion_when_available(monkeypatch):
    monkeypatch.setattr(
        "src.complete_kg.maybe_complete_article_with_openai",
        lambda article_key, article_payload, heuristic_result: {
            "sentiment": "Positive",
            "section": "Politics",
            "article_types": ["OpinionArticle"],
            "additional_topics": ["Healthcare"],
        },
    )

    graph = build_ontology()
    article_uri = NEWS["article/llm_completion"]
    graph.add((article_uri, RDF.type, NEWS.NewsArticle))
    graph.add((article_uri, RDF.type, SCHEMA.NewsArticle))
    graph.add((article_uri, SCHEMA.headline, Literal("Health secretary defends NHS plan")))
    graph.add(
        (
            article_uri,
            SCHEMA.description,
            Literal("Ministers said the NHS proposal would improve services."),
        )
    )
    graph.add(
        (article_uri, NEWS.publishedDate, Literal("2026-03-22T10:00:00Z", datatype=XSD.dateTime))
    )

    enriched = enrich_graph(graph)

    assert (article_uri, NEWS.hasSentiment, NEWS.Positive) in enriched
    assert (article_uri, NEWS.hasSection, Literal("Politics")) in enriched
    assert (article_uri, RDF.type, NEWS.OpinionArticle) in enriched
    assert (article_uri, NEWS.hasTopic, NEWS["topic/Healthcare"]) in enriched
