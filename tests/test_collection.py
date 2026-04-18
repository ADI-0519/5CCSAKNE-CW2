"""Tests for fixed-scope source normalisation and unification."""

import json

from src.config import CONFIG
from src.data_collection import latest_snapshot_path, load_cached_sources
from src.data_normalisation import (
    normalise_collected_sources,
    normalise_guardian_articles,
    normalise_newsapi_articles,
)


def test_guardian_result_is_normalised_to_unified_schema():
    raw_data = {
        "response": {
            "results": [
                {
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
            ]
        }
    }

    record = normalise_guardian_articles(raw_data)[0]

    assert record["source_system"] == "guardian"
    assert record["source_name"] == "The Guardian"
    assert record["section"] == "Politics"
    assert record["tags"] == ["Housing", "Politics"]
    assert record["word_count"] == 420
    assert record["updated_at"] == "2026-03-15T09:00:00Z"


def test_newsapi_article_is_normalised_to_unified_schema():
    raw_data = {
        "articles": [
            {
                "source": {"name": "BBC News"},
                "author": "John Reporter",
                "title": "Labour sets out transport plan",
                "description": "The party outlined a transport policy package.",
                "url": "https://www.bbc.co.uk/news/uk-politics-123456",
                "publishedAt": "2026-03-20T11:00:00Z",
                "content": "The Labour Party said its transport plan would focus on public services.",
            }
        ]
    }

    record = normalise_newsapi_articles(raw_data)[0]

    assert record["source_system"] == "newsapi"
    assert record["source_name"] == "BBC News"
    assert record["section"] is None
    assert record["published_at"] == "2026-03-20T11:00:00Z"
    assert record["word_count"] is not None


def test_combined_source_normalisation_deduplicates_same_article():
    duplicate_article = {
        "source": {"name": "BBC News"},
        "author": "John Reporter",
        "title": "Labour sets out transport plan",
        "description": "The party outlined a transport policy package.",
        "url": "https://www.bbc.co.uk/news/uk-politics-123456",
        "publishedAt": "2026-03-20T11:00:00Z",
        "content": "The Labour Party said its transport plan would focus on public services.",
    }

    collected_data = {
        "sources": {
            "newsapi": {"articles": [duplicate_article, duplicate_article]},
            "guardian": {"response": {"results": []}},
        }
    }

    deduped = normalise_collected_sources(collected_data)

    assert len(deduped) == 1
    assert deduped[0]["title"] == "Labour sets out transport plan"


def test_latest_snapshot_path_returns_newest_json(tmp_path, monkeypatch):
    monkeypatch.setitem(CONFIG, "RAW_DATA_DIR", str(tmp_path))
    source_dir = tmp_path / "newsapi"
    source_dir.mkdir(parents=True)
    older = source_dir / "20260306T090000Z.json"
    newer = source_dir / "20260306T120000Z.json"
    older.write_text("{}", encoding="utf-8")
    newer.write_text("{}", encoding="utf-8")

    assert latest_snapshot_path("newsapi") == newer


def test_load_cached_sources_reads_core_source_snapshots(tmp_path, monkeypatch):
    monkeypatch.setitem(CONFIG, "RAW_DATA_DIR", str(tmp_path))

    guardian_dir = tmp_path / "guardian"
    parliament_dir = tmp_path / "parliament"
    govuk_dir = tmp_path / "govuk"
    guardian_dir.mkdir(parents=True)
    parliament_dir.mkdir(parents=True)
    govuk_dir.mkdir(parents=True)

    guardian_payload = {"response": {"results": [{"webTitle": "Guardian snapshot"}]}}
    parliament_payload = {"response": {"results": [{"title": "Debate snapshot"}]}}
    govuk_payload = {"response": {"results": [{"title": "Policy snapshot"}]}}

    (guardian_dir / "20260306T110000Z.json").write_text(
        json.dumps(guardian_payload), encoding="utf-8"
    )
    (parliament_dir / "20260306T120000Z.json").write_text(
        json.dumps(parliament_payload), encoding="utf-8"
    )
    (govuk_dir / "20260306T130000Z.json").write_text(json.dumps(govuk_payload), encoding="utf-8")

    cached = load_cached_sources()

    assert cached["sources"]["guardian"] == guardian_payload
    assert cached["sources"]["parliament"] == parliament_payload
    assert cached["sources"]["govuk"] == govuk_payload
    assert cached["scope"]["project_scope"] == CONFIG["project_scope"]


def test_load_cached_sources_can_include_legacy_newsapi(tmp_path, monkeypatch):
    monkeypatch.setitem(CONFIG, "RAW_DATA_DIR", str(tmp_path))

    news_dir = tmp_path / "newsapi"
    guardian_dir = tmp_path / "guardian"
    parliament_dir = tmp_path / "parliament"
    govuk_dir = tmp_path / "govuk"
    news_dir.mkdir(parents=True)
    guardian_dir.mkdir(parents=True)
    parliament_dir.mkdir(parents=True)
    govuk_dir.mkdir(parents=True)

    news_payload = {"articles": [{"title": "News snapshot"}]}
    guardian_payload = {"response": {"results": [{"webTitle": "Guardian snapshot"}]}}
    parliament_payload = {"response": {"results": [{"title": "Debate snapshot"}]}}
    govuk_payload = {"response": {"results": [{"title": "Policy snapshot"}]}}

    (news_dir / "20260306T100000Z.json").write_text(json.dumps(news_payload), encoding="utf-8")
    (guardian_dir / "20260306T110000Z.json").write_text(
        json.dumps(guardian_payload), encoding="utf-8"
    )
    (parliament_dir / "20260306T120000Z.json").write_text(
        json.dumps(parliament_payload), encoding="utf-8"
    )
    (govuk_dir / "20260306T130000Z.json").write_text(json.dumps(govuk_payload), encoding="utf-8")

    cached = load_cached_sources(include_legacy_newsapi=True)

    assert cached["sources"]["newsapi"] == news_payload
    assert cached["sources"]["guardian"] == guardian_payload
    assert cached["sources"]["parliament"] == parliament_payload
    assert cached["sources"]["govuk"] == govuk_payload
