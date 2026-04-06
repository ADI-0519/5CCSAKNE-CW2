"""Tests for fixed-scope data collection and unification."""

from src.data_collection import (
    _deduplicate_records,
    _guardian_result_to_record,
    _newsapi_article_to_record,
)


def test_guardian_result_is_normalised_to_unified_schema():
    result = {
        "sectionName": "Politics",
        "webPublicationDate": "2026-03-15T08:30:00Z",
        "webTitle": "Government unveils new housing policy",
        "webUrl": "https://www.theguardian.com/politics/2026/mar/15/housing-policy",
        "fields": {
            "headline": "Government unveils new housing policy",
            "trailText": "Ministers announced new housing measures.",
            "bodyText": "The UK government set out a new plan for housing reform.",
            "byline": "Jane Reporter",
            "lastModified": "2026-03-15T09:00:00Z",
            "wordcount": "420",
        },
        "tags": [
            {"webTitle": "Housing"},
            {"webTitle": "Politics"},
        ],
    }

    record = _guardian_result_to_record(result)

    assert record["source_system"] == "guardianapi"
    assert record["source_name"] == "The Guardian"
    assert record["section"] == "Politics"
    assert record["tags"] == ["Housing", "Politics"]
    assert record["word_count"] == 420
    assert record["updated_at"] == "2026-03-15T09:00:00Z"


def test_newsapi_article_is_normalised_to_unified_schema():
    article = {
        "source": {"name": "BBC News"},
        "author": "John Reporter",
        "title": "Labour sets out transport plan",
        "description": "The party outlined a transport policy package.",
        "url": "https://www.bbc.co.uk/news/uk-politics-123456",
        "publishedAt": "2026-03-20T11:00:00Z",
        "content": "The Labour Party said its transport plan would focus on public services.",
    }

    record = _newsapi_article_to_record(article)

    assert record["source_system"] == "newsapi"
    assert record["source_name"] == "BBC News"
    assert record["section"] == "Politics"
    assert record["published_at"] == "2026-03-20T11:00:00Z"
    assert record["word_count"] is not None


def test_deduplicate_records_keeps_first_url_occurrence():
    records = [
        {"url": "https://example.com/a", "title": "A"},
        {"url": "https://example.com/a", "title": "A duplicate"},
        {"url": "https://example.com/b", "title": "B"},
    ]

    deduped = _deduplicate_records(records)

    assert len(deduped) == 2
    assert deduped[0]["title"] == "A"
    assert deduped[1]["title"] == "B"
