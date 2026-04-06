"""Tests for KG completion/enrichment."""

import json
from pathlib import Path

from rdflib import RDF, Graph, Literal
from rdflib.namespace import XSD

from src.build_ontology import NEWS, SCHEMA, build_ontology
from src.complete_kg import enrich_graph
from src.data_extraction import extract_relevant_information
from src.data_normalisation import normalise_data
from src.json_to_rdf import convert_json_to_rdf

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "sample_response.json"


def _build_fixture_graph():
    raw_data = json.loads(FIXTURE_PATH.read_text())
    rdf_graph = convert_json_to_rdf(normalise_data(extract_relevant_information(raw_data)))
    graph = build_ontology()
    for triple in rdf_graph:
        graph.add(triple)
    return graph


def _add_named_entity(graph, entity_uri, label, rdf_types):
    for rdf_type in rdf_types:
        graph.add((entity_uri, RDF.type, rdf_type))
    graph.add((entity_uri, SCHEMA.name, Literal(label)))


def test_enrich_graph_adds_article_completion_metadata():
    enriched = enrich_graph(_build_fixture_graph())
    article_nodes = list(enriched.subjects(RDF.type, NEWS.NewsArticle))

    assert article_nodes
    for article_uri in article_nodes:
        assert (article_uri, NEWS.wordCount, None) in enriched
        assert (article_uri, NEWS.hasSentiment, None) in enriched
        assert (article_uri, NEWS.hasSection, None) in enriched
        assert (article_uri, NEWS.hasUpdateTimestamp, None) in enriched


def test_enrich_graph_infers_additional_topics():
    enriched = enrich_graph(_build_fixture_graph())
    innovation_uri = NEWS["topic/innovation"]
    assert (innovation_uri, RDF.type, NEWS.Topic) in enriched
    assert any(enriched.triples((None, NEWS.hasTopic, innovation_uri)))


def test_enrich_graph_classifies_articles_and_adds_follow_up():
    graph = build_ontology()
    publisher_uri = NEWS["org/Daily_News"]
    org_uri = NEWS["org/City_Council"]

    _add_named_entity(graph, publisher_uri, "Daily News", (NEWS.NewsOrganisation, NEWS.Organisation, SCHEMA.Organization))
    _add_named_entity(graph, org_uri, "City Council", (NEWS.Organisation, SCHEMA.Organization))

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
