"""Tests for RDF generation from KG-ready records."""

import pytest
from rdflib import RDF
from rdflib.namespace import XSD

from src.json_to_rdf import NEWS, SCHEMA, convert_json_to_rdf


def sample_record(**overrides):
    record = {
        "id": "abc123def456789a",
        "source_system": "guardian",
        "source_name": "The Guardian",
        "title": "Labour responds to spring budget announcement",
        "url": "https://example.com/article",
        "published_at": "2026-03-06T10:00:00Z",
        "updated_at": "2026-03-06T11:00:00Z",
        "author": "Jane Smith",
        "section": "Politics",
        "summary": "A politics update from Westminster.",
        "content": "Labour criticised the Treasury after the spring budget announcement in London.",
        "tags": ["Politics", "Budget"],
        "word_count": 250,
        "article_type": "OpinionArticle",
        "sentiment": "Negative",
        "follow_up_candidates": [{"match_key": "The Guardian|Budget", "reason": "same source"}],
        "event_candidates": [
            {
                "name": "Budget",
                "type": "EconomicEvent",
                "date": "2026-03-06",
                "location": "London",
                "source": "heuristic",
            }
        ],
        "entities": {
            "organizations": ["Labour", "Treasury"],
            "people": ["Jane Smith", "Keir Starmer"],
            "politicians": ["Keir Starmer"],
            "political_parties": ["Labour"],
            "government_bodies": ["Treasury"],
            "locations": ["London"],
            "technologies": [],
            "topics": ["Politics", "Economic Policy"],
            "events": ["Budget"],
        },
        "relations": [],
    }
    record.update(overrides)
    return record


class TestConvertJsonToRdf:
    def test_raises_on_empty_input(self):
        with pytest.raises(ValueError, match="No normalised data"):
            convert_json_to_rdf([])

    def test_returns_non_empty_graph(self):
        graph = convert_json_to_rdf([sample_record()])
        assert len(graph) > 0

    def test_article_node_has_expected_types_and_metadata(self):
        graph = convert_json_to_rdf([sample_record()])
        article = NEWS["article/abc123def456789a"]

        assert (article, RDF.type, NEWS.NewsArticle) in graph
        assert (article, RDF.type, NEWS.OpinionArticle) in graph
        assert (article, SCHEMA.headline, None) in graph
        assert (article, NEWS.hasSection, None) in graph
        assert (article, NEWS.wordCount, None) in graph

    def test_author_and_publisher_nodes_are_created(self):
        graph = convert_json_to_rdf([sample_record()])
        article = NEWS["article/abc123def456789a"]
        author = NEWS["person/Jane_Smith"]
        publisher = NEWS["organisation/The_Guardian"]

        assert (article, NEWS.hasAuthor, author) in graph
        assert (author, RDF.type, NEWS.Journalist) in graph
        assert (article, NEWS.publishedBy, publisher) in graph
        assert (publisher, RDF.type, NEWS.NewsOrganisation) in graph

    def test_people_orgs_locations_and_topics_are_typed(self):
        graph = convert_json_to_rdf([sample_record()])

        politician = NEWS["person/Keir_Starmer"]
        party = NEWS["organisation/Labour"]
        body = NEWS["organisation/Treasury"]
        location = NEWS["location/London"]
        topic = NEWS["topic/Politics"]

        assert (politician, RDF.type, NEWS.Politician) in graph
        assert (party, RDF.type, NEWS.PoliticalParty) in graph
        assert (body, RDF.type, NEWS.GovernmentBody) in graph
        assert (location, RDF.type, NEWS.Location) in graph
        assert (topic, RDF.type, NEWS.Topic) in graph

    def test_event_and_sentiment_triples_are_created(self):
        graph = convert_json_to_rdf([sample_record()])
        article = NEWS["article/abc123def456789a"]
        event = NEWS["event/Budget_2026-03-06T00_00_00Z_London"]

        assert (article, NEWS.hasSentiment, NEWS.Negative) in graph
        assert (article, NEWS.coversEvent, event) in graph
        assert (event, RDF.type, NEWS.EconomicEvent) in graph
        assert any(obj.datatype == XSD.dateTime for obj in graph.objects(event, NEWS.eventDate))

    def test_same_event_from_multiple_articles_reuses_event_node(self):
        first = sample_record(
            id="article-a",
            source_name="The Guardian",
            event_candidates=[
                {
                    "name": "Budget",
                    "type": "EconomicEvent",
                    "date": "2026-03-06",
                    "location": "London",
                    "source": "heuristic",
                }
            ],
        )
        second = sample_record(
            id="article-b",
            source_name="BBC News",
            author="John Smith",
            event_candidates=[
                {
                    "name": "Budget",
                    "type": "EconomicEvent",
                    "date": "2026-03-06",
                    "location": "London",
                    "source": "heuristic",
                }
            ],
        )
        graph = convert_json_to_rdf([first, second])
        event = NEWS["event/Budget_2026-03-06T00_00_00Z_London"]

        assert (NEWS["article/article-a"], NEWS.coversEvent, event) in graph
        assert (NEWS["article/article-b"], NEWS.coversEvent, event) in graph

    def test_follow_up_link_is_created_between_related_articles(self):
        first = sample_record(id="article-a", published_at="2026-03-06T10:00:00Z")
        second = sample_record(id="article-b", published_at="2026-03-06T12:00:00Z")
        graph = convert_json_to_rdf([first, second])

        assert (
            NEWS["article/article-a"],
            NEWS.hasFollowUp,
            NEWS["article/article-b"],
        ) in graph
