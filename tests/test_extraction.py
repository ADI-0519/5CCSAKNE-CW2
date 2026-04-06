"""Behavioral tests for the current extraction pipeline."""

import pytest

from src.data_extraction import (
    build_article_id,
    classify_article_type,
    classify_sentiment,
    extract_relevant_information,
)


def make_article(**overrides):
    article = {
        "id": "article-1",
        "source_system": "guardian",
        "source_name": "The Guardian",
        "title": "Keir Starmer faces pressure over budget plans",
        "url": "https://example.com/article-1",
        "published_at": "2026-03-20T10:00:00Z",
        "updated_at": None,
        "author": "Pippa Crerar",
        "section": "Politics",
        "summary": "Treasury plans spark debate in Westminster.",
        "content": (
            "Keir Starmer and Rachel Reeves faced criticism in London after the Treasury "
            "announced budget and public spending changes in Parliament."
        ),
        "tags": ["Politics", "Budget"],
        "word_count": 120,
        "raw_article_type_hint": None,
    }
    article.update(overrides)
    return article


class TestBuildArticleId:
    def test_stable_for_same_input(self):
        result_one = build_article_id("https://example.com/article", "Title", "2026-03-06")
        result_two = build_article_id("https://example.com/article", "Title", "2026-03-06")
        assert result_one == result_two
        assert len(result_one) == 16


class TestClassificationHelpers:
    def test_opinion_article_detected_from_section(self):
        article = make_article(section="Comment is Free", raw_article_type_hint=None)
        result = classify_article_type(article, f"{article['title']} {article['summary']}")
        assert result == "OpinionArticle"

    def test_breaking_article_detected_from_live_title(self):
        article = make_article(title="Live: Labour faces budget backlash")
        result = classify_article_type(article, f"{article['title']} {article['summary']}")
        assert result == "BreakingNewsArticle"

    def test_sentiment_classification_detects_negative_language(self):
        text = "The policy drew criticism, concern and backlash across Parliament."
        assert classify_sentiment(text) == "Negative"

    def test_sentiment_classification_detects_positive_language(self):
        text = "The plan was welcomed as progress and a boost for growth."
        assert classify_sentiment(text) == "Positive"


class TestExtractRelevantInformation:
    def test_raises_on_none_input(self):
        with pytest.raises(ValueError, match="No data provided"):
            extract_relevant_information(None)

    def test_raises_on_empty_list_input(self):
        with pytest.raises(ValueError, match="No articles found"):
            extract_relevant_information([])

    def test_extracts_from_normalised_article_list(self):
        records = extract_relevant_information([make_article()])
        assert len(records) == 1

        record = records[0]
        assert record["article_type"] == "NewsArticle"
        assert record["sentiment"] in {"Positive", "Negative", "Neutral"}
        assert "entities" in record
        assert "event_candidates" in record
        assert "relations" in record

    def test_removes_people_organisation_overlap(self):
        article = make_article(
            title="Home Office confirms new immigration rules",
            content=(
                "The Home Office announced changes in London. Griff Ferris said the Home Office "
                "proposal would face challenge."
            ),
            tags=["Immigration and asylum", "Home Office"],
        )

        record = extract_relevant_information([article])[0]
        people = set(record["entities"]["people"])
        organisations = set(record["entities"]["organizations"])

        assert "Griff Ferris" in people
        assert "Home Office" in organisations
        assert "Home Office" not in people
        assert not (people & organisations)

    def test_extracts_topics_events_and_actor_types(self):
        article = make_article(
            title="Treasury announces spring budget as Labour responds",
            content=(
                "The Treasury announced the spring budget in London as Labour criticised the "
                "proposal in Parliament."
            ),
            tags=["Politics", "Labour", "Budget"],
        )

        record = extract_relevant_information([article])[0]
        entities = record["entities"]

        assert "Budget" in entities["events"] or "Spring Statement" in entities["events"]
        assert "Labour" in entities["political_parties"]
        assert "Treasury" in entities["government_bodies"]
        assert "Politics" in entities["topics"] or "Economic Policy" in entities["topics"]

    def test_respects_raw_article_type_hint(self):
        article = make_article(raw_article_type_hint="OpinionArticle", section="UK news")
        record = extract_relevant_information([article])[0]
        assert record["article_type"] == "OpinionArticle"

    def test_merges_openai_extraction_when_available(self, monkeypatch):
        monkeypatch.setattr(
            "src.data_extraction.maybe_extract_article_with_openai",
            lambda article, text, heuristic_result: {
                "people": ["Wes Streeting"],
                "organizations": ["NHS England"],
                "locations": ["Manchester"],
                "topics": ["Healthcare"],
                "politicians": ["Wes Streeting"],
                "political_parties": [],
                "government_bodies": ["NHS England"],
                "sentiment": "Positive",
                "article_type": "OpinionArticle",
                "events": [
                    {
                        "name": "NHS Reform Announcement",
                        "type": "PoliticalEvent",
                        "date": "2026-03-20",
                        "location": "Manchester",
                    }
                ],
            },
        )

        record = extract_relevant_information([make_article()])[0]

        assert record["sentiment"] == "Positive"
        assert record["article_type"] == "OpinionArticle"
        assert "Wes Streeting" in record["entities"]["people"]
        assert "NHS England" in record["entities"]["government_bodies"]
        assert "Healthcare" in record["entities"]["topics"]
        assert "NHS Reform Announcement" in record["entities"]["events"]
