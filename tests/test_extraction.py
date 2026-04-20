"""Behavioral tests for the current extraction pipeline."""

import pytest

from src.data_extraction import (
    build_article_id,
    choose_event_location,
    classify_article_type,
    classify_sentiment,
    extract_relevant_information,
    infer_event_type,
    normalize_event_name,
    sanitize_locations,
    sanitize_organizations,
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

        assert "Labour" in entities["political_parties"]
        assert "Treasury" in entities["government_bodies"]
        assert "Politics" in entities["topics"] or "Economic Policy" in entities["topics"]

    def test_filters_people_from_locations(self):
        article = make_article(
            title="Nigel Farage launches Reform UK local election push",
            content=(
                "Nigel Farage said Reform UK was ready for local election campaigning in England "
                "and Scotland after a press conference in Westminster."
            ),
            tags=["Reform UK", "Nigel Farage", "Politics"],
        )

        record = extract_relevant_information([article])[0]
        locations = set(record["entities"]["locations"])

        assert "Nigel Farage" not in locations
        assert "Farage" not in locations
        assert "England" in locations

    def test_sanitize_locations_filters_role_and_noise_terms(self):
        locations = sanitize_locations(
            ["London", "British", "Labour MPs", "PMQs", "UK The", "Manchester"]
        )
        assert locations == ["London", "Manchester"]

    def test_sanitize_locations_removes_entity_prefix_overlap(self):
        locations = sanitize_locations(
            ["MSI Reproductive", "London"],
            blocked_entities={"MSI Reproductive Choices"},
        )
        assert locations == ["London"]

    def test_sanitize_organizations_filters_tag_noise(self):
        organisations = sanitize_organizations(
            ["Birmingham Labour West Midlands News", "BBC News", "Treasury"]
        )
        assert organisations == ["BBC News", "Treasury"]

    def test_choose_event_location_prefers_westminster_for_parliamentary_events(self):
        location = choose_event_location(
            "Prime Minister's Questions",
            "ParliamentaryDebate",
            ["Cyprus", "Westminster", "London"],
            "pmqs dominated the commons today",
            ["Parliament", "Politics"],
        )
        assert location == "Westminster"

    def test_choose_event_location_drops_broad_location_when_no_parliamentary_anchor(self):
        location = choose_event_location(
            "Prime Minister's Questions",
            "ParliamentaryDebate",
            ["England", "Iran"],
            "pmqs dominated the commons today",
            ["Parliament", "Politics"],
        )
        assert location is None

    def test_does_not_create_election_event_without_election_signal(self):
        article = make_article(
            title="Reform UK controversies overshadow policy launch",
            content=(
                "Nigel Farage said the party had learned lessons from the last general election "
                "but the press conference focused on pensions policy and internal discipline."
            ),
            tags=["Politics", "Reform UK", "Nigel Farage"],
        )

        record = extract_relevant_information([article])[0]
        event_names = {event["name"] for event in record["event_candidates"]}

        assert "Election" not in event_names
        assert "General Election" not in event_names

    def test_does_not_fallback_to_policy_announcement_from_body_noise_alone(self):
        article = make_article(
            title="Lords attendance records raise fresh questions",
            summary="Records show some peers rarely attend the chamber.",
            content=(
                "The House of Lords attendance records prompted criticism. A separate paragraph "
                "noted previous government plans and policy proposals, but the article itself "
                "was about attendance and scrutiny rather than a new announcement."
            ),
            tags=["Politics", "House of Lords"],
        )

        record = extract_relevant_information([article])[0]
        assert record["event_candidates"] == []

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
                        "type": "GovernmentPolicyEvent",
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

    def test_pmqs_is_treated_as_parliamentary_debate(self):
        assert infer_event_type("Prime Minister's Questions") == "ParliamentaryDebate"

    def test_normalize_event_name_collapses_pmqs_variant(self):
        assert (
            normalize_event_name("Prime Minister's Questions (PMQs)")
            == "Prime Minister's Questions"
        )

    def test_openai_event_type_is_upgraded_to_more_specific_ontology_type(self, monkeypatch):
        monkeypatch.setattr(
            "src.data_extraction.maybe_extract_article_with_openai",
            lambda article, text, heuristic_result: {
                "people": [],
                "organizations": [],
                "locations": ["London"],
                "topics": ["Parliament"],
                "politicians": [],
                "political_parties": [],
                "government_bodies": [],
                "sentiment": "Neutral",
                "article_type": "NewsArticle",
                "events": [
                    {
                        "name": "Prime Minister's Questions",
                        "type": "ParliamentaryEvent",
                        "date": "2026-03-20",
                        "location": "PMQs",
                    }
                ],
            },
        )

        article = make_article(
            title="PMQs sees Starmer clash with opposition leader",
            summary="Prime Minister's Questions returned to the Commons this week.",
            content="Prime Minister's Questions dominated Westminster politics in London.",
            tags=["Politics", "Parliament"],
        )
        record = extract_relevant_information([article])[0]
        event = record["event_candidates"][0]

        assert event["name"] == "Prime Minister's Questions"
        assert event["type"] == "ParliamentaryDebate"
        assert event["location"] == "Westminster"

    def test_openai_historical_events_outside_window_are_rejected(self, monkeypatch):
        monkeypatch.setattr(
            "src.data_extraction.maybe_extract_article_with_openai",
            lambda article, text, heuristic_result: {
                "people": [],
                "organizations": [],
                "locations": ["Westminster"],
                "topics": ["Parliament"],
                "politicians": [],
                "political_parties": [],
                "government_bodies": [],
                "sentiment": "Neutral",
                "article_type": "NewsArticle",
                "events": [
                    {
                        "name": "Historic Parliamentary Reform Clash",
                        "type": "ParliamentaryEvent",
                        "date": "2008-01-01",
                        "location": "Westminster",
                    }
                ],
            },
        )

        article = make_article(
            title="Retrospective on a long Commons career",
            summary="A retrospective piece reflecting on decades in Westminster.",
            content="The article reflects on earlier clashes in Parliament and political life.",
            tags=["Politics", "Parliament"],
        )
        record = extract_relevant_information([article])[0]

        assert record["event_candidates"] == []

    def test_specific_openai_event_replaces_generic_policy_announcement(self, monkeypatch):
        monkeypatch.setattr(
            "src.data_extraction.maybe_extract_article_with_openai",
            lambda article, text, heuristic_result: {
                "people": [],
                "organizations": [],
                "locations": ["London"],
                "topics": ["Government Policy"],
                "politicians": [],
                "political_parties": [],
                "government_bodies": [],
                "sentiment": "Neutral",
                "article_type": "NewsArticle",
                "events": [
                    {
                        "name": "Digital ID Policy Rollout",
                        "type": "GovernmentPolicyEvent",
                        "date": "2026-03-20",
                        "location": "London",
                    }
                ],
            },
        )

        article = make_article(
            title="Ministers to launch phased digital ID rollout",
            summary="Cabinet ministers prepare a new digital identity launch.",
            content="The government announced plans for a phased digital ID rollout in London.",
            tags=["Government Policy"],
        )
        record = extract_relevant_information([article])[0]
        event_names = {event["name"] for event in record["event_candidates"]}

        assert "Digital ID Policy Rollout" in event_names
        assert "Policy Announcement" not in event_names

    def test_parliament_written_statement_demotes_generic_parliamentary_event(self, monkeypatch):
        monkeypatch.setattr(
            "src.data_extraction.maybe_extract_article_with_openai",
            lambda article, text, heuristic_result: {
                "people": [],
                "organizations": [],
                "locations": [],
                "topics": ["Parliament"],
                "politicians": [],
                "political_parties": [],
                "government_bodies": [],
                "sentiment": "Neutral",
                "article_type": "NewsArticle",
                "events": [
                    {
                        "name": "Policy Announcement",
                        "type": "ParliamentaryEvent",
                        "date": "2026-03-26",
                        "location": None,
                    }
                ],
            },
        )

        article = make_article(
            source_system="parliament",
            source_name="UK Parliament",
            title="National Scheme of Delegation",
            section="Lords",
            summary="Written statement laid before the House.",
            content="A written ministerial statement was laid before Parliament.",
            tags=["Lords"],
        )
        record = extract_relevant_information([article])[0]

        assert record["event_candidates"]
        assert record["event_candidates"][0]["name"] == "Ministerial Statement"
        assert record["event_candidates"][0]["type"] == "MinisterialStatement"
