"""Tests for ontology-aligned KG completion/enrichment."""

import json

from rdflib import RDF, Literal
from rdflib.namespace import XSD

from src.build_ontology import NEWS, SCHEMA, build_ontology
from src.complete_kg import enrich_graph
from src.json_to_rdf import organisation_uri, person_uri


def add_named_entity(graph, entity_uri, label, rdf_types):
    for rdf_type in rdf_types:
        graph.add((entity_uri, RDF.type, rdf_type))
    graph.add((entity_uri, SCHEMA.name, Literal(label)))


def test_enrich_graph_adds_reports_on_inverse_links():
    graph = build_ontology()
    article_uri = NEWS["article/report_a"]
    event_uri = NEWS["event/report_a"]

    graph.add((article_uri, RDF.type, NEWS.NewsArticle))
    graph.add((article_uri, RDF.type, SCHEMA.NewsArticle))
    graph.add((event_uri, RDF.type, NEWS.PolicyEvent))
    graph.add((event_uri, SCHEMA.name, Literal("Digital ID Rollout")))
    graph.add((event_uri, NEWS.reportedByArticle, article_uri))

    enriched = enrich_graph(graph)

    assert (article_uri, NEWS.reportsOn, event_uri) in enriched


def test_enrich_graph_matches_guardian_event_to_official_source_record():
    graph = build_ontology()

    guardian_publisher = NEWS["org/guardian"]
    parliament_publisher = NEWS["org/parliament"]
    guardian_article = NEWS["article/guardian_1"]
    parliament_article = NEWS["article/parliament_1"]
    event_uri = NEWS["event/afghan_review"]
    source_record = NEWS["source-record/parliament/afghan_review"]

    add_named_entity(
        graph,
        guardian_publisher,
        "The Guardian",
        (NEWS.NewsOrganisation, SCHEMA.Organization),
    )
    add_named_entity(
        graph,
        parliament_publisher,
        "UK Parliament",
        (NEWS.NewsOrganisation, SCHEMA.Organization),
    )

    graph.add((guardian_article, RDF.type, NEWS.NewsArticle))
    graph.add((guardian_article, RDF.type, SCHEMA.NewsArticle))
    graph.add(
        (guardian_article, SCHEMA.headline, Literal("Afghan Special Forces Relocation Review"))
    )
    graph.add((guardian_article, NEWS.publishedBy, guardian_publisher))

    graph.add((parliament_article, RDF.type, NEWS.NewsArticle))
    graph.add((parliament_article, RDF.type, SCHEMA.NewsArticle))
    graph.add(
        (parliament_article, SCHEMA.headline, Literal("Afghan Special Forces Relocation Review"))
    )
    graph.add((parliament_article, NEWS.publishedBy, parliament_publisher))
    graph.add(
        (
            parliament_article,
            NEWS.publishedDate,
            Literal("2026-03-26T10:00:00Z", datatype=XSD.dateTime),
        )
    )

    graph.add((source_record, RDF.type, NEWS.SourceRecord))
    graph.add((source_record, RDF.type, NEWS.OfficialSourceRecord))
    graph.add((source_record, RDF.type, NEWS.ParliamentSourceRecord))
    graph.add((source_record, NEWS.sourceSystem, Literal("parliament")))
    graph.add((source_record, NEWS.sourceTitle, Literal("Afghan Special Forces Relocation Review")))

    graph.add((event_uri, RDF.type, NEWS.PolicyEvent))
    graph.add((event_uri, RDF.type, NEWS.GovernmentPolicyEvent))
    graph.add((event_uri, SCHEMA.name, Literal("Afghan Special Forces Relocation Review")))
    graph.add((event_uri, NEWS.reportedByArticle, guardian_article))
    graph.add((event_uri, NEWS.occursOnDate, Literal("2026-03-26", datatype=XSD.date)))

    enriched = enrich_graph(graph)

    assert (event_uri, NEWS.matchedToSourceRecord, source_record) in enriched
    assert (event_uri, NEWS.representedInOfficialSource, source_record) in enriched


