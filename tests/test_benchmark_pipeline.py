from src.benchmark_pipeline import _extract_output_summary


def test_extract_output_summary_has_expected_keys():
    summary = _extract_output_summary()

    assert set(summary) == {"query_coverage", "validation", "graph", "extraction"}
    assert "answered_queries" in summary["query_coverage"]
    assert "rule_count" in summary["validation"]
    assert "triple_count" in summary["graph"]
    assert "record_count" in summary["extraction"]
