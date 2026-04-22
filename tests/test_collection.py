"""Tests for fixed-scope source normalisation and unification."""

import json

from src.config import CONFIG
from src.data_collection import (
    build_govuk_search_url,
    fetch_govuk_data,
    latest_snapshot_path,
    load_cached_sources,
)
from src.data_normalisation import (
    normalise_collected_sources,
    normalise_govuk_records,
    normalise_guardian_articles,
)


def test_guardian_result_is_normalised_to_unified_schema():
    raw_data = {
        "response": {
            "results": [
                {
                    "sectionName": "Politics",
                    "webPublicationDate": "2026-03-25T08:30:00Z",
                    "webTitle": "Government unveils new housing policy",
                    "webUrl": "https://www.theguardian.com/politics/2026/mar/15/housing-policy",
                    "fields": {
                        "headline": "Government unveils new housing policy",
                        "trailText": "Ministers announced new housing measures.",
                        "bodyText": "The UK government set out a new plan for housing reform.",
                        "byline": "Jane Reporter",
                        "lastModified": "2026-03-25T09:00:00Z",
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
    assert record["updated_at"] == "2026-03-25T09:00:00Z"


def test_govuk_record_is_normalised_to_unified_schema():
    raw_data = {
        "response": {
            "results": [
                {
                    "title": "Labour sets out transport plan",
                    "link": "/government/publications/transport-plan",
                    "public_timestamp": "2026-03-24T11:00:00Z",
                    "description": "A transport policy package.",
                    "format": "policy_paper",
                    "organisations": ["Department for Transport"],
                }
            ]
        }
    }

    record = normalise_govuk_records(raw_data)[0]

    assert record["source_system"] == "govuk"
    assert record["source_name"] == "GOV.UK"
    assert record["section"] == "policy_paper"
    assert record["published_at"] == "2026-03-24T11:00:00Z"
    assert record["word_count"] is not None


def test_combined_source_normalisation_deduplicates_same_article():
    duplicate_article = {
        "title": "Labour sets out transport plan",
        "link": "/government/publications/transport-plan",
        "public_timestamp": "2026-03-24T11:00:00Z",
        "description": "The party outlined a transport policy package.",
        "format": "policy_paper",
        "organisations": ["Department for Transport"],
    }

    collected_data = {
        "sources": {
            "govuk": {"response": {"results": [duplicate_article, duplicate_article]}},
            "guardian": {"response": {"results": []}},
            "parliament": {"response": {"results": []}},
        }
    }

    deduped = normalise_collected_sources(collected_data)

    assert len(deduped) == 1
    assert deduped[0]["title"] == "Labour sets out transport plan"


def test_latest_snapshot_path_returns_newest_json(tmp_path, monkeypatch):
    monkeypatch.setitem(CONFIG, "RAW_DATA_DIR", str(tmp_path))
    source_dir = tmp_path / "guardian"
    source_dir.mkdir(parents=True)
    older = source_dir / "20260306T090000Z.json"
    newer = source_dir / "20260306T120000Z.json"
    older.write_text("{}", encoding="utf-8")
    newer.write_text("{}", encoding="utf-8")

    assert latest_snapshot_path("guardian") == newer


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


def test_build_govuk_search_url_includes_window_and_format_filters():
    url = build_govuk_search_url(page=2)

    assert "start=100" in url
    assert "order=-public_timestamp" in url
    assert (
        f"filter_public_timestamp=from%3A{CONFIG['date_start']}%2Cto%3A{CONFIG['date_end']}" in url
    )
    for document_format in CONFIG["GOVUK_DOCUMENT_FORMATS"]:
        assert f"filter_format={document_format}" in url


def test_fetch_govuk_data_paginates_until_window_results_found(monkeypatch):
    page_one = {
        "results": [
            {
                "title": "Too new result",
                "link": "/government/publications/too-new-result",
                "public_timestamp": "2026-04-25T11:00:00Z",
                "description": "Outside the coursework window.",
                "format": "policy_paper",
                "organisations": ["Cabinet Office"],
            }
        ],
        "total": 200,
        "start": 0,
    }
    page_two = {
        "results": [
            {
                "title": "In-window policy paper",
                "link": "/government/publications/in-window-policy-paper",
                "public_timestamp": "2026-03-24T11:00:00Z",
                "description": "Inside the coursework window.",
                "format": "policy_paper",
                "organisations": ["Cabinet Office"],
            },
            {
                "title": "Older result",
                "link": "/government/publications/older-result",
                "public_timestamp": "2026-03-15T11:00:00Z",
                "description": "Older than the coursework window.",
                "format": "policy_paper",
                "organisations": ["Cabinet Office"],
            },
        ],
        "total": 200,
        "start": 100,
    }
    responses = [page_one, page_two]

    def fake_fetch_json(url):
        return responses.pop(0)

    monkeypatch.setattr("src.data_collection.fetch_json", fake_fetch_json)

    payload = fetch_govuk_data(save_snapshot=False)

    assert payload["pagesFetched"] == 2
    assert len(payload["response"]["results"]) == 1
    assert payload["response"]["results"][0]["title"] == "In-window policy paper"


def test_fetch_govuk_data_filters_out_of_scope_reference_material(monkeypatch):
    page_one = {
        "results": [
            {
                "title": "Rates and allowances: Inheritance Tax thresholds and interest rates",
                "link": "/government/publications/inheritance-tax-thresholds",
                "public_timestamp": "2026-03-24T11:00:00Z",
                "description": "Reference rates and allowances material.",
                "format": "guidance",
                "organisations": ["HM Revenue and Customs"],
            },
            {
                "title": "Treasury growth plan",
                "link": "/government/publications/treasury-growth-plan",
                "public_timestamp": "2026-03-24T11:05:00Z",
                "description": "A policy paper about growth and investment.",
                "format": "policy_paper",
                "organisations": ["HM Treasury"],
            },
        ],
        "total": 2,
        "start": 0,
    }

    monkeypatch.setattr("src.data_collection.fetch_json", lambda url: page_one)

    payload = fetch_govuk_data(save_snapshot=False)

    assert payload["pagesFetched"] == 1
    assert len(payload["response"]["results"]) == 1
    assert payload["response"]["results"][0]["title"] == "Treasury growth plan"