def test_enrich_graph_mirrors_existing_official_source_links_as_matches():
    graph = build_ontology()

    event_uri = NEWS["event/already_represented"]
    source_record = NEWS["source-record/parliament/already_represented"]

    graph.add((source_record, RDF.type, NEWS.SourceRecord))
    graph.add((source_record, RDF.type, NEWS.OfficialSourceRecord))
    graph.add((source_record, NEWS.sourceSystem, Literal("parliament")))
    graph.add((source_record, NEWS.sourceTitle, Literal("Already represented source")))

    graph.add((event_uri, RDF.type, NEWS.PolicyEvent))
    graph.add((event_uri, SCHEMA.name, Literal("Already represented source")))
    graph.add((event_uri, NEWS.representedInOfficialSource, source_record))

    enriched = enrich_graph(graph)

    assert (event_uri, NEWS.matchedToSourceRecord, source_record) in enriched
    assert (event_uri, NEWS.representedInOfficialSource, source_record) in enriched


def test_enrich_graph_avoids_weak_cross_source_match():
    graph = build_ontology()

    guardian_publisher = NEWS["org/guardian"]
    gov_publisher = NEWS["org/govuk"]
    guardian_article = NEWS["article/guardian_weak"]
    gov_article = NEWS["article/gov_weak"]
    event_uri = NEWS["event/weak_match"]
    source_record = NEWS["source-record/govuk/weak_match"]

    add_named_entity(
        graph,
        guardian_publisher,
        "The Guardian",
        (NEWS.NewsOrganisation, SCHEMA.Organization),
    )
    add_named_entity(
        graph,
        gov_publisher,
        "GOV.UK",
        (NEWS.NewsOrganisation, SCHEMA.Organization),
    )

    graph.add((guardian_article, RDF.type, NEWS.NewsArticle))
    graph.add((guardian_article, RDF.type, SCHEMA.NewsArticle))
    graph.add((guardian_article, SCHEMA.headline, Literal("Labour feud grows after reshuffle")))
    graph.add((guardian_article, NEWS.publishedBy, guardian_publisher))

    graph.add((gov_article, RDF.type, NEWS.NewsArticle))
    graph.add((gov_article, RDF.type, SCHEMA.NewsArticle))
    graph.add((gov_article, SCHEMA.headline, Literal("Building safety systems guidance update")))
    graph.add((gov_article, NEWS.publishedBy, gov_publisher))
    graph.add(
        (gov_article, NEWS.publishedDate, Literal("2026-03-28T09:00:00Z", datatype=XSD.dateTime))
    )

    graph.add((source_record, RDF.type, NEWS.SourceRecord))
    graph.add((source_record, RDF.type, NEWS.OfficialSourceRecord))
    graph.add((source_record, RDF.type, NEWS.GovernmentSourceRecord))
    graph.add((source_record, NEWS.sourceSystem, Literal("govuk")))
    graph.add((source_record, NEWS.sourceTitle, Literal("Building safety systems guidance update")))

    graph.add((event_uri, RDF.type, NEWS.PolicyEvent))
    graph.add((event_uri, SCHEMA.name, Literal("Labour leadership row")))
    graph.add((event_uri, NEWS.reportedByArticle, guardian_article))
    graph.add((event_uri, NEWS.occursOnDate, Literal("2026-03-28", datatype=XSD.date)))

    enriched = enrich_graph(graph)

    assert (event_uri, NEWS.matchedToSourceRecord, source_record) not in enriched
    assert (event_uri, NEWS.representedInOfficialSource, source_record) not in enriched


