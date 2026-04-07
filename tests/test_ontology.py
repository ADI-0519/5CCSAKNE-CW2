"""Unit tests for ontology modelling choices."""

from rdflib.namespace import RDF, RDFS

from src.build_ontology import NEWS, SCHEMA, build_ontology


def test_ontology_defines_people_and_organisation_classes():
    graph = build_ontology()
    assert (NEWS.Organisation, RDF.type, RDFS.Class) in graph
    assert (NEWS.Organisation, RDFS.subClassOf, SCHEMA.Organization) in graph
    assert (NEWS.Politician, RDF.type, RDFS.Class) in graph
    assert (NEWS.Politician, RDFS.subClassOf, SCHEMA.Person) in graph
    assert (NEWS.PoliticalParty, RDF.type, RDFS.Class) in graph


def test_ontology_defines_article_mention_properties():
    graph = build_ontology()
    assert (NEWS.mentionsOrganisation, RDF.type, RDF.Property) in graph
    assert (NEWS.mentionsPerson, RDF.type, RDF.Property) in graph
    assert (NEWS.mentionsLocation, RDF.type, RDF.Property) in graph
    assert (NEWS.hasTopic, RDF.type, RDF.Property) in graph


def test_ontology_defines_event_and_analysis_properties():
    graph = build_ontology()
    assert (NEWS.publishedBy, RDF.type, RDF.Property) in graph
    assert (NEWS.hasAuthor, RDF.type, RDF.Property) in graph
    assert (NEWS.coversEvent, RDF.type, RDF.Property) in graph
    assert (NEWS.hasSentiment, RDF.type, RDF.Property) in graph
