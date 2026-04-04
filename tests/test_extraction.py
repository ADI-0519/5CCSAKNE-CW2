"""Unit tests for data_extraction module."""

import pytest
from src.data_extraction import (
    _extract_technologies,
    _extract_topics,
    _extract_organizations,
    _extract_people,
    _extract_locations,
    _generate_relations,
    _stable_id,
    extract_relevant_information,
)


class TestExtractTechnologies:
    def test_detects_known_keyword(self):
        result = _extract_technologies("This article is about Machine Learning trends.")
        assert "Machine Learning" in result

    def test_case_insensitive(self):
        result = _extract_technologies("advances in ARTIFICIAL INTELLIGENCE")
        assert "Artificial Intelligence" in result

    def test_returns_empty_for_no_match(self):
        result = _extract_technologies("The weather is nice today.")
        assert result == []

    def test_deduplicates_via_set(self):
        text = "AI and AI and AI"
        result = _extract_technologies(text)
        assert result.count("AI") == 1

    def test_detects_multiple_keywords(self):
        text = "GPT and deep learning are both AI technologies."
        result = _extract_technologies(text)
        assert "GPT" in result
        assert "Deep Learning" in result
        assert "AI" in result


class TestExtractTopics:
    def test_detects_topic(self):
        result = _extract_topics("New government regulation on AI is expected.")
        assert "regulation" in result
        assert "government" in result

    def test_returns_empty_for_no_match(self):
        result = _extract_topics("Cats and dogs are popular pets.")
        assert result == []


class TestExtractOrganizations:
    def test_detects_org_with_suffix(self):
        result = _extract_organizations("OpenAI Corporation announced new research today.")
        assert any("OpenAI" in o for o in result)

    def test_detects_tech_suffix(self):
        result = _extract_organizations("Acme Technologies released a new product.")
        assert any("Acme" in o for o in result)

    def test_no_false_positive_without_suffix(self):
        result = _extract_organizations("John went to the store.")
        assert result == []


class TestExtractPeople:
    def test_detects_two_word_name(self):
        result = _extract_people("CEO Jane Smith presented the findings.")
        assert "Jane Smith" in result

    def test_filters_person_stoplist(self):
        result = _extract_people("The event was held in New York.")
        assert "New York" not in result

    def test_filters_entity_stoplist(self):
        result = _extract_people("More details will follow.")
        assert result == []


class TestExtractLocations:
    def test_detects_location_after_in(self):
        result = _extract_locations("The conference was held in London this week.")
        assert "London" in result

    def test_detects_location_after_from(self):
        result = _extract_locations("Reporting from Paris.")
        assert "Paris" in result

    def test_no_match_without_preposition(self):
        result = _extract_locations("Apple released a new product.")
        assert result == []


class TestStableId:
    def test_stable_from_url(self):
        id1 = _stable_id("https://example.com/article", "Title", "2024-01-01")
        id2 = _stable_id("https://example.com/article", "Title", "2024-01-01")
        assert id1 == id2

    def test_different_urls_different_ids(self):
        id1 = _stable_id("https://example.com/a", "", "")
        id2 = _stable_id("https://example.com/b", "", "")
        assert id1 != id2

    def test_id_is_16_chars(self):
        result = _stable_id("https://example.com/x", "", "")
        assert len(result) == 16


class TestExtractRelevantInformation:
    def test_raises_on_none_input(self):
        with pytest.raises((ValueError, AttributeError)):
            extract_relevant_information(None)

    def test_raises_on_empty_articles(self):
        with pytest.raises(ValueError, match="No articles"):
            extract_relevant_information({"articles": []})

    def test_returns_list_of_records(self):
        raw = {
            "articles": [{
                "source": {"name": "TestSource"},
                "author": "John Doe",
                "title": "AI in Machine Learning Research",
                "description": "Deep learning advances.",
                "url": "https://example.com/article1",
                "publishedAt": "2024-01-15T10:00:00Z",
                "content": "More AI content here.",
            }]
        }
        result = extract_relevant_information(raw)
        assert len(result) == 1
        record = result[0]
        assert "id" in record
        assert "title" in record
        assert "url" in record
        assert "published_at" in record
        assert "source_name" in record
        assert "entities" in record
        assert "relations" in record

    def test_entities_have_required_keys(self):
        raw = {
            "articles": [{
                "source": {"name": "TestSource"},
                "title": "Some Title",
                "description": "Some description",
                "url": "https://example.com/x",
                "publishedAt": "2024-01-15T10:00:00Z",
                "content": "",
            }]
        }
        result = extract_relevant_information(raw)
        entities = result[0]["entities"]
        for key in ("organizations", "people", "locations", "technologies", "topics"):
            assert key in entities
            assert isinstance(entities[key], list)

    def test_handles_missing_optional_fields(self):
        raw = {
            "articles": [{
                "source": {"name": "TestSource"},
                "title": "Minimal Article",
                "description": None,
                "url": "https://example.com/minimal",
                "publishedAt": "2024-01-15T10:00:00Z",
                "content": None,
                "author": None,
            }]
        }
        result = extract_relevant_information(raw)
        assert len(result) == 1