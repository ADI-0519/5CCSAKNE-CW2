from rdflib import Graph, Literal
from rdflib.namespace import RDF

from src.validate_graph import NEWS, SCHEMA, execute_validation, load_validation_rules


def build_valid_graph():
    graph = Graph()

    event = NEWS["event/statement"]
    article = NEWS["article/a1"]
    record = NEWS["source-record/r1"]
    actor = NEWS["person/actor1"]
    party = NEWS["organisation/party1"]
    department = NEWS["organisation/dept1"]
    topic = NEWS["topic/topic1"]

    graph.add((event, RDF.type, NEWS.PolicyEvent))
    graph.add((event, RDF.type, NEWS.MinisterialStatement))
    graph.add((event, SCHEMA.name, Literal("Ministerial Statement on Housing")))
    graph.add((event, NEWS.occursOnDate, Literal("2026-03-12")))
    graph.add((event, NEWS.issuedByDepartment, department))
    graph.add((event, NEWS.involvesGovernmentBody, department))
    graph.add((event, NEWS.concernsPolicyTopic, topic))
    graph.add((event, NEWS.reportedByArticle, article))
    graph.add((event, NEWS.representedInOfficialSource, record))
    graph.add((event, NEWS.matchedToSourceRecord, record))

    graph.add((article, RDF.type, NEWS.NewsArticle))
    graph.add((record, RDF.type, NEWS.SourceRecord))
    graph.add((record, RDF.type, NEWS.OfficialSourceRecord))
    graph.add((record, NEWS.sourceSystem, Literal("govuk")))
    graph.add((record, NEWS.sourceTitle, Literal("Housing statement")))

    graph.add((actor, RDF.type, NEWS.PoliticalActor))
    graph.add((party, RDF.type, NEWS.PoliticalParty))
    graph.add((actor, NEWS.memberOfParty, party))

    debate = NEWS["event/debate"]
    graph.add((debate, RDF.type, NEWS.PolicyEvent))
    graph.add((debate, RDF.type, NEWS.ParliamentaryDebate))
    graph.add((debate, NEWS.occursOnDate, Literal("2026-03-13")))
    graph.add((debate, NEWS.concernsPolicyTopic, topic))

    return graph


def test_validation_rules_pass_on_conforming_graph():
    report = execute_validation(build_valid_graph(), load_validation_rules())

    assert report["failed_rule_count"] == 0
    assert report["total_violations"] == 0
    assert all(result["passed"] for result in report["results"])


def test_validation_rules_flag_expected_violations():
    graph = Graph()
    event = NEWS["event/bad"]
    article = NEWS["article/not-typed"]
    actor = NEWS["person/not-typed"]
    party = NEWS["organisation/not-party"]
    record = NEWS["source-record/missing-meta"]
    bad_target = NEWS["source-record/not-official"]
    bad_match_target = NEWS["target/not-source-record"]
    bad_subject = NEWS["not-an-event"]
    department = NEWS["organisation/dept-without-body-link"]

    graph.add((event, RDF.type, NEWS.PolicyEvent))
    graph.add((event, RDF.type, NEWS.MinisterialStatement))
    graph.add((event, RDF.type, NEWS.ParliamentaryDebate))
    graph.add((event, NEWS.reportedByArticle, article))
    graph.add((bad_subject, NEWS.reportedByArticle, article))
    graph.add((event, NEWS.representedInOfficialSource, bad_target))
    graph.add((event, NEWS.matchedToSourceRecord, bad_match_target))
    graph.add((event, NEWS.issuedByDepartment, department))
    graph.add((actor, NEWS.memberOfParty, party))
    graph.add((record, RDF.type, NEWS.OfficialSourceRecord))
    graph.add((bad_target, RDF.type, NEWS.SourceRecord))

    report = execute_validation(graph, load_validation_rules())
    violations = {result["rule_id"]: result["violation_count"] for result in report["results"]}

    assert violations["V01"] == 0
    assert violations["V02"] == 1
    assert violations["V03"] == 1
    assert violations["V04"] == 1
    assert violations["V05"] == 2
    assert violations["V06"] == 1
    assert violations["V07"] == 1
    assert violations["V08"] == 1
    assert violations["V09"] == 1
    assert violations["V10"] == 1
    assert violations["V11"] == 1
    assert violations["V12"] == 1