def test_enrich_graph_requires_strong_lexical_overlap_for_non_exact_match():
    graph = build_ontology()

    guardian_publisher = NEWS["org/guardian_overlap"]
    gov_publisher = NEWS["org/govuk_overlap"]
    guardian_article = NEWS["article/guardian_overlap"]
    gov_article = NEWS["article/gov_overlap"]
    event_uri = NEWS["event/overlap_match"]
    source_record = NEWS["source-record/govuk/overlap_match"]

    add_named_entity(
        graph,
        guardian_publisher,
        "The Guardian",
        (NEWS.NewsOrganisation, SCHEMA.Organization),
    )
    add_named_entity(
        graph,
        gov_publisher,
        "GOV.UK",
        (NEWS.NewsOrganisation, SCHEMA.Organization),
    )

    graph.add((guardian_article, RDF.type, NEWS.NewsArticle))
    graph.add((guardian_article, RDF.type, SCHEMA.NewsArticle))
    graph.add(
        (guardian_article, SCHEMA.headline, Literal("Housing update triggers local criticism"))
    )
    graph.add((guardian_article, NEWS.publishedBy, guardian_publisher))

    graph.add((gov_article, RDF.type, NEWS.NewsArticle))
    graph.add((gov_article, RDF.type, SCHEMA.NewsArticle))
    graph.add((gov_article, SCHEMA.headline, Literal("Housing reform package unveiled")))
    graph.add((gov_article, NEWS.publishedBy, gov_publisher))
    graph.add(
        (gov_article, NEWS.publishedDate, Literal("2026-03-28T09:00:00Z", datatype=XSD.dateTime))
    )

    graph.add((source_record, RDF.type, NEWS.SourceRecord))
    graph.add((source_record, RDF.type, NEWS.OfficialSourceRecord))
    graph.add((source_record, RDF.type, NEWS.GovernmentSourceRecord))
    graph.add((source_record, NEWS.sourceSystem, Literal("govuk")))
    graph.add((source_record, NEWS.sourceTitle, Literal("Housing reform package unveiled")))

    graph.add((event_uri, RDF.type, NEWS.PolicyEvent))
    graph.add((event_uri, SCHEMA.name, Literal("Housing update")))
    graph.add((event_uri, NEWS.reportedByArticle, guardian_article))
    graph.add((event_uri, NEWS.occursOnDate, Literal("2026-03-28", datatype=XSD.date)))

    enriched = enrich_graph(graph)

    assert (event_uri, NEWS.matchedToSourceRecord, source_record) not in enriched
    assert (event_uri, NEWS.representedInOfficialSource, source_record) not in enriched


def test_enrich_graph_does_not_add_legacy_completion_predicates():
    graph = build_ontology()
    article_uri = NEWS["article/clean_stage"]
    event_uri = NEWS["event/clean_stage"]

    graph.add((article_uri, RDF.type, NEWS.NewsArticle))
    graph.add((article_uri, RDF.type, SCHEMA.NewsArticle))
    graph.add((event_uri, RDF.type, NEWS.PolicyEvent))
    graph.add((event_uri, SCHEMA.name, Literal("Treasury Policy Update")))
    graph.add((event_uri, NEWS.reportedByArticle, article_uri))

    enriched = enrich_graph(graph)

    assert (article_uri, NEWS.hasSentiment, None) not in enriched
    assert (article_uri, NEWS.hasSection, None) not in enriched
    assert (article_uri, NEWS.hasTopic, None) not in enriched
    assert (article_uri, NEWS.hasFollowUp, None) not in enriched


