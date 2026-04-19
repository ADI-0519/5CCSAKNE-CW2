"""Unit tests for the current normalisation layer."""

import pytest

from src.data_normalisation import (
    build_stable_id,
    canonicalise_date,
    is_valid_url,
    normalise_collected_sources,
    normalise_data,
    normalise_govuk_records,
    normalise_name,
    normalise_parliament_records,
)


class TestUtilityFunctions:
    def test_build_stable_id_prefers_url(self):
        first = build_stable_id("https://example.com/a", "Title", "2026-03-06")
        second = build_stable_id("https://example.com/a", "Different", "2026-04-01")
        assert first == second
        assert len(first) == 16

    def test_canonicalise_date_accepts_supported_formats(self):
        assert canonicalise_date("2026-03-06T10:00:00Z") == "2026-03-06T10:00:00Z"
        assert canonicalise_date("2026-03-06").startswith("2026-03-06")

    def test_canonicalise_date_rejects_invalid_input(self):
        with pytest.raises(ValueError, match="Cannot parse date"):
            canonicalise_date("not-a-date")

    def test_is_valid_url_accepts_http_and_https(self):
        assert is_valid_url("https://example.com") is True
        assert is_valid_url("http://example.com") is True
        assert is_valid_url("ftp://example.com") is False

    def test_normalise_name_trims_and_collapses_whitespace(self):
        assert normalise_name("  hello   world  ") == "hello world"
        assert normalise_name(None) == ""


class TestSourceNormalisation:
    def test_normalise_collected_sources_preserves_core_sources(self):
        collected = {
            "sources": {
                "guardian": {
                    "response": {
                        "results": [
                            {
                                "webTitle": "Opinion: Immigration policy needs reform",
                                "webUrl": "https://example.com/guardian-1",
                                "webPublicationDate": "2026-03-06T09:00:00Z",
                                "sectionName": "Comment is Free",
                                "tags": [{"webTitle": "Immigration and asylum"}],
                                "fields": {
                                    "byline": "Polly Toynbee",
                                    "trailText": "An opinion column on immigration.",
                                    "bodyText": "The Home Office is under pressure over immigration policy.",
                                    "lastModified": "2026-03-06T10:00:00Z",
                                    "wordcount": "500",
                                },
                            }
                        ]
                    }
                },
                "parliament": {
                    "response": {
                        "results": [
                            {
                                "title": "Budget debate",
                                "url": "https://api.parliament.uk/event/1",
                                "date": "2026-03-06T11:00:00Z",
                                "house": "House of Commons",
                                "description": "Members debated the Spring Budget.",
                                "topics": ["Budget", "Taxation"],
                            }
                        ]
                    }
                },
                "govuk": {
                    "response": {
                        "results": [
                            {
                                "title": "New immigration policy paper",
                                "link": "/government/publications/new-immigration-policy-paper",
                                "public_timestamp": "2026-03-06T12:00:00Z",
                                "description": "A new policy paper from the Home Office.",
                                "format": "policy_paper",
                                "organisations": ["Home Office"],
                            }
                        ]
                    }
                },
            }
        }

        result = normalise_collected_sources(collected)
        assert len(result) == 3
        assert {record["source_system"] for record in result} == {
            "guardian",
            "parliament",
            "govuk",
        }

    def test_guardian_contributor_tags_are_not_kept_as_topics(self):
        collected = {
            "sources": {
                "guardian": {
                    "response": {
                        "results": [
                            {
                                "webTitle": "Politics article",
                                "webUrl": "https://example.com/guardian-2",
                                "webPublicationDate": "2026-03-06T09:00:00Z",
                                "sectionName": "Politics",
                                "tags": [
                                    {"type": "contributor", "webTitle": "John Harris"},
                                    {"type": "keyword", "webTitle": "Labour"},
                                ],
                                "fields": {
                                    "byline": "John Harris",
                                    "trailText": "Politics update.",
                                    "bodyText": "Labour responds in Parliament.",
                                    "lastModified": "2026-03-06T10:00:00Z",
                                    "wordcount": "400",
                                },
                            }
                        ]
                    }
                }
            }
        }

        result = normalise_collected_sources(collected)
        assert result[0]["tags"] == ["Labour"]

    def test_normalise_parliament_records_maps_source_fields_to_shared_schema(self):
        raw_data = {
            "response": {
                "results": [
                    {
                        "title": "Health statement",
                        "url": "https://api.parliament.uk/event/health-statement",
                        "date": "2026-03-07T10:30:00Z",
                        "house": "House of Commons",
                        "description": "A statement on NHS performance.",
                        "topics": ["NHS", "Healthcare"],
                    }
                ]
            }
        }

        record = normalise_parliament_records(raw_data)[0]

        assert record["source_system"] == "parliament"
        assert record["source_name"] == "UK Parliament"
        assert record["section"] == "House of Commons"
        assert "Healthcare" in record["tags"]
        assert record["published_at"] == "2026-03-07T10:30:00Z"

    def test_normalise_govuk_records_maps_search_results_to_shared_schema(self):
        raw_data = {
            "response": {
                "results": [
                    {
                        "title": "Treasury growth plan",
                        "link": "/government/publications/treasury-growth-plan",
                        "public_timestamp": "2026-03-08T09:15:00Z",
                        "description": "A policy paper about growth and investment.",
                        "format": "policy_paper",
                        "organisations": ["HM Treasury"],
                    }
                ]
            }
        }

        record = normalise_govuk_records(raw_data)[0]

        assert record["source_system"] == "govuk"
        assert record["source_name"] == "GOV.UK"
        assert record["section"] == "policy_paper"
        assert record["url"] == "https://www.gov.uk/government/publications/treasury-growth-plan"
        assert "HM Treasury" in record["tags"]


