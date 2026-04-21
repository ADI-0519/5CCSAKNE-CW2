import argparse
import json
from collections import Counter
from pathlib import Path

from rdflib import RDF, Graph

from src.build_ontology import NEWS
from src.run_queries import load_kg

DEFAULT_KG_PATH = Path("kg/generated/completed_kg.ttl")
DEFAULT_KG_RECORDS_PATH = Path("data/processed/kg_records.json")
DEFAULT_VALIDATION_RESULTS_PATH = Path("output/validation_results.json")
DEFAULT_OUTPUT_PATH = Path("output/kg_summary.json")


def ratio(count, total):
    if not total:
        return 0.0
    return round((count / total) * 100, 2)


def load_json(path):
    file_path = Path(path)
    if not file_path.exists():
        return None
    return json.loads(file_path.read_text(encoding="utf-8"))


def count_subjects(graph: Graph, rdf_type):
    return len(set(graph.subjects(RDF.type, rdf_type)))


def count_events_with_predicate(graph: Graph, predicate, rdf_type=NEWS.PolicyEvent):
    events = set(graph.subjects(RDF.type, rdf_type))
    return sum(1 for event in events if next(graph.objects(event, predicate), None) is not None)


def build_graph_summary(graph: Graph):
    policy_events = set(graph.subjects(RDF.type, NEWS.PolicyEvent))
    policy_event_count = len(policy_events)
    return {
        "triple_count": len(graph),
        "policy_event_count": policy_event_count,
        "parliamentary_event_count": count_subjects(graph, NEWS.ParliamentaryEvent),
        "government_policy_event_count": count_subjects(graph, NEWS.GovernmentPolicyEvent),
        "parliamentary_debate_count": count_subjects(graph, NEWS.ParliamentaryDebate),
        "ministerial_statement_count": count_subjects(graph, NEWS.MinisterialStatement),
        "events_with_date_count": count_events_with_predicate(graph, NEWS.occursOnDate),
        "events_with_topic_count": count_events_with_predicate(graph, NEWS.concernsPolicyTopic),
        "events_with_government_body_count": count_events_with_predicate(
            graph, NEWS.involvesGovernmentBody
        ),
        "parliamentary_events_with_body_count": count_events_with_predicate(
            graph, NEWS.occursInParliamentaryBody, NEWS.ParliamentaryEvent
        ),
        "events_linked_to_official_source_count": count_events_with_predicate(
            graph, NEWS.representedInOfficialSource
        ),
        "coverage_percentages": {
            "with_date": ratio(
                count_events_with_predicate(graph, NEWS.occursOnDate), policy_event_count
            ),
            "with_topic": ratio(
                count_events_with_predicate(graph, NEWS.concernsPolicyTopic), policy_event_count
            ),
            "with_government_body": ratio(
                count_events_with_predicate(graph, NEWS.involvesGovernmentBody), policy_event_count
            ),
            "linked_to_official_source": ratio(
                count_events_with_predicate(graph, NEWS.representedInOfficialSource),
                policy_event_count,
            ),
        },
    }


def build_extraction_summary(kg_records):
    if not kg_records:
        return {}

    confidence_counts = Counter()
    extraction_method_counts = Counter()
    generic_fallback_name_counts = Counter()
    generic_fallback_event_count = 0
    records_with_generic_fallback = 0
    event_count = 0

    for record in kg_records:
        events = record.get("event_candidates", [])
        event_count += len(events)
        record_has_generic_fallback = False
        for event in events:
            confidence_counts[
                str(event.get("confidence") or "unknown").strip().lower() or "unknown"
            ] += 1
            extraction_method_counts[
                str(event.get("extraction_method") or "unknown").strip().lower() or "unknown"
            ] += 1
            if event.get("is_generic_fallback"):
                generic_fallback_event_count += 1
                record_has_generic_fallback = True
                generic_fallback_name_counts[event.get("name") or "Unknown"] += 1
        if record_has_generic_fallback:
            records_with_generic_fallback += 1

    return {
        "record_count": len(kg_records),
        "event_count": event_count,
        "generic_fallback_event_count": generic_fallback_event_count,
        "records_with_generic_fallback": records_with_generic_fallback,
        "generic_fallback_name_counts": dict(sorted(generic_fallback_name_counts.items())),
        "confidence_counts": dict(sorted(confidence_counts.items())),
        "extraction_method_counts": dict(sorted(extraction_method_counts.items())),
    }


def build_summary(graph: Graph, kg_records=None, validation_report=None):
    summary = {"graph": build_graph_summary(graph)}
    if kg_records is not None:
        summary["extraction"] = build_extraction_summary(kg_records)
    if validation_report is not None:
        summary["validation"] = {
            "rule_count": validation_report.get("rule_count", 0),
            "failed_rule_count": validation_report.get("failed_rule_count", 0),
            "total_violations": validation_report.get("total_violations", 0),
            "severity_totals": validation_report.get("severity_totals", {}),
        }
    return summary


def save_summary(summary, output_path=DEFAULT_OUTPUT_PATH):
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Save headline KG summary metrics.")
    parser.add_argument("--kg", type=Path, default=DEFAULT_KG_PATH)
    parser.add_argument("--kg-records", type=Path, default=DEFAULT_KG_RECORDS_PATH)
    parser.add_argument("--validation", type=Path, default=DEFAULT_VALIDATION_RESULTS_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    args = parser.parse_args()

    graph = load_kg(args.kg)
    kg_records = load_json(args.kg_records)
    validation_report = load_json(args.validation)
    summary = build_summary(graph, kg_records, validation_report)
    save_summary(summary, args.output)

    print(f"[SUMMARY] KG: {args.kg}")
    print(f"[SUMMARY] Policy events: {summary['graph']['policy_event_count']}")
    print(
        f"[SUMMARY] Validation failures: {summary.get('validation', {}).get('failed_rule_count', 0)}"
    )


if __name__ == "__main__":
    main()