def test_enrich_graph_rag_uses_canonical_typed_entity_uris(monkeypatch):
    graph = build_ontology()
    article_uri = NEWS["article/rag_entities"]
    event_uri = NEWS["event/rag_entities"]
    publisher_uri = NEWS["org/guardian_rag"]
    topic_uri = NEWS["topic/housing"]

    add_named_entity(
        graph,
        publisher_uri,
        "The Guardian",
        (NEWS.NewsOrganisation, SCHEMA.Organization),
    )

    graph.add((article_uri, RDF.type, NEWS.NewsArticle))
    graph.add((article_uri, RDF.type, SCHEMA.NewsArticle))
    graph.add(
        (
            article_uri,
            SCHEMA.headline,
            Literal("Keir Starmer presses Home Office on housing reform"),
        )
    )
    graph.add((article_uri, NEWS.publishedBy, publisher_uri))

    graph.add((topic_uri, RDF.type, NEWS.PolicyTopic))
    graph.add((topic_uri, SCHEMA.name, Literal("Housing")))

    graph.add((event_uri, RDF.type, NEWS.PolicyEvent))
    graph.add((event_uri, SCHEMA.name, Literal("Housing Reform Push")))
    graph.add((event_uri, NEWS.reportedByArticle, article_uri))
    graph.add((event_uri, NEWS.concernsPolicyTopic, topic_uri))

    monkeypatch.setattr(
        "src.complete_kg.load_cache_payload",
        lambda path: None,
    )
    monkeypatch.setattr("src.complete_kg.save_cache_payload", lambda path, payload: None)
    monkeypatch.setattr(
        "src.complete_kg.request_structured_output",
        lambda instructions, user_input, response_format: {
            "proposed_actors": ["Keir Starmer"],
            "proposed_departments": ["Home Office"],
            "proposed_topics": ["Housing"],
        },
    )

    enriched = enrich_graph(graph)

    actor_uri = person_uri("Keir Starmer")
    dept_uri = organisation_uri("Home Office")

    assert (event_uri, NEWS.involvesActor, actor_uri) in enriched
    assert (actor_uri, RDF.type, NEWS.PoliticalActor) in enriched
    assert (actor_uri, RDF.type, SCHEMA.Person) in enriched
    assert (actor_uri, SCHEMA.name, Literal("Keir Starmer")) in enriched

    assert (event_uri, NEWS.involvesGovernmentBody, dept_uri) in enriched
    assert (dept_uri, RDF.type, NEWS.GovernmentDepartment) in enriched
    assert (dept_uri, RDF.type, NEWS.GovernmentBody) in enriched
    assert (dept_uri, RDF.type, NEWS.OfficialBody) in enriched
    assert (dept_uri, SCHEMA.name, Literal("Home Office")) in enriched

    assert (event_uri, NEWS.involvesActor, NEWS["keir_starmer"]) not in enriched
    assert (event_uri, NEWS.involvesGovernmentBody, NEWS["home_office"]) not in enriched


def test_enrich_graph_rag_skips_party_names_returned_as_actors(monkeypatch):
    graph = build_ontology()
    article_uri = NEWS["article/rag_party"]
    event_uri = NEWS["event/rag_party"]
    publisher_uri = NEWS["org/guardian_party"]

    add_named_entity(
        graph,
        publisher_uri,
        "The Guardian",
        (NEWS.NewsOrganisation, SCHEMA.Organization),
    )

    graph.add((article_uri, RDF.type, NEWS.NewsArticle))
    graph.add((article_uri, RDF.type, SCHEMA.NewsArticle))
    graph.add((article_uri, SCHEMA.headline, Literal("Labour Party backs new housing pledge")))
    graph.add((article_uri, NEWS.publishedBy, publisher_uri))

    graph.add((event_uri, RDF.type, NEWS.PolicyEvent))
    graph.add((event_uri, SCHEMA.name, Literal("Housing Pledge")))
    graph.add((event_uri, NEWS.reportedByArticle, article_uri))

    monkeypatch.setattr("src.complete_kg.load_cache_payload", lambda path: None)
    monkeypatch.setattr("src.complete_kg.save_cache_payload", lambda path, payload: None)
    monkeypatch.setattr(
        "src.complete_kg.request_structured_output",
        lambda instructions, user_input, response_format: {
            "proposed_actors": ["Labour Party"],
            "proposed_departments": [],
            "proposed_topics": [],
        },
    )

    enriched = enrich_graph(graph)

    assert list(enriched.objects(event_uri, NEWS.involvesActor)) == []
    assert (person_uri("Labour Party"), RDF.type, NEWS.PoliticalActor) not in enriched


