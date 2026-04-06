"""Tests for SPARQL competency-query execution."""

import json
from pathlib import Path

from src.build_ontology import build_ontology
from src.data_extraction import extract_relevant_information
from src.data_normalisation import normalise_data
from src.json_to_rdf import convert_json_to_rdf
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
