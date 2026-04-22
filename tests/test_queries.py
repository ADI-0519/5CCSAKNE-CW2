"""Tests for SPARQL competency-query execution."""

import json
from pathlib import Path

from rdflib import RDF, Literal
from rdflib.namespace import XSD

from src.build_ontology import build_ontology
from src.data_extraction import extract_relevant_information
from src.data_normalisation import normalise_data
from src.json_to_rdf import NEWS, SCHEMA, convert_json_to_rdf
from src.run_queries import execute_queries, load_query_definitions, save_results

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "sample_response.json"


def build_fixture_graph():
    raw_data = json.loads(FIXTURE_PATH.read_text())
    rdf_graph = convert_json_to_rdf(normalise_data(extract_relevant_information(raw_data)))
    graph = build_ontology()
    for triple in rdf_graph:
        graph.add(triple)
    return graph


def test_load_query_definitions_reads_all_20_queries():
    definitions = load_query_definitions()
    assert len(definitions) == 20
    assert definitions[0].query_id == "CQ01"
    assert definitions[-1].query_id == "CQ20"


def test_query_definitions_include_prefixes():
    definitions = load_query_definitions()
    assert definitions[0].query_text.startswith("PREFIX news:")
    assert "SELECT" in definitions[0].query_text


def test_execute_queries_runs_against_fixture_graph():
    graph = build_fixture_graph()
    definitions = load_query_definitions()
    results = execute_queries(graph, definitions)

    assert len(results) == 20
    assert all("query_id" in result for result in results)
    assert all("row_count" in result for result in results)
    assert all(isinstance(result["row_count"], int) for result in results)
    assert all("rows" in result for result in results)
    assert all("variables" in result for result in results)


def test_query_execution_is_stable_against_fixture_graph():
    graph = build_fixture_graph()
    definitions = load_query_definitions()
    results = execute_queries(graph, definitions)
    results_again = execute_queries(graph, definitions)

    first_counts = {result["query_id"]: result["row_count"] for result in results}
    second_counts = {result["query_id"]: result["row_count"] for result in results_again}

    assert first_counts == second_counts


def test_save_results_writes_json(tmp_path):
    graph = build_fixture_graph()
    definitions = load_query_definitions()
    results = execute_queries(graph, definitions)
    output_file = tmp_path / "results.json"

    save_results(results, output_file)

    assert output_file.exists()
    loaded = json.loads(output_file.read_text())
    assert len(loaded) == 20


def test_execute_queries_normalises_and_deduplicates_identical_rows():
    graph = build_ontology()
    event = NEWS["event/test-statement"]
    department = NEWS["organisation/HM_Treasury"]
    duplicate_department = NEWS["organisation/HM_Treasury_Duplicate"]
    graph.add((event, NEWS.issuedByDepartment, department))
    graph.add((event, NEWS.issuedByDepartment, duplicate_department))
    graph.add(
        (
            event,
            SCHEMA.name,
            Literal("Joint Statement: EU-UK Financial Regulatory Forum, March 2026"),
        )
    )
    graph.add((event, NEWS.occursOnDate, Literal("2026-03-12")))
    graph.add((department, SCHEMA.name, Literal("  HM Treasury  ")))
    graph.add((duplicate_department, SCHEMA.name, Literal("HM Treasury")))

    definitions = [
        type(
            "QD",
            (),
            {
                "query_id": "CQ02",
                "title": "test",
                "query_text": """
PREFIX news: <http://example.org/news#>
PREFIX schema: <https://schema.org/>
SELECT ?statementName ?departmentName ?eventDate
WHERE {
  ?event news:issuedByDepartment ?department ;
         schema:name ?statementName ;
         news:occursOnDate ?eventDate .
  ?department schema:name ?departmentName .
}
""".strip(),
            },
        )()
    ]

    results = execute_queries(graph, definitions)

    assert results[0]["row_count"] == 1
    assert results[0]["rows"] == [
        {
            "statementName": "Joint Statement: EU-UK Financial Regulatory Forum, March 2026",
            "departmentName": "HM Treasury",
            "eventDate": "2026-03-12",
        }
    ]


def test_cq17_only_returns_articles_backed_by_matched_source_records():
    graph = build_ontology()
    journalist = NEWS["person/Test_Journalist"]
    article = NEWS["article/test-article"]
    unmatched_event = NEWS["event/unmatched"]
    matched_event = NEWS["event/matched"]
    department = NEWS["organisation/HM_Treasury"]
    source_record = NEWS["source-record/govuk/test"]

    graph.add((journalist, RDF.type, NEWS.Journalist))
    graph.add((journalist, SCHEMA.name, Literal("Test Journalist")))
    graph.add((article, RDF.type, NEWS.NewsArticle))
    graph.add((article, NEWS.hasAuthor, journalist))
    graph.add((article, SCHEMA.headline, Literal("Treasury policy analysis")))
    graph.add((department, RDF.type, NEWS.GovernmentDepartment))
    graph.add((department, SCHEMA.name, Literal("HM Treasury")))
    graph.add((source_record, RDF.type, NEWS.SourceRecord))
    graph.add((source_record, RDF.type, NEWS.OfficialSourceRecord))

    for event in (unmatched_event, matched_event):
        graph.add((event, RDF.type, NEWS.PolicyEvent))
        graph.add((event, RDF.type, NEWS.GovernmentPolicyEvent))
        graph.add((event, NEWS.reportedByArticle, article))
        graph.add((event, NEWS.involvesGovernmentBody, department))
        graph.add((event, NEWS.occursOnDate, Literal("2026-03-12", datatype=XSD.date)))

    graph.add((matched_event, NEWS.matchedToSourceRecord, source_record))

    cq17 = next(
        definition for definition in load_query_definitions() if definition.query_id == "CQ17"
    )
    results = execute_queries(graph, [cq17])

    assert results[0]["row_count"] == 1
    assert results[0]["rows"] == [
        {
            "journalistName": "Test Journalist",
            "headline": "Treasury policy analysis",
            "departmentName": "HM Treasury",
        }
    ]