def test_enrich_graph_rag_skips_official_bodies_returned_as_actors(monkeypatch):
    graph = build_ontology()
    article_uri = NEWS["article/rag_body_actor"]
    event_uri = NEWS["event/rag_body_actor"]
    publisher_uri = NEWS["org/guardian_body_actor"]

    add_named_entity(
        graph,
        publisher_uri,
        "The Guardian",
        (NEWS.NewsOrganisation, SCHEMA.Organization),
    )

    graph.add((article_uri, RDF.type, NEWS.NewsArticle))
    graph.add((article_uri, RDF.type, SCHEMA.NewsArticle))
    graph.add(
        (
            article_uri,
            SCHEMA.headline,
            Literal("Welsh Government and Ministry of Justice strike deal"),
        )
    )
    graph.add((article_uri, NEWS.publishedBy, publisher_uri))

    graph.add((event_uri, RDF.type, NEWS.PolicyEvent))
    graph.add((event_uri, SCHEMA.name, Literal("Youth justice agreement")))
    graph.add((event_uri, NEWS.reportedByArticle, article_uri))

    monkeypatch.setattr("src.complete_kg.load_cache_payload", lambda path: None)
    monkeypatch.setattr("src.complete_kg.save_cache_payload", lambda path, payload: None)
    monkeypatch.setattr(
        "src.complete_kg.request_structured_output",
        lambda instructions, user_input, response_format: {
            "proposed_actors": ["Welsh Government"],
            "proposed_departments": ["Ministry of Justice"],
            "proposed_topics": [],
        },
    )

    enriched = enrich_graph(graph)

    assert list(enriched.objects(event_uri, NEWS.involvesActor)) == []
    assert (person_uri("Welsh Government"), None, None) not in enriched


def test_enrich_graph_rag_does_not_attach_parliamentary_body_as_government_body(monkeypatch):
    graph = build_ontology()
    article_uri = NEWS["article/rag_parliamentary_body"]
    event_uri = NEWS["event/rag_parliamentary_body"]
    publisher_uri = NEWS["org/guardian_parliamentary_body"]

    add_named_entity(
        graph,
        publisher_uri,
        "The Guardian",
        (NEWS.NewsOrganisation, SCHEMA.Organization),
    )

    graph.add((article_uri, RDF.type, NEWS.NewsArticle))
    graph.add((article_uri, RDF.type, SCHEMA.NewsArticle))
    graph.add((article_uri, SCHEMA.headline, Literal("House of Commons debate on housing reforms")))
    graph.add((article_uri, NEWS.publishedBy, publisher_uri))

    graph.add((event_uri, RDF.type, NEWS.PolicyEvent))
    graph.add((event_uri, SCHEMA.name, Literal("Housing Reform Debate")))
    graph.add((event_uri, NEWS.reportedByArticle, article_uri))

    monkeypatch.setattr("src.complete_kg.load_cache_payload", lambda path: None)
    monkeypatch.setattr("src.complete_kg.save_cache_payload", lambda path, payload: None)
    monkeypatch.setattr(
        "src.complete_kg.request_structured_output",
        lambda instructions, user_input, response_format: {
            "proposed_actors": [],
            "proposed_departments": ["House of Commons"],
            "proposed_topics": [],
        },
    )

    enriched = enrich_graph(graph)
    commons_uri = organisation_uri("House of Commons")

    assert (event_uri, NEWS.involvesGovernmentBody, commons_uri) not in enriched
    assert (commons_uri, None, None) not in enriched


