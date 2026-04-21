"""Tests for RDF generation against the redesigned event-centred ontology."""

import pytest
from rdflib import RDF
from rdflib.namespace import XSD

from src.json_to_rdf import NEWS, SCHEMA, convert_json_to_rdf


def sample_record(**overrides):
    record = {
        "id": "abc123def456789a",
        "source_system": "guardian",
        "source_name": "The Guardian",
        "title": "Labour responds to spring budget announcement",
        "url": "https://example.com/article",
        "published_at": "2026-03-06T10:00:00Z",
        "updated_at": "2026-03-06T11:00:00Z",
        "author": "Jane Smith",
        "section": "Politics",
        "summary": "A politics update from Westminster.",
        "content": "Labour criticised the Treasury after the spring budget announcement in London.",
        "tags": ["Politics", "Budget"],
        "word_count": 250,
        "article_type": "NewsArticle",
        "sentiment": "Negative",
        "follow_up_candidates": [{"match_key": "The Guardian|Budget", "reason": "same source"}],
        "event_candidates": [
            {
                "name": "Budget",
                "type": "EconomicEvent",
                "date": "2026-03-06",
                "location": "London",
                "source": "heuristic",
            }
        ],
        "entities": {
            "organizations": ["Labour", "Treasury"],
            "people": ["Jane Smith", "Keir Starmer"],
            "politicians": ["Keir Starmer"],
            "political_parties": ["Labour"],
            "government_bodies": ["Treasury"],
            "locations": ["London"],
            "technologies": [],
            "topics": ["Politics", "Economic Policy"],
            "events": ["Budget"],
        },
        "relations": [],
    }
    record.update(overrides)
    return record


