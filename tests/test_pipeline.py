"""Smoke and contract tests for the current KG pipeline."""

from collections import Counter

import pytest

from src.data_extraction import extract_relevant_information
from src.data_normalisation import normalise_collected_sources, normalise_data
from src.json_to_rdf import NEWS, convert_json_to_rdf


@pytest.fixture
def sample_collected_data():
    return {
        "sources": {
            "newsapi": {
                "articles": [
                    {
                        "source": {"name": "BBC News"},
                        "author": "Laura Kuenssberg",
                        "title": "Keir Starmer under pressure as Treasury defends spring budget plans",
                        "description": "Labour faces questions over tax and public spending in Westminster.",
                        "url": "https://example.com/article-1",
                        "publishedAt": "2026-03-20T10:00:00Z",
                        "content": (
                            "Keir Starmer and Rachel Reeves faced criticism in London after the Treasury "
                            "outlined budget and public spending changes in Parliament."
                        ),
                    }
                ]
            },
            "guardian": {
                "response": {
                    "results": [
                        {
                            "webTitle": "Opinion: Parliament needs a clearer immigration policy",
                            "webUrl": "https://example.com/article-2",
                            "webPublicationDate": "2026-03-25T08:30:00Z",
                            "sectionName": "Comment is Free",
                            "tags": [{"type": "keyword", "webTitle": "Immigration and asylum"}],
                            "fields": {
                                "byline": "Polly Toynbee",
                                "trailText": "An opinion piece on Westminster and immigration.",
                                "bodyText": (
                                    "The Home Office and Labour Party are under scrutiny over immigration policy in London."
                                ),
                                "lastModified": "2026-03-25T09:00:00Z",
                                "wordcount": "650",
                            },
                        }
                    ]
                }
            },
        }
    }


@pytest.fixture
def source_records(sample_collected_data):
    return normalise_collected_sources(sample_collected_data)


@pytest.fixture
def extracted_records(source_records):
    return extract_relevant_information(source_records)


@pytest.fixture
def kg_records(extracted_records):
    return normalise_data(extracted_records)


@pytest.fixture
def rdf_graph(kg_records):
    return convert_json_to_rdf(kg_records)


class TestPipelineStages:
    def test_source_normalisation_keeps_both_sources(self, source_records):
        assert len(source_records) == 2
        assert Counter(record["source_system"] for record in source_records) == {
            "newsapi": 1,
            "guardian": 1,
        }

    def test_extraction_outputs_kg_ready_fields(self, extracted_records):
        record = extracted_records[0]
        for key in (
            "article_type",
            "sentiment",
            "entities",
            "event_candidates",
            "follow_up_candidates",
            "relations",
        ):
            assert key in record

    def test_normalised_records_preserve_entity_groups(self, kg_records):
        entities = kg_records[0]["entities"]
        for key in (
            "organizations",
            "people",
            "politicians",
            "political_parties",
            "government_bodies",
            "locations",
            "topics",
            "events",
        ):
            assert key in entities

    def test_pipeline_produces_nonempty_graph(self, rdf_graph):
        assert len(rdf_graph) > 0

    def test_graph_contains_article_nodes_for_all_records(self, kg_records, rdf_graph):
        article_count = sum(1 for _ in rdf_graph.triples((None, None, None)))
        assert article_count > 0
        for record in kg_records:
            article_uri = NEWS[f"article/{record['id']}"]
            assert (article_uri, None, None) in rdf_graph

    def test_graph_contains_event_and_sentiment_information(self, rdf_graph):
        assert any(True for _ in rdf_graph.triples((None, NEWS.hasSentiment, None)))
        assert any(True for _ in rdf_graph.triples((None, NEWS.coversEvent, None)))

    def test_guardian_opinion_article_survives_end_to_end(self, kg_records):
        opinion_records = [
            record for record in kg_records if record["article_type"] == "OpinionArticle"
        ]
        assert opinion_records
        assert opinion_records[0]["section"] == "Comment is Free"
