from rdflib.namespace import OWL, RDF, RDFS

from src.build_ontology import CORE, NEWS, SCHEMA, build_ontology


def test_ontology_defines_people_and_institution_classes():
    graph = build_ontology()
    assert (NEWS.PoliticalActor, RDF.type, OWL.Class) in graph
    assert (NEWS.PoliticalActor, RDFS.subClassOf, SCHEMA.Person) in graph
    assert (NEWS.PoliticalParty, RDF.type, OWL.Class) in graph
    assert (NEWS.GovernmentBody, RDF.type, OWL.Class) in graph
    assert (NEWS.GovernmentDepartment, RDFS.subClassOf, NEWS.GovernmentBody) in graph
    assert (NEWS.ParliamentaryBody, RDFS.subClassOf, NEWS.GovernmentBody) in graph


def test_ontology_defines_event_and_topic_classes():
    graph = build_ontology()
    assert (NEWS.PolicyEvent, RDF.type, OWL.Class) in graph
    assert (NEWS.ParliamentaryEvent, RDFS.subClassOf, NEWS.PolicyEvent) in graph
    assert (NEWS.GovernmentPolicyEvent, RDFS.subClassOf, NEWS.PolicyEvent) in graph
    assert (NEWS.ParliamentaryDebate, RDFS.subClassOf, NEWS.ParliamentaryEvent) in graph
    assert (NEWS.MinisterialStatement, RDFS.subClassOf, NEWS.GovernmentPolicyEvent) in graph
    assert (NEWS.PolicyTopic, RDF.type, OWL.Class) in graph
    assert (NEWS.Location, RDFS.subClassOf, CORE.Place) in graph


def test_ontology_defines_reporting_and_provenance_classes():
    graph = build_ontology()
    assert (NEWS.NewsArticle, RDF.type, OWL.Class) in graph
    assert (NEWS.NewsArticle, RDFS.subClassOf, SCHEMA.NewsArticle) in graph
    assert (NEWS.NewsOrganisation, RDF.type, OWL.Class) in graph
    assert (NEWS.Journalist, RDF.type, OWL.Class) in graph
    assert (NEWS.SourceRecord, RDF.type, OWL.Class) in graph
    assert (NEWS.OfficialSourceRecord, RDFS.subClassOf, NEWS.SourceRecord) in graph
    assert (NEWS.ParliamentSourceRecord, RDFS.subClassOf, NEWS.OfficialSourceRecord) in graph
    assert (NEWS.GovernmentSourceRecord, RDFS.subClassOf, NEWS.OfficialSourceRecord) in graph


def test_ontology_defines_core_event_properties():
    graph = build_ontology()
    for property_uri in (
        NEWS.concernsPolicyTopic,
        NEWS.involvesActor,
        NEWS.involvesGovernmentBody,
        NEWS.issuedByDepartment,
        NEWS.occursInParliamentaryBody,
        NEWS.occursInLocation,
        NEWS.memberOfParty,
    ):
        assert (property_uri, RDF.type, OWL.ObjectProperty) in graph


def test_ontology_defines_reporting_and_alignment_properties():
    graph = build_ontology()
    for property_uri in (
        NEWS.reportedByArticle,
        NEWS.publishedBy,
        NEWS.hasAuthor,
        NEWS.representedInOfficialSource,
        NEWS.matchedToSourceRecord,
    ):
        assert (property_uri, RDF.type, OWL.ObjectProperty) in graph
