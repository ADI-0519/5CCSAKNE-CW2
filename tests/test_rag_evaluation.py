import json
from pathlib import Path

from src.evaluate_rag import build_entry, build_report, uri_to_label


def make_audit_entry(
    event_uri,
    *,
    actors=None,
    departments=None,
    topics=None,
    match_score=None,
    source_record=None,
):
    return {
        "event_uri": event_uri,
        "matched_source_record_uri": source_record,
        "match_score": match_score,
        "matched_to_source_record_added": source_record is not None,
        "represented_in_official_source_added": False,
        "rag_added_actors": actors or [],
        "rag_added_departments": departments or [],
        "rag_added_topics": topics or [],
    }


def test_uri_to_label_strips_sub_prefix():
    assert uri_to_label("http://example.org/news#topic/Government_Policy") == "Government Policy"
    assert uri_to_label("http://example.org/news#organisation/Home_Office") == "Home Office"
    assert uri_to_label("http://example.org/news#event/Housing_Reform_2026-03-25") == "Housing Reform 2026-03-25"


def test_uri_to_label_no_sub_prefix():
    assert uri_to_label("http://example.org/news#Keir_Starmer") == "Keir Starmer"


def test_build_entry_computes_counts(monkeypatch):
    event_uri = "http://example.org/news#event/Housing_Reform_2026-03-25"
    monkeypatch.setattr(
        "src.evaluate_rag.load_rag_cache",
        lambda uri: {
            "proposed_actors": ["Keir Starmer", "Angela Rayner"],
            "proposed_departments": ["Ministry of Housing"],
            "proposed_topics": ["Housing", "Government Policy"],
        },
    )
    audit = make_audit_entry(
        event_uri,
        actors=["http://example.org/news#Keir_Starmer"],
        departments=["http://example.org/news#organisation/Ministry_of_Housing"],
        topics=[
            "http://example.org/news#topic/Housing",
            "http://example.org/news#topic/Government_Policy",
        ],
    )
    entry = build_entry(audit)

    assert entry["n_proposed"] == 5
    assert entry["n_accepted"] == 4
    assert entry["n_rejected"] == 1
    assert entry["accepted_actors"] == ["Keir Starmer"]
    assert entry["accepted_departments"] == ["Ministry of Housing"]
    assert set(entry["accepted_topics"]) == {"Housing", "Government Policy"}
    assert entry["manual_correct"] is None


def test_build_entry_no_cache(monkeypatch):
    event_uri = "http://example.org/news#event/Steel_Strategy_2026-03-20"
    monkeypatch.setattr("src.evaluate_rag.load_rag_cache", lambda uri: None)
    audit = make_audit_entry(
        event_uri,
        topics=["http://example.org/news#topic/Industry"],
    )
    entry = build_entry(audit)

    # accepted comes from audit even when cache is missing
    assert entry["accepted_topics"] == ["Industry"]
    assert entry["n_proposed"] == 0
    assert entry["n_accepted"] == 1
    assert entry["n_rejected"] == -1


def test_build_report_skips_entries_with_no_rag(monkeypatch, tmp_path):
    monkeypatch.setattr("src.evaluate_rag.load_rag_cache", lambda uri: None)

    audit_data = {
        "entry_count": 3,
        "entries": [
            make_audit_entry("http://example.org/news#event/A", topics=["http://example.org/news#topic/T"]),
            make_audit_entry("http://example.org/news#event/B"),  # no rag additions
            make_audit_entry("http://example.org/news#event/C", actors=["http://example.org/news#P"]),
        ],
    }
    audit_path = tmp_path / "audit.json"
    audit_path.write_text(json.dumps(audit_data), encoding="utf-8")

    report = build_report(audit_path)

    assert report["summary"]["events_with_rag_additions"] == 2
    assert report["summary"]["events_skipped_no_rag"] == 1
    assert len(report["entries"]) == 2