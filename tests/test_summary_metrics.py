from rdflib import Graph, Literal
from rdflib.namespace import RDF

from src.summarise_kg import build_summary
from src.validate_graph import NEWS


def test_build_summary_reports_graph_extraction_and_validation_metrics():
    graph = Graph()
    event = NEWS["event/e1"]
    article = NEWS["article/a1"]
    topic = NEWS["topic/t1"]
    department = NEWS["organisation/d1"]

    graph.add((event, RDF.type, NEWS.PolicyEvent))
    graph.add((event, RDF.type, NEWS.GovernmentPolicyEvent))
    graph.add((event, NEWS.occursOnDate, Literal("2026-03-12")))
    graph.add((event, NEWS.reportedByArticle, article))
    graph.add((event, NEWS.concernsPolicyTopic, topic))
    graph.add((event, NEWS.involvesGovernmentBody, department))

    kg_records = [
        {
            "event_candidates": [
                {
                    "name": "Policy Announcement",
                    "confidence": "low",
                    "extraction_method": "heuristic",
                    "is_generic_fallback": True,
                }
            ]
        }
    ]
    validation_report = {
        "rule_count": 17,
        "failed_rule_count": 2,
        "total_violations": 3,
        "severity_totals": {"warning": 2, "error": 1},
    }

    summary = build_summary(graph, kg_records, validation_report)

    assert summary["graph"]["policy_event_count"] == 1
    assert summary["graph"]["government_policy_event_count"] == 1
    assert summary["graph"]["coverage_percentages"]["with_date"] == 100.0
    assert summary["extraction"]["generic_fallback_event_count"] == 1
    assert summary["extraction"]["confidence_counts"] == {"low": 1}
    assert summary["validation"]["rule_count"] == 17
    assert summary["validation"]["failed_rule_count"] == 2
