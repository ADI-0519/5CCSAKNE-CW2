from pathlib import Path

from src.evaluate_extraction import (
    build_gold_template,
    evaluate_samples,
    project_record,
    select_template_records,
)


def make_record(
    record_id,
    source_system,
    *,
    title="Title",
    topics=None,
    government_bodies=None,
    locations=None,
    events=None,
):
    return {
        "id": record_id,
        "source_system": source_system,
        "source_name": "Test Source",
        "title": title,
        "url": f"https://example.org/{record_id}",
        "published_at": "2026-03-20T10:00:00Z",
        "author": "Reporter",
        "article_type": "NewsArticle",
        "entities": {
            "topics": topics or [],
            "government_bodies": government_bodies or [],
            "locations": locations or [],
            "politicians": [],
            "political_parties": [],
        },
        "event_candidates": events or [],
    }


def make_event(
    name,
    *,
    event_type="GovernmentPolicyEvent",
    topics=None,
    government_bodies=None,
    actors=None,
    parties=None,
    parliamentary_body=None,
):
    return {
        "name": name,
        "type": event_type,
        "date": "2026-03-20T10:00:00Z",
        "location": None,
        "policy_topics": topics or [],
        "political_actors": actors or [],
        "government_bodies": government_bodies or [],
        "parliamentary_body": parliamentary_body,
        "political_parties": parties or [],
        "confidence": "high",
        "extraction_method": "heuristic",
        "is_generic_fallback": False,
    }


def test_select_template_records_can_balance_by_source():
    records = [
        make_record("g1", "guardian"),
        make_record("g2", "guardian"),
        make_record("p1", "parliament"),
        make_record("p2", "parliament"),
        make_record("u1", "govuk"),
    ]

    selected = select_template_records(records, per_source=1)

    assert [record["id"] for record in selected] == ["g1", "p1", "u1"]


def test_build_gold_template_uses_projected_gold_snapshot():
    record = make_record(
        "g1",
        "guardian",
        topics=["Housing"],
        government_bodies=["HM Treasury"],
        events=[make_event("Rent Reform", topics=["Housing"], government_bodies=["HM Treasury"])],
    )

    template = build_gold_template([record], Path("data/processed/sample.json"))

    assert template["prediction_input"] == "data/processed/sample.json"
    assert len(template["samples"]) == 1
    sample = template["samples"][0]
    assert sample["record_id"] == "g1"
    assert sample["gold"] == project_record(record)
    assert sample["prediction_snapshot"] == project_record(record)


def test_evaluate_samples_reports_metrics_overall_and_by_source():
    prediction_records = [
        make_record(
            "g1",
            "guardian",
            topics=["Housing", "Politics"],
            government_bodies=["HM Treasury"],
            locations=["London"],
            events=[
                make_event(
                    "Rent Reform",
                    topics=["Housing"],
                    government_bodies=["HM Treasury"],
                    actors=["Rachel Reeves"],
                    parties=["Labour Party"],
                )
            ],
        ),
        make_record(
            "p1",
            "parliament",
            topics=["Parliament"],
            government_bodies=[],
            locations=["Westminster"],
            events=[
                make_event(
                    "PMQs",
                    event_type="ParliamentaryDebate",
                    topics=["Parliament"],
                    government_bodies=[],
                    parliamentary_body="House of Commons",
                )
            ],
        ),
    ]

    gold_standard = {
        "samples": [
            {
                "record_id": "g1",
                "source_system": "guardian",
                "gold": {
                    "metadata": {
                        "source_system": "guardian",
                        "source_name": "Test Source",
                        "title": "Title",
                        "url": "https://example.org/g1",
                        "published_at": "2026-03-20T10:00:00Z",
                        "author": "Reporter",
                        "article_type": "NewsArticle",
                    },
                    "topics": ["Housing"],
                    "government_bodies": ["HM Treasury"],
                    "locations": ["London"],
                    "politicians": [],
                    "political_parties": [],
                    "events": [
                        {
                            "name": "Rent Reform",
                            "type": "GovernmentPolicyEvent",
                            "date": "2026-03-20T10:00:00Z",
                            "location": None,
                            "policy_topics": ["Housing"],
                            "political_actors": ["Rachel Reeves"],
                            "government_bodies": ["HM Treasury"],
                            "parliamentary_body": None,
                            "political_parties": ["Labour Party"],
                            "confidence": "high",
                            "extraction_method": "heuristic",
                            "is_generic_fallback": False,
                        }
                    ],
                },
            },
            {
                "record_id": "p1",
                "source_system": "parliament",
                "gold": {
                    "metadata": {
                        "source_system": "parliament",
                        "source_name": "Test Source",
                        "title": "Title",
                        "url": "https://example.org/p1",
                        "published_at": "2026-03-20T10:00:00Z",
                        "author": "Reporter",
                        "article_type": "NewsArticle",
                    },
                    "topics": ["Parliament"],
                    "government_bodies": [],
                    "locations": ["Westminster"],
                    "politicians": [],
                    "political_parties": [],
                    "events": [
                        {
                            "name": "PMQs",
                            "type": "ParliamentaryDebate",
                            "date": "2026-03-20T10:00:00Z",
                            "location": None,
                            "policy_topics": ["Parliament"],
                            "political_actors": [],
                            "government_bodies": [],
                            "parliamentary_body": "House of Commons",
                            "political_parties": [],
                            "confidence": "high",
                            "extraction_method": "heuristic",
                            "is_generic_fallback": False,
                        }
                    ],
                },
            },
        ]
    }

    report = evaluate_samples(prediction_records, gold_standard)

    assert report["sample_count"] == 2
    assert report["missing_prediction_count"] == 0
    assert report["overall"]["metadata_accuracy"] == 1.0
    assert report["overall"]["event_name"]["precision"] == 1.0
    assert report["overall"]["event_name"]["recall"] == 1.0
    assert report["overall"]["event_type"]["f1"] == 1.0
    assert report["overall"]["record_topics"]["precision"] == 0.6667
    assert report["overall"]["record_topics"]["recall"] == 1.0
    assert report["overall"]["institution_links"]["f1"] == 1.0
    assert report["by_source_system"]["guardian"]["metrics"]["record_topics"]["precision"] == 0.5
    assert report["by_source_system"]["parliament"]["metrics"]["institution_links"]["recall"] == 1.0
