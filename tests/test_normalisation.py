"""Unit tests for the current normalisation layer."""

import pytest

from src.data_normalisation import (
    build_stable_id,
    canonicalise_date,
    is_relevant_newsapi_article,
    is_valid_url,
    normalise_collected_sources,
    normalise_data,
    normalise_name,
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
    def test_normalise_collected_sources_preserves_both_sources(self):
        collected = {
            "sources": {
                "newsapi": {
                    "articles": [
                        {
                            "source": {"name": "BBC News"},
                            "author": "Laura Kuenssberg",
                            "title": "Labour responds to budget row",
                            "description": "A Westminster update.",
                            "url": "https://example.com/newsapi-1",
                            "publishedAt": "2026-03-06T08:00:00Z",
                            "content": "The Treasury and Labour traded criticism in Parliament.",
                        }
                    ]
                },
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
            }
        }

        result = normalise_collected_sources(collected)
        assert len(result) == 2
        assert {record["source_system"] for record in result} == {"newsapi", "guardian"}

    def test_newsapi_scope_filter_rejects_blocked_off_scope_source(self):
        article = {
            "source": {"name": "Screen Rant"},
            "author": "Reporter",
            "title": "10 Near-Perfect Forgotten Horror TV Shows That Deserve A Second Chance",
            "description": "A television feature with no UK politics relevance.",
            "url": "https://example.com/off-scope",
            "publishedAt": "2026-03-06T08:00:00Z",
            "content": "Entertainment coverage only.",
        }

        assert is_relevant_newsapi_article(article) is False

    def test_newsapi_scope_filter_keeps_uk_politics_article(self):
        article = {
            "source": {"name": "BBC News"},
            "author": "Reporter",
            "title": "Keir Starmer faces pressure over UK budget plans",
            "description": "The prime minister and Treasury are under pressure in Westminster.",
            "url": "https://example.com/on-scope",
            "publishedAt": "2026-03-06T08:00:00Z",
            "content": "Labour MPs said the UK government must rethink the budget.",
        }

        assert is_relevant_newsapi_article(article) is True

    def test_newsapi_scope_filter_rejects_unapproved_publisher_even_if_text_matches(self):
        article = {
            "source": {"name": "Japan Today"},
            "author": "Reporter",
            "title": "Keir Starmer discusses UK budget in Westminster",
            "description": "The prime minister and Treasury remain under pressure.",
            "url": "https://example.com/matching-but-unapproved",
            "publishedAt": "2026-03-06T08:00:00Z",
            "content": "UK politics coverage from an out-of-scope publisher.",
        }

        assert is_relevant_newsapi_article(article) is False

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
