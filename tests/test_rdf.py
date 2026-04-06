"""Unit tests for json_to_rdf module."""

import pytest
from rdflib import RDF, Literal
from rdflib.namespace import XSD

from src.build_ontology import CORE
from src.json_to_rdf import EX, SCHEMA, convert_json_to_rdf


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
            {"subject": "abc123def456789a", "predicate": "mentions", "object": "research"},
            {"subject": "abc123def456789a", "predicate": "published_by", "object": "TechCrunch"},
            {"subject": "abc123def456789a", "predicate": "authored_by", "object": "Jane Smith"},
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
        assert (article_uri, RDF.type, EX.NewsArticle) in g
        assert (article_uri, RDF.type, SCHEMA.NewsArticle) in g

    def test_article_has_headline(self):
        g = convert_json_to_rdf([_sample_record()])
        article_uri = EX["article/abc123def456789a"]
        headline_values = list(g.objects(article_uri, SCHEMA.headline))
        assert Literal("OpenAI Announces GPT Breakthrough") in headline_values

    def test_article_has_date_published(self):
        g = convert_json_to_rdf([_sample_record()])
        article_uri = EX["article/abc123def456789a"]
        dates = list(g.objects(article_uri, EX.publishedDate))
        assert len(dates) == 1
        assert str(dates[0]).startswith("2024-01-15T10:00:00")

    def test_article_has_url(self):
        g = convert_json_to_rdf([_sample_record()])
        article_uri = EX["article/abc123def456789a"]
        urls = list(g.objects(article_uri, EX.articleURL))
        assert Literal("https://techcrunch.com/2024/01/15/openai-gpt", datatype=XSD.anyURI) in urls

    def test_article_has_author(self):
        g = convert_json_to_rdf([_sample_record()])
        article_uri = EX["article/abc123def456789a"]
        author_uri = EX["person/Jane_Smith"]
        authors = list(g.objects(article_uri, EX.hasAuthor))
        assert author_uri in authors
        assert (author_uri, RDF.type, EX.Journalist) in g

    def test_org_entity_created(self):
        g = convert_json_to_rdf([_sample_record()])
        org_uri = EX["org/OpenAI_Corporation"]
        assert (org_uri, RDF.type, EX.Organisation) in g
        assert (org_uri, RDF.type, SCHEMA.Organization) in g

    def test_publisher_entity_created(self):
        g = convert_json_to_rdf([_sample_record()])
        org_uri = EX["org/TechCrunch"]
        assert (org_uri, RDF.type, EX.NewsOrganisation) in g
        assert (org_uri, RDF.type, EX.Organisation) in g

    def test_tech_entity_created(self):
        g = convert_json_to_rdf([_sample_record()])
        tech_uri = EX["tech/GPT"]
        assert (tech_uri, RDF.type, EX.Technology) in g

    def test_person_entity_created(self):
        g = convert_json_to_rdf([_sample_record()])
        person_uri = EX["person/Jane_Smith"]
        assert (person_uri, RDF.type, SCHEMA.Person) in g

    def test_location_entity_created(self):
        g = convert_json_to_rdf([_sample_record()])
        loc_uri = EX["location/San_Francisco"]
        assert (loc_uri, RDF.type, EX.Location) in g
        assert (loc_uri, RDF.type, CORE.Place) in g

    def test_mentions_relation_present(self):
        g = convert_json_to_rdf([_sample_record()])
        article_uri = EX["article/abc123def456789a"]
        tech_uri = EX["tech/GPT"]
        assert (article_uri, EX.mentionsTechnology, tech_uri) in g

    def test_topic_relation_present(self):
        g = convert_json_to_rdf([_sample_record()])
        article_uri = EX["article/abc123def456789a"]
        topic_uri = EX["topic/research"]
        assert (article_uri, EX.hasTopic, topic_uri) in g

    def test_published_by_relation_present(self):
        g = convert_json_to_rdf([_sample_record()])
        article_uri = EX["article/abc123def456789a"]
        publisher_uri = EX["org/TechCrunch"]
        assert (article_uri, EX.publishedBy, publisher_uri) in g

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
