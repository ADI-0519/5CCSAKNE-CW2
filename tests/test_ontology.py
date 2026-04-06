"""Unit tests for ontology modelling choices."""

from rdflib.namespace import RDF, RDFS

from src.build_ontology import NEWS, SCHEMA, build_ontology


def test_ontology_defines_organisation_and_technology_classes():
    graph = build_ontology()
    assert (NEWS.Organisation, RDF.type, RDFS.Class) in graph
    assert (NEWS.Organisation, RDFS.subClassOf, SCHEMA.Organization) in graph
    assert (NEWS.Technology, RDF.type, RDFS.Class) in graph


def test_ontology_defines_article_mention_properties():
    graph = build_ontology()
    assert (NEWS.mentionsOrganisation, RDF.type, RDF.Property) in graph
    assert (NEWS.mentionsTechnology, RDF.type, RDF.Property) in graph
    assert (NEWS.hasTopic, RDF.type, RDF.Property) in graph


def test_ontology_defines_modelling_support_properties():
    graph = build_ontology()
    assert (NEWS.usesTechnology, RDF.type, RDF.Property) in graph
    assert (NEWS.publishedBy, RDF.type, RDF.Property) in graph
    assert (NEWS.hasAuthor, RDF.type, RDF.Property) in graph
