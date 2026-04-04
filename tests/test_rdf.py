"""Unit tests for json_to_rdf module."""

import pytest
from rdflib import RDF, Literal
from rdflib.namespace import Namespace

from src.json_to_rdf import EX, convert_json_to_rdf

SCHEMA_NS = Namespace("http://schema.org/")


def _sample_record():
    return {
        "id": "abc123def456789a",
        "title": "OpenAI Announces GPT Breakthrough",
        "url": "https://techcrunch.com/2024/01/15/openai-gpt",
        "published_at": "2024-01-15T10:00:00Z",
        "source_name": "TechCrunch",
        "author": "Jane Smith",
        "summary": "A major GPT announcement.",
        "entities": {
            "organizations": ["OpenAI Corporation"],
            "people": ["Jane Smith", "Sam Altman"],
            "locations": ["San Francisco"],
            "technologies": ["GPT", "AI"],
            "topics": ["research"],
        },
        "relations": [
            {"subject": "abc123def456789a", "predicate": "mentions", "object": "GPT"},
            {
                "subject": "abc123def456789a",
                "predicate": "mentions",
                "object": "OpenAI Corporation",
            },
            {"subject": "OpenAI Corporation", "predicate": "uses_technology", "object": "GPT"},
        ],
    }


class TestConvertJsonToRdf:
    def test_raises_on_empty_input(self):
        with pytest.raises(ValueError, match="No normalised data"):
            convert_json_to_rdf([])

    def test_raises_on_none_input(self):
        with pytest.raises((ValueError, TypeError)):
            convert_json_to_rdf(None)

    def test_returns_non_empty_graph(self):
        g = convert_json_to_rdf([_sample_record()])
        assert len(g) > 0

    def test_article_has_correct_type(self):
        g = convert_json_to_rdf([_sample_record()])
        article_uri = EX["article/abc123def456789a"]
        assert (article_uri, RDF.type, SCHEMA_NS.NewsArticle) in g

    def test_article_has_headline(self):
        g = convert_json_to_rdf([_sample_record()])
        article_uri = EX["article/abc123def456789a"]
        headline_values = list(g.objects(article_uri, SCHEMA_NS.headline))
        assert Literal("OpenAI Announces GPT Breakthrough") in headline_values

    def test_article_has_date_published(self):
        g = convert_json_to_rdf([_sample_record()])
        article_uri = EX["article/abc123def456789a"]
        dates = list(g.objects(article_uri, SCHEMA_NS.datePublished))
        assert len(dates) == 1
        # rdflib may render the timezone as Z or +00:00 — both are correct UTC
        assert str(dates[0]).startswith("2024-01-15T10:00:00")

    def test_article_has_url(self):
        g = convert_json_to_rdf([_sample_record()])
        article_uri = EX["article/abc123def456789a"]
        urls = list(g.objects(article_uri, SCHEMA_NS.url))
        assert Literal("https://techcrunch.com/2024/01/15/openai-gpt") in urls

    def test_article_has_author(self):
        g = convert_json_to_rdf([_sample_record()])
        article_uri = EX["article/abc123def456789a"]
        authors = list(g.objects(article_uri, SCHEMA_NS.author))
        assert Literal("Jane Smith") in authors

    def test_org_entity_created(self):
        g = convert_json_to_rdf([_sample_record()])
        org_uri = EX["org/OpenAI_Corporation"]
        assert (org_uri, RDF.type, SCHEMA_NS.Organization) in g

    def test_tech_entity_created(self):
        g = convert_json_to_rdf([_sample_record()])
        tech_uri = EX["tech/GPT"]
        assert (tech_uri, RDF.type, EX.Technology) in g

    def test_person_entity_created(self):
        g = convert_json_to_rdf([_sample_record()])
        person_uri = EX["person/Jane_Smith"]
        assert (person_uri, RDF.type, SCHEMA_NS.Person) in g

    def test_location_entity_created(self):
        g = convert_json_to_rdf([_sample_record()])
        loc_uri = EX["location/San_Francisco"]
        assert (loc_uri, RDF.type, SCHEMA_NS.Place) in g

    def test_mentions_relation_present(self):
        g = convert_json_to_rdf([_sample_record()])
        article_uri = EX["article/abc123def456789a"]
        tech_uri = EX["tech/GPT"]
        assert (article_uri, EX.mentions, tech_uri) in g

    def test_uses_technology_relation_present(self):
        g = convert_json_to_rdf([_sample_record()])
        org_uri = EX["org/OpenAI_Corporation"]
        tech_uri = EX["tech/GPT"]
        assert (org_uri, EX.usesTechnology, tech_uri) in g

    def test_raises_on_unknown_predicate(self):
        record = _sample_record()
        record["relations"] = [
            {"subject": record["id"], "predicate": "invented_by", "object": "GPT"}
        ]
        with pytest.raises(ValueError, match="Unknown predicate"):
            convert_json_to_rdf([record])

    def test_multiple_records_produce_more_triples(self):
        r1 = _sample_record()
        r2 = _sample_record()
        r2["id"] = "bbbbbbbbbbbbbbbb"
        r2["url"] = "https://example.com/other"
        r2["relations"] = [
            {"subject": "bbbbbbbbbbbbbbbb", "predicate": "mentions", "object": "GPT"}
        ]
        g_single = convert_json_to_rdf([r1])
        g_double = convert_json_to_rdf([r1, r2])
        assert len(g_double) > len(g_single)

    def test_graph_serializes_to_turtle(self, tmp_path):
        g = convert_json_to_rdf([_sample_record()])
        out = tmp_path / "test.ttl"
        g.serialize(destination=str(out), format="turtle")
        content = out.read_text()
        assert "@prefix" in content
        assert "NewsArticle" in content
