"""Tests for ontology-aligned KG completion/enrichment."""

from rdflib import RDF, Literal
from rdflib.namespace import XSD

from src.build_ontology import NEWS, SCHEMA, build_ontology
from src.complete_kg import enrich_graph


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
