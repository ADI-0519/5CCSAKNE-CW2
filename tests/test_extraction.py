"""Behavioral tests for the current extraction pipeline."""

import pytest

from src.data_extraction import (
    build_article_id,
    build_extraction_audit_metrics,
    choose_event_location,
    classify_article_type,
    classify_sentiment,
    coerce_event_type_for_source,
    extract_relevant_information,
    infer_event_type,
    normalize_event_name,
    sanitize_locations,
    sanitize_organizations,
    should_use_openai_extraction,
)


def make_article(**overrides):
    article = {
        "id": "article-1",
        "source_system": "guardian",
        "source_name": "The Guardian",
        "title": "Keir Starmer faces pressure over budget plans",
        "url": "https://example.com/article-1",
        "published_at": "2026-03-25T10:00:00Z",
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

        assert "Labour Party" in entities["political_parties"]
        assert "HM Treasury" in entities["government_bodies"]
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

    def test_optional_spacy_candidates_are_used_as_first_pass_entities(self, monkeypatch):
        monkeypatch.setattr(
            "src.data_extraction.extract_spacy_entities",
            lambda text: {
                "people": ["Wes Streeting"],
                "organizations": ["Institute for Fiscal Studies"],
                "locations": ["Birmingham"],
            },
        )

        article = make_article(
            title="Thinktank warns over fiscal pressure",
            content=(
                "Wes Streeting met the Institute for Fiscal Studies. "
                "Birmingham leaders later reacted."
            ),
            tags=["Politics"],
        )

        record = extract_relevant_information([article])[0]

        assert "Wes Streeting" in record["entities"]["people"]
        assert "Institute for Fiscal Studies" in record["entities"]["organizations"]
        assert "Birmingham" in record["entities"]["locations"]

    def test_sanitize_locations_filters_role_and_noise_terms(self):
        locations = sanitize_locations(
            ["London", "British", "Labour MPs", "PMQs", "UK The", "Manchester"]
        )
        assert locations == ["London", "Manchester"]

    def test_sanitize_locations_filters_department_codes_and_slug_noise(self):
        locations = sanitize_locations(["DfE", "PB202", "north-york", "England", "London"])
        assert locations == ["England", "London"]

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

    def test_does_not_fallback_to_policy_announcement_from_weak_government_mentions_alone(self):
        article = make_article(
            title="Ministers argue over tactics ahead of local media round",
            summary="Senior figures traded criticism over presentation and discipline.",
            content=(
                "Government ministers and Treasury allies disagreed over tactics and media handling. "
                "The piece discusses political pressure, but it does not describe an announcement, "
                "proposal, plan, consultation, guidance, or statement."
            ),
            tags=["Politics", "Government Policy"],
        )

        record = extract_relevant_information([article])[0]

        assert record["event_candidates"] == []

    def test_obituary_does_not_get_generic_policy_fallback(self):
        article = make_article(
            title="David Winnick obituary",
            summary="A retrospective on a long parliamentary career.",
            content=(
                "The obituary reflects on decades in politics, Westminster, and Labour history "
                "without describing a new announcement or current policy event."
            ),
            tags=["Politics", "Parliament"],
        )

        record = extract_relevant_information([article])[0]

        assert record["event_candidates"] == []

    def test_specific_event_candidates_carry_confidence(self):
        article = make_article(
            title="Treasury announces spring budget as Labour responds",
            content=(
                "The Treasury announced the spring budget in London as Labour criticised the "
                "proposal in Parliament."
            ),
            tags=["Politics", "Labour", "Budget"],
        )

        record = extract_relevant_information([article])[0]

        assert record["event_candidates"]
        assert record["event_candidates"][0]["confidence"] in {"medium", "high", "low"}

    def test_specific_event_candidates_include_event_scoped_fields(self):
        article = make_article(
            title="Treasury announces spring budget as Labour responds",
            content=(
                "Keir Starmer said Labour would respond after the Treasury announced the spring "
                "budget in London."
            ),
            tags=["Politics", "Labour", "Budget"],
        )

        record = extract_relevant_information([article])[0]
        event = record["event_candidates"][0]

        assert "policy_topics" in event
        assert "political_actors" in event
        assert "government_bodies" in event
        assert "political_parties" in event
        assert "evidence_spans" in event
        assert "extraction_method" in event

    def test_liveblog_without_clear_event_signal_does_not_get_generic_policy_fallback(self):
        article = make_article(
            title="Social media has led to a complete rewiring of childhood, says minister - UK politics live",
            url="https://example.com/politics/live/2026/mar/27/uk-politics-live",
            summary="Rolling coverage of UK politics through the day.",
            content=(
                "Rolling updates covered several reactions from ministers and opposition figures "
                "throughout the day without a single clearly bounded policy event."
            ),
            tags=["Politics", "Government Policy"],
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
                        "name": "NHS Reform Options",
                        "type": "GovernmentPolicyEvent",
                        "date": "2026-03-25",
                        "location": "Manchester",
                    }
                ],
            },
        )

        article = make_article(
            title="Officials outline NHS reform options",
            summary="A briefing note outlined possible health reforms.",
            content="Officials outlined possible reforms and options in Manchester.",
            tags=[],
            section="UK news",
        )
        record = extract_relevant_information([article])[0]

        assert record["sentiment"] == "Positive"
        assert record["article_type"] == "OpinionArticle"
        assert "Wes Streeting" in record["entities"]["people"]
        assert "NHS England" in record["entities"]["government_bodies"]
        assert "Healthcare" in record["entities"]["topics"]
        assert "NHS Reform Options" in record["entities"]["events"]

    def test_event_scoped_openai_entities_are_promoted_to_record_entities(self, monkeypatch):
        monkeypatch.setattr(
            "src.data_extraction.maybe_extract_article_with_openai",
            lambda article, text, heuristic_result: {
                "people": [],
                "organizations": [],
                "locations": ["Manchester"],
                "topics": [],
                "politicians": [],
                "political_parties": [],
                "government_bodies": [],
                "sentiment": "Neutral",
                "article_type": "NewsArticle",
                "events": [
                    {
                        "name": "NHS Reform Options",
                        "type": "GovernmentPolicyEvent",
                        "date": "2026-03-25",
                        "location": "Manchester",
                        "policy_topics": ["Healthcare"],
                        "political_actors": ["Wes Streeting"],
                        "government_bodies": ["NHS England"],
                        "parliamentary_body": None,
                        "political_parties": ["Labour"],
                        "evidence_spans": ["Wes Streeting outlined NHS reform options."],
                        "confidence": "high",
                    }
                ],
            },
        )

        article = make_article(
            title="Officials outline NHS reform options",
            summary="A briefing note outlined possible health reforms.",
            content="Wes Streeting outlined NHS reform options in Manchester.",
            tags=[],
            section="UK news",
        )
        record = extract_relevant_information([article])[0]
        event = record["event_candidates"][0]

        assert "Wes Streeting" in record["entities"]["politicians"]
        assert "Labour Party" in record["entities"]["political_parties"]
        assert "NHS England" in record["entities"]["government_bodies"]
        assert "Healthcare" in record["entities"]["topics"]
        assert event["confidence"] == "high"
        assert event["extraction_method"] == "openai"

    def test_openai_event_with_heuristic_support_becomes_hybrid(self, monkeypatch):
        monkeypatch.setattr(
            "src.data_extraction.maybe_extract_article_with_openai",
            lambda article, text, heuristic_result: {
                "people": [],
                "organizations": ["Treasury", "Labour"],
                "locations": ["London"],
                "topics": ["Economic Policy"],
                "politicians": ["Keir Starmer"],
                "political_parties": ["Labour"],
                "government_bodies": ["Treasury"],
                "sentiment": "Neutral",
                "article_type": "NewsArticle",
                "events": [
                    {
                        "name": "Budget",
                        "type": "GovernmentPolicyEvent",
                        "date": "2026-03-25",
                        "location": "London",
                        "policy_topics": [],
                        "political_actors": [],
                        "government_bodies": [],
                        "parliamentary_body": None,
                        "political_parties": [],
                        "evidence_spans": [],
                        "confidence": "",
                    }
                ],
            },
        )

        article = make_article(
            title="Treasury announces budget as Labour responds",
            summary="Keir Starmer criticised the Treasury in London.",
            content="Keir Starmer said Labour would respond after the Treasury announced the budget in London.",
            tags=["Politics", "Budget", "Labour"],
            section="Politics",
        )

        record = extract_relevant_information([article])[0]
        event = record["event_candidates"][0]

        assert event["extraction_method"] == "hybrid"
        assert event["confidence"] in {"medium", "high"}

    def test_pmqs_is_treated_as_parliamentary_debate(self):
        assert infer_event_type("Prime Minister's Questions") == "ParliamentaryDebate"

    def test_generic_statement_is_not_promoted_to_ministerial_statement(self):
        assert (
            infer_event_type("UK statement at the UN Security Council") == "GovernmentPolicyEvent"
        )

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
                        "date": "2026-03-25",
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
                        "date": "2026-03-25",
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
        assert record["event_candidates"][0]["type"] == "ParliamentaryEvent"

    def test_ambiguous_parliament_event_stays_parliamentary_instead_of_becoming_government(self):
        article = make_article(
            source_system="parliament",
            source_name="UK Parliament",
            title="Delegation Scheme Update",
            section="Commons",
            summary="Parliament considered an updated delegation scheme.",
            content=(
                "Parliament considered an updated delegation scheme in Westminster. "
                "The record describes committee discussion rather than a ministerial briefing."
            ),
            tags=["Commons"],
        )
        signals = {
            "salient_text_lower": "delegation scheme update parliament commons",
            "text_lower": (
                "parliament considered an updated delegation scheme in westminster. "
                "the record describes committee discussion rather than a ministerial briefing."
            ),
            "parliament_written_statement": False,
        }

        result = coerce_event_type_for_source(
            article,
            "Delegation Scheme Update",
            "GovernmentPolicyEvent",
            signals,
        )

        assert result == "ParliamentaryEvent"

    def test_govuk_policy_paper_gets_source_aware_fallback_event(self):
        article = make_article(
            source_system="govuk",
            source_name="GOV.UK",
            title="National Cancer Plan for England",
            section="policy_paper",
            summary="Government sets out a long-term policy plan for cancer services.",
            content="Government sets out a long-term policy plan for cancer services in England.",
            tags=["policy_paper"],
            author=None,
        )

        record = extract_relevant_information([article])[0]

        assert record["event_candidates"]
        assert record["event_candidates"][0]["name"] == "National Cancer Plan for England"
        assert record["event_candidates"][0]["type"] == "GovernmentPolicyEvent"

    def test_govuk_speech_fallback_stays_government_policy_event(self):
        article = make_article(
            source_system="govuk",
            source_name="GOV.UK",
            title="Trade Minister Speech at Chatham House",
            section="speech",
            summary="Speech on trade and growth.",
            content="The Trade Minister set out the government's trade priorities at Chatham House.",
            tags=["speech"],
            author=None,
        )

        record = extract_relevant_information([article])[0]

        assert record["event_candidates"]
        assert record["event_candidates"][0]["type"] == "GovernmentPolicyEvent"

    def test_fcdo_statement_infers_foreign_office_department_body(self):
        article = make_article(
            source_system="govuk",
            source_name="GOV.UK",
            title="Summoning of the Iranian Ambassador to the United Kingdom: FCDO statement",
            section="press_release",
            summary="Foreign affairs statement issued by the government.",
            content="The FCDO issued a statement after summoning the Iranian Ambassador.",
            tags=["statement"],
            author=None,
        )

        record = extract_relevant_information([article])[0]

        assert (
            "Foreign, Commonwealth and Development Office"
            in record["entities"]["government_bodies"]
        )

    def test_generic_parliament_policy_announcement_without_department_demotes_from_ministerial(
        self,
    ):
        article = make_article(
            source_system="parliament",
            source_name="UK Parliament",
            title="National Scheme of Delegation",
            section="Lords",
            summary=None,
            content=(
                "My Honourable Friend has today made the following statement. "
                "Planning is principally a local activity."
            ),
            tags=[],
            author=None,
        )

        record = extract_relevant_information([article])[0]

        assert record["event_candidates"]
        assert record["event_candidates"][0]["name"] == "Policy Announcement"
        assert record["event_candidates"][0]["type"] == "ParliamentaryEvent"

    def test_govuk_policy_paper_without_explicit_event_signal_does_not_get_fallback_event(self):
        article = make_article(
            source_system="govuk",
            source_name="GOV.UK",
            title="HM Treasury Market Engagement Group",
            section="policy_paper",
            summary="Reference material for market participants.",
            content="Reference material for market participants.",
            tags=["policy_paper"],
            author=None,
        )

        record = extract_relevant_information([article])[0]

        assert record["event_candidates"] == []

    def test_govuk_person_record_does_not_get_fallback_event(self):
        article = make_article(
            source_system="govuk",
            source_name="GOV.UK",
            title="Dr Vanessa Ogden CBE",
            section="person",
            summary="Dr Vanessa Ogden CBE is the Regional Director for London.",
            content="Dr Vanessa Ogden CBE is the Regional Director for London.",
            tags=["person"],
            author=None,
        )

        record = extract_relevant_information([article])[0]

        assert record["event_candidates"] == []

    def test_openai_extraction_is_skipped_for_structured_sources(self):
        heuristic_result = {
            "people": [],
            "organizations": [],
            "locations": [],
            "topics": ["Government Policy"],
            "politicians": [],
            "political_parties": [],
            "government_bodies": [],
            "sentiment": "Neutral",
            "article_type": "NewsArticle",
            "events": [],
        }
        article = make_article(source_system="govuk", source_name="GOV.UK")

        assert should_use_openai_extraction(article, heuristic_result) is False

    def test_openai_extraction_is_skipped_for_liveblogs(self):
        heuristic_result = {
            "people": [],
            "organizations": [],
            "locations": [],
            "topics": ["Politics"],
            "politicians": [],
            "political_parties": [],
            "government_bodies": [],
            "sentiment": "Neutral",
            "article_type": "BreakingNewsArticle",
            "events": [],
        }
        article = make_article(
            title="UK politics: ministers under pressure - as it happened",
            url="https://example.com/live/article",
        )

        assert should_use_openai_extraction(article, heuristic_result) is False

    def test_openai_extraction_is_skipped_when_heuristics_are_already_strong(self):
        heuristic_result = {
            "people": [],
            "organizations": [],
            "locations": ["London"],
            "topics": ["Government Policy"],
            "politicians": ["Keir Starmer"],
            "political_parties": [],
            "government_bodies": ["Treasury"],
            "sentiment": "Neutral",
            "article_type": "NewsArticle",
            "events": [
                {
                    "name": "Spring Statement",
                    "type": "GovernmentPolicyEvent",
                    "date": "2026-03-25",
                    "location": "London",
                    "source": "heuristic",
                }
            ],
        }
        article = make_article(title="Treasury confirms spring statement timetable")

        assert should_use_openai_extraction(article, heuristic_result) is False


def test_build_extraction_audit_metrics_counts_generic_fallbacks():
    records = [
        {
            "event_candidates": [
                {
                    "name": "Policy Announcement",
                    "confidence": "low",
                    "extraction_method": "heuristic",
                    "is_generic_fallback": True,
                },
                {
                    "name": "Spring Statement",
                    "confidence": "high",
                    "extraction_method": "hybrid",
                    "is_generic_fallback": False,
                },
            ]
        },
        {
            "event_candidates": [
                {
                    "name": "Budget",
                    "confidence": "medium",
                    "extraction_method": "openai",
                    "is_generic_fallback": True,
                }
            ]
        },
    ]

    metrics = build_extraction_audit_metrics(records)

    assert metrics["record_count"] == 2
    assert metrics["event_count"] == 3
    assert metrics["generic_fallback_event_count"] == 2
    assert metrics["records_with_generic_fallback"] == 2
    assert metrics["generic_fallback_name_counts"] == {"Budget": 1, "Policy Announcement": 1}
    assert metrics["confidence_counts"] == {"high": 1, "low": 1, "medium": 1}