class TestConvertJsonToRdf:
    def test_raises_on_empty_input(self):
        with pytest.raises(ValueError, match="No normalised data"):
            convert_json_to_rdf([])

    def test_returns_non_empty_graph(self):
        graph = convert_json_to_rdf([sample_record()])
        assert len(graph) > 0

    def test_article_node_has_expected_metadata(self):
        graph = convert_json_to_rdf([sample_record()])
        article = NEWS["article/abc123def456789a"]

        assert (article, RDF.type, NEWS.NewsArticle) in graph
        assert (article, SCHEMA.headline, None) in graph
        assert (article, NEWS.articleURL, None) in graph
        assert (article, NEWS.publishedDate, None) in graph

    def test_author_and_publisher_nodes_are_created(self):
        graph = convert_json_to_rdf([sample_record()])
        article = NEWS["article/abc123def456789a"]
        author = NEWS["person/Jane_Smith"]
        publisher = NEWS["organisation/The_Guardian"]

        assert (article, NEWS.hasAuthor, author) in graph
        assert (author, RDF.type, NEWS.Journalist) in graph
        assert (article, NEWS.publishedBy, publisher) in graph
        assert (publisher, RDF.type, NEWS.NewsOrganisation) in graph

    def test_core_domain_entities_are_typed(self):
        graph = convert_json_to_rdf([sample_record()])

        actor = NEWS["person/Keir_Starmer"]
        party = NEWS["organisation/Labour_Party"]
        body = NEWS["organisation/HM_Treasury"]
        topic = NEWS["topic/Politics"]
        location = NEWS["location/London"]

        assert (actor, RDF.type, NEWS.PoliticalActor) in graph
        assert (party, RDF.type, NEWS.PoliticalParty) in graph
        assert (body, RDF.type, NEWS.OfficialBody) in graph
        assert (body, RDF.type, NEWS.GovernmentBody) in graph
        assert (body, RDF.type, NEWS.GovernmentDepartment) in graph
        assert (topic, RDF.type, NEWS.PolicyTopic) in graph
        assert (location, RDF.type, NEWS.Location) in graph

    def test_policy_event_triples_are_created(self):
        graph = convert_json_to_rdf([sample_record()])
        article = NEWS["article/abc123def456789a"]
        event = NEWS["event/Budget_2026-03-06_London_abc123de"]
        topic = NEWS["topic/Economic_Policy"]
        actor = NEWS["person/Keir_Starmer"]
        body = NEWS["organisation/HM_Treasury"]
        location = NEWS["location/London"]

        assert (event, RDF.type, NEWS.PolicyEvent) in graph
        assert (event, RDF.type, NEWS.GovernmentPolicyEvent) in graph
        assert (event, NEWS.reportedByArticle, article) in graph
        assert (event, NEWS.concernsPolicyTopic, topic) in graph
        assert (event, NEWS.involvesActor, actor) in graph
        assert (event, NEWS.involvesGovernmentBody, body) in graph
        assert (event, NEWS.occursInLocation, location) in graph
        assert any(obj.datatype == XSD.date for obj in graph.objects(event, NEWS.occursOnDate))

    def test_parliamentary_debate_is_classified_from_event_name(self):
        record = sample_record(
            event_candidates=[
                {
                    "name": "Commons debate on immigration policy",
                    "type": "PoliticalEvent",
                    "date": "2026-03-10",
                    "location": "Westminster",
                    "source": "openai",
                }
            ],
            entities={
                "organizations": [],
                "people": [],
                "politicians": [],
                "political_parties": [],
                "government_bodies": ["House of Commons"],
                "locations": ["Westminster"],
                "technologies": [],
                "topics": ["Immigration", "Parliament"],
                "events": ["Commons debate on immigration policy"],
            },
        )

        graph = convert_json_to_rdf([record])
        event = NEWS["event/Parliamentary_Debate_2026-03-10_Westminster_abc123de"]
        body = NEWS["organisation/House_of_Commons"]

        assert (event, RDF.type, NEWS.ParliamentaryDebate) in graph
        assert (event, NEWS.occursInParliamentaryBody, body) in graph
        assert (event, NEWS.involvesGovernmentBody, body) not in graph

    def test_government_policy_event_does_not_become_debate_from_article_prose(self):
        record = sample_record(
            title="Banknote redesign sparks debate among commentators",
            summary="Opinion column arguing the Bank of England should not duck this debate.",
            event_candidates=[
                {
                    "name": "Banknote Design Policy Announcement",
                    "type": "GovernmentPolicyEvent",
                    "date": "2026-03-16",
                    "location": "Bristol",
                    "source": "openai",
                }
            ],
            entities={
                "organizations": [],
                "people": [],
                "politicians": [],
                "political_parties": [],
                "government_bodies": ["Bank of England", "Treasury"],
                "locations": ["Bristol"],
                "technologies": [],
                "topics": ["Opinion", "Parliament"],
                "events": ["Banknote Design Policy Announcement"],
            },
        )

        graph = convert_json_to_rdf([record])
        event = NEWS["event/Banknote_Design_Policy_Announcement_2026-03-16_Bristol"]

        assert (event, RDF.type, NEWS.GovernmentPolicyEvent) in graph
        assert (event, RDF.type, NEWS.ParliamentaryDebate) not in graph
        assert (event, RDF.type, NEWS.ParliamentaryEvent) not in graph

    def test_ministerial_statement_links_to_department(self):
        record = sample_record(
            source_system="govuk",
            source_name="GOV.UK",
            event_candidates=[
                {
                    "name": "Ministerial statement on social care reform",
                    "type": "PoliticalEvent",
                    "date": "2026-03-12",
                    "location": "London",
                    "source": "official",
                }
            ],
            entities={
                "organizations": [],
                "people": [],
                "politicians": [],
                "political_parties": [],
                "government_bodies": ["Department of Health and Social Care"],
                "locations": ["London"],
                "technologies": [],
                "topics": ["Healthcare", "Government Policy"],
                "events": ["Ministerial statement on social care reform"],
            },
        )

        graph = convert_json_to_rdf([record])
        event = NEWS["event/Ministerial_Statement_2026-03-12_London_abc123de"]
        department = NEWS["organisation/Department_of_Health_and_Social_Care"]

        assert (event, RDF.type, NEWS.MinisterialStatement) in graph
        assert (department, RDF.type, NEWS.GovernmentDepartment) in graph
        assert (event, NEWS.issuedByDepartment, department) in graph

    def test_generic_diplomatic_statement_is_not_typed_as_ministerial_statement(self):
        record = sample_record(
            source_system="govuk",
            source_name="GOV.UK",
            title="UK statement at the UN Security Council",
            summary="A UK statement on international security.",
            event_candidates=[
                {
                    "name": "UK statement at the UN Security Council",
                    "type": "MinisterialStatement",
                    "date": "2026-03-12",
                    "location": "Westminster",
                    "source": "openai",
                }
            ],
            entities={
                "organizations": [],
                "people": [],
                "politicians": [],
                "political_parties": [],
                "government_bodies": [],
                "locations": ["Westminster"],
                "technologies": [],
                "topics": ["Government Policy"],
                "events": ["UK statement at the UN Security Council"],
            },
        )

        graph = convert_json_to_rdf([record])
        event = NEWS["event/UK_statement_at_the_UN_Security_Council_2026-03-12_Westminster"]

        assert (event, RDF.type, NEWS.PolicyEvent) in graph
        assert (event, RDF.type, NEWS.MinisterialStatement) not in graph

    def test_generic_parliament_policy_announcement_does_not_become_ministerial_without_department(
        self,
    ):
        record = sample_record(
            source_system="parliament",
            source_name="UK Parliament",
            title="National Scheme of Delegation",
            summary=None,
            event_candidates=[
                {
                    "name": "Policy Announcement",
                    "type": "MinisterialStatement",
                    "date": "2026-03-26",
                    "location": None,
                    "source": "heuristic",
                    "policy_topics": ["Parliament"],
                    "government_bodies": [],
                }
            ],
            entities={
                "organizations": [],
                "people": [],
                "politicians": [],
                "political_parties": [],
                "government_bodies": [],
                "locations": [],
                "technologies": [],
                "topics": ["Parliament"],
                "events": ["Policy Announcement"],
            },
        )

        graph = convert_json_to_rdf([record])
        event = NEWS["event/Policy_Announcement_2026-03-26_abc123de"]

        assert (event, RDF.type, NEWS.PolicyEvent) in graph
        assert (event, RDF.type, NEWS.MinisterialStatement) not in graph

    def test_events_only_link_to_bodies_supported_by_context(self):
        record = sample_record(
            title="Prime minister questioned over energy bills at PMQs",
            summary="The Commons exchange focused on energy and public spending.",
            event_candidates=[
                {
                    "name": "Prime Minister's Questions",
                    "type": "ParliamentaryDebate",
                    "date": "2026-03-19",
                    "location": "Westminster",
                    "source": "heuristic",
                }
            ],
            entities={
                "organizations": [],
                "people": [],
                "politicians": [],
                "political_parties": [],
                "government_bodies": ["House of Commons", "House of Lords", "Treasury"],
                "locations": ["Westminster"],
                "technologies": [],
                "topics": ["Parliament", "Economic Policy"],
                "events": ["Prime Minister's Questions"],
            },
        )

        graph = convert_json_to_rdf([record])
        event = NEWS["event/Prime_Minister_s_Questions_2026-03-19_Westminster"]
        commons = NEWS["organisation/House_of_Commons"]
        lords = NEWS["organisation/House_of_Lords"]
        treasury = NEWS["organisation/Treasury"]

        assert (event, NEWS.occursInParliamentaryBody, commons) in graph
        assert (event, NEWS.occursInParliamentaryBody, lords) not in graph
        assert (event, NEWS.involvesGovernmentBody, treasury) not in graph

    def test_official_sources_create_source_records_and_link_events(self):
        record = sample_record(
            id="govuk-1",
            source_system="govuk",
            source_name="GOV.UK",
            title="Ministerial statement on planning reform",
            event_candidates=[
                {
                    "name": "Ministerial statement on planning reform",
                    "type": "PoliticalEvent",
                    "date": "2026-03-20",
                    "location": "London",
                    "source": "official",
                }
            ],
            entities={
                "organizations": [],
                "people": [],
                "politicians": [],
                "political_parties": [],
                "government_bodies": ["Department for Levelling Up"],
                "locations": ["London"],
                "technologies": [],
                "topics": ["Housing", "Government Policy"],
                "events": ["Ministerial statement on planning reform"],
            },
        )

        graph = convert_json_to_rdf([record])
        event = NEWS["event/Ministerial_Statement_2026-03-20_London_govuk-1"]
        source_record = NEWS["source-record/govuk/govuk-1"]

        assert (source_record, RDF.type, NEWS.SourceRecord) in graph
        assert (source_record, RDF.type, NEWS.GovernmentSourceRecord) in graph
        assert (event, NEWS.representedInOfficialSource, source_record) in graph

    def test_parliament_written_statement_is_not_promoted_to_parliamentary_event(self):
        record = sample_record(
            source_system="parliament",
            source_name="UK Parliament",
            title="National Scheme of Delegation",
            summary="Written statement laid before the House.",
            section="Lords",
            event_candidates=[
                {
                    "name": "Policy Announcement",
                    "type": "GovernmentPolicyEvent",
                    "date": "2026-03-26",
                    "location": None,
                    "source": "openai",
                }
            ],
            entities={
                "organizations": [],
                "people": [],
                "politicians": [],
                "political_parties": [],
                "government_bodies": [],
                "locations": [],
                "technologies": [],
                "topics": ["Parliament"],
                "events": ["Policy Announcement"],
            },
        )

        graph = convert_json_to_rdf([record])
        event = NEWS["event/Policy_Announcement_2026-03-26_abc123de"]

        assert (event, RDF.type, NEWS.GovernmentPolicyEvent) in graph
        assert (event, RDF.type, NEWS.ParliamentaryEvent) not in graph

    def test_low_confidence_generic_event_is_not_upgraded_from_context_alone(self):
        record = sample_record(
            title="Commons voices clash over migration tactics",
            summary="MPs argued over migration tactics in a heated exchange.",
            event_candidates=[
                {
                    "name": "Policy Announcement",
                    "type": "PolicyEvent",
                    "date": "2026-03-26",
                    "location": "Westminster",
                    "source": "heuristic",
                    "confidence": "Low",
                }
            ],
            entities={
                "organizations": [],
                "people": [],
                "politicians": [],
                "political_parties": [],
                "government_bodies": ["House of Commons"],
                "locations": ["Westminster"],
                "technologies": [],
                "topics": ["Parliament"],
                "events": ["Policy Announcement"],
            },
        )

        graph = convert_json_to_rdf([record])
        event = NEWS["event/Policy_Announcement_2026-03-26_Westminster_abc123de"]

        assert (event, RDF.type, NEWS.PolicyEvent) in graph
        assert (event, RDF.type, NEWS.ParliamentaryDebate) not in graph

    def test_specific_event_names_gain_canonical_labels(self):
        record = sample_record(
            event_candidates=[
                {
                    "name": "New measures to support cost of living",
                    "type": "EconomicEvent",
                    "date": "2026-04-05",
                    "location": None,
                    "source": "openai",
                }
            ],
            entities={
                "organizations": ["Treasury"],
                "people": [],
                "politicians": [],
                "political_parties": [],
                "government_bodies": ["Treasury"],
                "locations": [],
                "technologies": [],
                "topics": ["Economic Policy", "Public Spending"],
                "events": ["New measures to support cost of living"],
            },
        )

        graph = convert_json_to_rdf([record])
        event = NEWS["event/Budget_2026-04-05_abc123de"]
        event_names = {str(value) for value in graph.objects(event, SCHEMA.name)}

        assert "Budget" in event_names

    def test_event_specific_fields_prevent_article_level_over_attachment(self):
        record = sample_record(
            event_candidates=[
                {
                    "name": "Budget",
                    "type": "GovernmentPolicyEvent",
                    "date": "2026-03-06",
                    "location": "London",
                    "source": "heuristic",
                    "confidence": "high",
                    "policy_topics": ["Economic Policy"],
                    "political_actors": ["Keir Starmer"],
                    "government_bodies": ["Treasury"],
                    "parliamentary_body": None,
                    "political_parties": ["Labour"],
                    "evidence_spans": ["Budget statement in London."],
                },
                {
                    "name": "Prime Minister's Questions",
                    "type": "ParliamentaryDebate",
                    "date": "2026-03-07",
                    "location": "Westminster",
                    "source": "heuristic",
                    "confidence": "high",
                    "policy_topics": ["Parliament"],
                    "political_actors": [],
                    "government_bodies": [],
                    "parliamentary_body": "House of Commons",
                    "political_parties": [],
                    "evidence_spans": ["PMQs returned to the Commons."],
                },
            ],
            entities={
                "organizations": [],
                "people": [],
                "politicians": ["Keir Starmer"],
                "political_parties": ["Labour"],
                "government_bodies": ["Treasury", "House of Commons"],
                "locations": ["London", "Westminster"],
                "technologies": [],
                "topics": ["Economic Policy", "Parliament"],
                "events": ["Budget", "Prime Minister's Questions"],
            },
        )

        graph = convert_json_to_rdf([record])
        budget = NEWS["event/Budget_2026-03-06_London_abc123de"]
        pmqs = NEWS["event/Prime_Minister_s_Questions_2026-03-07_Westminster"]
        actor = NEWS["person/Keir_Starmer"]
        econ_topic = NEWS["topic/Economic_Policy"]
        parliament_topic = NEWS["topic/Parliament"]

        assert (budget, NEWS.involvesActor, actor) in graph
        assert (pmqs, NEWS.involvesActor, actor) not in graph
        assert (budget, NEWS.concernsPolicyTopic, econ_topic) in graph
        assert (budget, NEWS.concernsPolicyTopic, parliament_topic) not in graph
        assert (pmqs, NEWS.concernsPolicyTopic, parliament_topic) in graph
        assert (pmqs, NEWS.concernsPolicyTopic, econ_topic) not in graph

    def test_single_party_event_does_not_create_member_of_party_link(self):
        record = sample_record(
            event_candidates=[
                {
                    "name": "Budget",
                    "type": "GovernmentPolicyEvent",
                    "date": "2026-03-06",
                    "location": "London",
                    "source": "heuristic",
                    "confidence": "high",
                    "policy_topics": ["Economic Policy"],
                    "political_actors": ["Keir Starmer"],
                    "government_bodies": ["Treasury"],
                    "parliamentary_body": None,
                    "political_parties": ["Labour"],
                    "evidence_spans": ["Labour responded to the budget."],
                }
            ],
        )

        graph = convert_json_to_rdf([record])
        actor = NEWS["person/Keir_Starmer"]
        party = NEWS["organisation/Labour_Party"]

        assert (actor, NEWS.memberOfParty, party) not in graph

    def test_event_only_entities_are_minted_and_linked_in_rdf(self):
        record = sample_record(
            event_candidates=[
                {
                    "name": "NHS Reform Options",
                    "type": "GovernmentPolicyEvent",
                    "date": "2026-03-20",
                    "location": "Manchester",
                    "source": "openai",
                    "confidence": "high",
                    "policy_topics": ["Healthcare"],
                    "political_actors": ["Wes Streeting"],
                    "government_bodies": ["NHS England"],
                    "parliamentary_body": None,
                    "political_parties": ["Labour"],
                    "evidence_spans": ["Wes Streeting outlined NHS reform options."],
                }
            ],
            entities={
                "organizations": [],
                "people": [],
                "politicians": [],
                "political_parties": [],
                "government_bodies": [],
                "locations": ["Manchester"],
                "technologies": [],
                "topics": [],
                "events": ["NHS Reform Options"],
            },
        )

        graph = convert_json_to_rdf([record])
        event = NEWS["event/NHS_Reform_Options_2026-03-20_Manchester"]
        actor = NEWS["person/Wes_Streeting"]
        topic = NEWS["topic/Healthcare"]
        body = NEWS["organisation/NHS_England"]
        party = NEWS["organisation/Labour_Party"]

        assert (event, NEWS.involvesActor, actor) in graph
        assert (event, NEWS.concernsPolicyTopic, topic) in graph
        assert (event, NEWS.involvesGovernmentBody, body) in graph
        assert (actor, NEWS.memberOfParty, party) not in graph

    def test_member_of_party_is_not_inferred_for_multiple_event_actors(self):
        record = sample_record(
            event_candidates=[
                {
                    "name": "Budget",
                    "type": "GovernmentPolicyEvent",
                    "date": "2026-03-06",
                    "location": "London",
                    "source": "heuristic",
                    "confidence": "high",
                    "policy_topics": ["Economic Policy"],
                    "political_actors": ["Keir Starmer", "Rachel Reeves"],
                    "government_bodies": ["Treasury"],
                    "parliamentary_body": None,
                    "political_parties": ["Labour"],
                    "evidence_spans": ["Labour responded to the budget."],
                }
            ],
            entities={
                "organizations": [],
                "people": [],
                "politicians": ["Keir Starmer", "Rachel Reeves"],
                "political_parties": ["Labour"],
                "government_bodies": ["Treasury"],
                "locations": ["London"],
                "technologies": [],
                "topics": ["Economic Policy"],
                "events": ["Budget"],
            },
        )

        graph = convert_json_to_rdf([record])
        starmer = NEWS["person/Keir_Starmer"]
        reeves = NEWS["person/Rachel_Reeves"]
        party = NEWS["organisation/Labour_Party"]

        assert (starmer, NEWS.memberOfParty, party) not in graph
        assert (reeves, NEWS.memberOfParty, party) not in graph