def test_enrich_graph_writes_completion_audit_log(monkeypatch, tmp_path):
    graph = build_ontology()
    article_uri = NEWS["article/rag_audit"]
    event_uri = NEWS["event/rag_audit"]
    publisher_uri = NEWS["org/guardian_audit"]
    topic_uri = NEWS["topic/housing_audit"]
    audit_path = tmp_path / "completion_audit.json"

    add_named_entity(
        graph,
        publisher_uri,
        "The Guardian",
        (NEWS.NewsOrganisation, SCHEMA.Organization),
    )

    graph.add((article_uri, RDF.type, NEWS.NewsArticle))
    graph.add((article_uri, RDF.type, SCHEMA.NewsArticle))
    graph.add(
        (article_uri, SCHEMA.headline, Literal("Keir Starmer backs Home Office housing update"))
    )
    graph.add((article_uri, NEWS.publishedBy, publisher_uri))

    graph.add((topic_uri, RDF.type, NEWS.PolicyTopic))
    graph.add((topic_uri, SCHEMA.name, Literal("Housing")))

    graph.add((event_uri, RDF.type, NEWS.PolicyEvent))
    graph.add((event_uri, SCHEMA.name, Literal("Housing Update")))
    graph.add((event_uri, NEWS.reportedByArticle, article_uri))

    monkeypatch.setattr("src.complete_kg.load_cache_payload", lambda path: None)
    monkeypatch.setattr("src.complete_kg.save_cache_payload", lambda path, payload: None)
    monkeypatch.setattr(
        "src.complete_kg.request_structured_output",
        lambda instructions, user_input, response_format: {
            "proposed_actors": ["Keir Starmer"],
            "proposed_departments": ["Home Office"],
            "proposed_topics": ["Housing"],
        },
    )

    enrich_graph(graph, audit_log_path=audit_path)

    payload = json.loads(audit_path.read_text(encoding="utf-8"))
    entry = next(item for item in payload["entries"] if item["event_uri"] == str(event_uri))
    assert entry["rag_added_actors"] == [str(person_uri("Keir Starmer"))]
    assert entry["rag_added_departments"] == [str(organisation_uri("Home Office"))]
    assert entry["rag_added_topics"] == [str(topic_uri)]


def test_rag_does_not_add_extra_department_when_event_already_has_one(monkeypatch):
    graph = build_ontology()
    article_uri = NEWS["article/existing_department"]
    event_uri = NEWS["event/existing_department"]
    publisher_uri = NEWS["org/guardian_existing_department"]
    existing_department = organisation_uri("Home Office")

    add_named_entity(
        graph,
        publisher_uri,
        "The Guardian",
        (NEWS.NewsOrganisation, SCHEMA.Organization),
    )
    add_named_entity(
        graph,
        existing_department,
        "Home Office",
        (NEWS.OfficialBody, NEWS.GovernmentBody, NEWS.GovernmentDepartment),
    )

    graph.add((article_uri, RDF.type, NEWS.NewsArticle))
    graph.add((article_uri, RDF.type, SCHEMA.NewsArticle))
    graph.add(
        (
            article_uri,
            SCHEMA.headline,
            Literal("Hyper-targeted scheme to help at-risk schools in England tackle knife crime"),
        )
    )
    graph.add((article_uri, NEWS.publishedBy, publisher_uri))

    graph.add((event_uri, RDF.type, NEWS.PolicyEvent))
    graph.add((event_uri, RDF.type, NEWS.GovernmentPolicyEvent))
    graph.add(
        (
            event_uri,
            SCHEMA.name,
            Literal("Launch of hyper-targeted programme to tackle knife crime in schools"),
        )
    )
    graph.add((event_uri, NEWS.reportedByArticle, article_uri))
    graph.add((event_uri, NEWS.involvesGovernmentBody, existing_department))

    monkeypatch.setattr("src.complete_kg.load_cache_payload", lambda path: None)
    monkeypatch.setattr("src.complete_kg.save_cache_payload", lambda path, payload: None)
    monkeypatch.setattr(
        "src.complete_kg.request_structured_output",
        lambda instructions, user_input, response_format: {
            "proposed_actors": [],
            "proposed_departments": ["Department for Education"],
            "proposed_topics": [],
        },
    )

    enriched = enrich_graph(graph)

    dfe = organisation_uri("Department for Education")
    assert (event_uri, NEWS.involvesGovernmentBody, existing_department) in enriched
    assert (event_uri, NEWS.involvesGovernmentBody, dfe) not in enriched