class TestExtractedRecordNormalisation:
    def valid_record(self, **overrides):
        record = {
            "id": "abc123",
            "source_system": "guardian",
            "source_name": "The Guardian",
            "title": "Keir Starmer faces pressure over budget plans",
            "url": "https://example.com/test",
            "published_at": "2026-03-06T10:00:00Z",
            "updated_at": None,
            "author": "Jane Doe",
            "section": "Politics",
            "summary": "A budget update.",
            "content": "The Treasury and Labour clashed in Parliament.",
            "tags": ["Politics", "Budget"],
            "word_count": 120,
            "article_type": "NewsArticle",
            "sentiment": "Negative",
            "event_candidates": [
                {
                    "name": "Budget",
                    "type": "EconomicEvent",
                    "date": "2026-03-06",
                    "location": "London",
                    "source": "heuristic",
                }
            ],
            "follow_up_candidates": [],
            "entities": {
                "organizations": ["Treasury", "Labour"],
                "people": ["Jane Doe"],
                "politicians": [],
                "political_parties": ["Labour"],
                "government_bodies": ["Treasury"],
                "locations": ["London"],
                "technologies": [],
                "topics": ["Politics", "Economic Policy"],
                "events": ["Budget"],
            },
            "relations": [
                {"subject": "abc123", "predicate": "published_by", "object": "The Guardian"},
                {"subject": "abc123", "predicate": "authored_by", "object": "Jane Doe"},
            ],
        }
        record.update(overrides)
        return record

    def test_normalise_data_preserves_richer_fields(self):
        result = normalise_data([self.valid_record()])
        record = result[0]
        assert record["source_system"] == "guardian"
        assert record["section"] == "Politics"
        assert record["article_type"] == "NewsArticle"
        assert record["sentiment"] == "Negative"
        assert record["entities"]["government_bodies"] == ["Treasury"]
        assert record["event_candidates"][0]["name"] == "Budget"

    def test_normalise_data_rejects_unknown_predicate(self):
        record = self.valid_record(
            relations=[{"subject": "abc123", "predicate": "invented_by", "object": "Budget"}]
        )
        with pytest.raises(ValueError, match="unknown predicate"):
            normalise_data([record])

    def test_normalise_data_deduplicates_entity_lists(self):
        record = self.valid_record(
            entities={
                "organizations": ["Treasury", "Treasury"],
                "people": ["Jane Doe", "Jane Doe"],
                "politicians": [],
                "political_parties": ["Labour", "Labour"],
                "government_bodies": ["Treasury", "Treasury"],
                "locations": ["London", "London"],
                "technologies": [],
                "topics": ["Politics", "Politics"],
                "events": ["Budget", "Budget"],
            }
        )
        result = normalise_data([record])[0]
        assert result["entities"]["organizations"] == ["Treasury"]
        assert result["entities"]["people"] == ["Jane Doe"]
        assert result["entities"]["topics"] == ["Politics"]
