import argparse
import json
from collections import defaultdict
from pathlib import Path

from src.data_normalisation import canonicalise_date, normalise_name

PROCESSED_DIR = Path("data/processed")
DEFAULT_GOLD_STANDARD_PATH = Path("data/evaluation/gold_standard_extraction.json")
DEFAULT_JSON_OUTPUT_PATH = Path("output/extraction_evaluation.json")
DEFAULT_MD_OUTPUT_PATH = Path("docs/extraction_evaluation.md")
SOURCE_SYSTEM_ORDER = {"guardian": 0, "parliament": 1, "govuk": 2}


def find_most_recent(pattern, base_dir=PROCESSED_DIR):
    matches = sorted(base_dir.glob(pattern))
    if matches:
        return matches[-1]
    return None


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def save_json(path, payload):
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


def normalize_scalar(value, *, is_date=False):
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    text = normalise_name(value)
    if not text:
        return None
    if is_date:
        try:
            return canonicalise_date(text)
        except ValueError:
            return text
    return text


def normalize_list(values, *, is_date=False):
    cleaned = []
    seen = set()
    for value in values or []:
        normalized = normalize_scalar(value, is_date=is_date)
        if normalized in (None, ""):
            continue
        if normalized not in seen:
            seen.add(normalized)
            cleaned.append(normalized)
    return sorted(cleaned)


def project_event(event):
    name = normalize_scalar(event.get("name"))
    if not name:
        return None
    return {
        "name": name,
        "type": normalize_scalar(event.get("type")),
        "date": normalize_scalar(event.get("date"), is_date=True),
        "location": normalize_scalar(event.get("location")),
        "policy_topics": normalize_list(event.get("policy_topics")),
        "political_actors": normalize_list(event.get("political_actors")),
        "government_bodies": normalize_list(event.get("government_bodies")),
        "parliamentary_body": normalize_scalar(event.get("parliamentary_body")),
        "political_parties": normalize_list(event.get("political_parties")),
        "confidence": normalize_scalar(event.get("confidence")),
        "extraction_method": normalize_scalar(event.get("extraction_method")),
        "is_generic_fallback": bool(event.get("is_generic_fallback")),
    }


def project_record(record):
    entities = record.get("entities", {})
    events = []
    for event in record.get("event_candidates", []):
        projected = project_event(event)
        if projected is not None:
            events.append(projected)
    events.sort(key=lambda item: item["name"])

    return {
        "metadata": {
            "source_system": normalize_scalar(record.get("source_system")),
            "source_name": normalize_scalar(record.get("source_name")),
            "title": normalize_scalar(record.get("title")),
            "url": normalize_scalar(record.get("url")),
            "published_at": normalize_scalar(record.get("published_at"), is_date=True),
            "author": normalize_scalar(record.get("author")),
            "article_type": normalize_scalar(record.get("article_type")),
        },
        "topics": normalize_list(entities.get("topics")),
        "politicians": normalize_list(entities.get("politicians")),
        "political_parties": normalize_list(entities.get("political_parties")),
        "government_bodies": normalize_list(entities.get("government_bodies")),
        "locations": normalize_list(entities.get("locations")),
        "events": events,
    }


def build_record_index(records):
    return {str(record.get("id")): record for record in records if record.get("id")}


def select_template_records(records, *, ids=None, per_source=0, limit=0):
    indexed = build_record_index(records)
    if ids:
        return [indexed[record_id] for record_id in ids if record_id in indexed]

    ordered = sorted(
        records,
        key=lambda record: (
            SOURCE_SYSTEM_ORDER.get(normalize_scalar(record.get("source_system")) or "", 99),
            normalize_scalar(record.get("source_system")) or "",
            normalize_scalar(record.get("published_at")) or "",
            normalize_scalar(record.get("title")) or "",
            str(record.get("id") or ""),
        ),
    )

    if per_source > 0:
        selected = []
        counts = defaultdict(int)
        for record in ordered:
            source_system = normalize_scalar(record.get("source_system")) or "unknown"
            if counts[source_system] >= per_source:
                continue
            selected.append(record)
            counts[source_system] += 1
        return selected

    if limit > 0:
        return ordered[:limit]
    return ordered


def build_gold_template(records, prediction_path):
    samples = []
    for record in records:
        projection = project_record(record)
        samples.append(
            {
                "record_id": str(record.get("id")),
                "source_system": projection["metadata"]["source_system"],
                "title": projection["metadata"]["title"],
                "url": projection["metadata"]["url"],
                "notes": "",
                "gold": projection,
                "prediction_snapshot": projection,
            }
        )
    return {
        "schema_version": 1,
        "prediction_input": Path(prediction_path).as_posix(),
        "instructions": (
            "Edit each sample.gold block so it reflects the manually judged correct extraction. "
            "Leave prediction_snapshot untouched as the original machine output reference."
        ),
        "samples": samples,
    }


def prf_from_counts(tp, fp, fn):
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if precision + recall else 0.0
    return {
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
    }


def compare_sets(predicted_values, gold_values):
    predicted = set(predicted_values or [])
    gold = set(gold_values or [])
    tp = len(predicted & gold)
    fp = len(predicted - gold)
    fn = len(gold - predicted)
    return tp, fp, fn


def metric_bucket():
    return {"tp": 0, "fp": 0, "fn": 0}


def add_metric_counts(bucket, tp, fp, fn):
    bucket["tp"] += tp
    bucket["fp"] += fp
    bucket["fn"] += fn


def summarize_metric_bucket(bucket):
    return prf_from_counts(bucket["tp"], bucket["fp"], bucket["fn"])


def event_map(events):
    mapping = {}
    for event in events or []:
        name = normalize_scalar(event.get("name"))
        if not name:
            continue
        mapping[name] = project_event(event)
    return mapping


def compare_event_types(predicted_events, gold_events):
    counts = metric_bucket()
    all_names = set(predicted_events) | set(gold_events)
    for name in all_names:
        predicted = predicted_events.get(name)
        gold = gold_events.get(name)
        if predicted is None:
            add_metric_counts(counts, 0, 0, 1)
            continue
        if gold is None:
            add_metric_counts(counts, 0, 1, 0)
            continue
        if predicted.get("type") == gold.get("type"):
            add_metric_counts(counts, 1, 0, 0)
        else:
            add_metric_counts(counts, 0, 1, 1)
    return counts


def compare_event_field_sets(predicted_events, gold_events, field_name):
    counts = metric_bucket()
    all_names = set(predicted_events) | set(gold_events)
    for name in all_names:
        predicted = predicted_events.get(name) or {}
        gold = gold_events.get(name) or {}

        predicted_values = predicted.get(field_name) or []
        gold_values = gold.get(field_name) or []
        if field_name == "government_bodies":
            parliamentary_body = predicted.get("parliamentary_body")
            if parliamentary_body:
                predicted_values = list(predicted_values) + [parliamentary_body]
            gold_parliamentary_body = gold.get("parliamentary_body")
            if gold_parliamentary_body:
                gold_values = list(gold_values) + [gold_parliamentary_body]

        tp, fp, fn = compare_sets(predicted_values, gold_values)
        add_metric_counts(counts, tp, fp, fn)
    return counts


def evaluate_samples(prediction_records, gold_standard):
    prediction_index = build_record_index(prediction_records)
    overall_metrics = {
        "event_name": metric_bucket(),
        "record_topics": metric_bucket(),
        "record_government_bodies": metric_bucket(),
        "record_locations": metric_bucket(),
        "event_type": metric_bucket(),
        "event_topics": metric_bucket(),
        "institution_links": metric_bucket(),
        "political_actors": metric_bucket(),
        "political_parties": metric_bucket(),
    }
    metadata_totals = {"correct": 0, "total": 0}
    by_source = {}
    sample_reports = []

    for sample in gold_standard.get("samples", []):
        record_id = str(sample.get("record_id") or "")
        gold = sample.get("gold") or {}
        prediction_record = prediction_index.get(record_id)
        if prediction_record is None:
            sample_reports.append(
                {
                    "record_id": record_id,
                    "source_system": sample.get("source_system"),
                    "status": "missing_prediction",
                }
            )
            continue

        predicted = project_record(prediction_record)
        source_system = (
            normalize_scalar(gold.get("metadata", {}).get("source_system"))
            or predicted["metadata"]["source_system"]
            or "unknown"
        )
        source_bucket = by_source.setdefault(
            source_system,
            {
                "sample_count": 0,
                "metadata": {"correct": 0, "total": 0},
                "metrics": {name: metric_bucket() for name in overall_metrics},
            },
        )
        source_bucket["sample_count"] += 1

        metadata_fields = set((gold.get("metadata") or {}).keys()) | set(
            predicted["metadata"].keys()
        )
        sample_metadata = {"correct": 0, "total": 0}
        for field_name in sorted(metadata_fields):
            gold_value = normalize_scalar((gold.get("metadata") or {}).get(field_name))
            predicted_value = normalize_scalar(predicted["metadata"].get(field_name))
            if gold_value is None and predicted_value is None:
                continue
            sample_metadata["total"] += 1
            metadata_totals["total"] += 1
            source_bucket["metadata"]["total"] += 1
            if gold_value == predicted_value:
                sample_metadata["correct"] += 1
                metadata_totals["correct"] += 1
                source_bucket["metadata"]["correct"] += 1

        predicted_events = event_map(predicted.get("events"))
        gold_events = event_map(gold.get("events"))

        event_tp, event_fp, event_fn = compare_sets(predicted_events.keys(), gold_events.keys())
        add_metric_counts(overall_metrics["event_name"], event_tp, event_fp, event_fn)
        add_metric_counts(source_bucket["metrics"]["event_name"], event_tp, event_fp, event_fn)

        set_fields = {
            "record_topics": (predicted.get("topics"), gold.get("topics")),
            "record_government_bodies": (
                predicted.get("government_bodies"),
                gold.get("government_bodies"),
            ),
            "record_locations": (predicted.get("locations"), gold.get("locations")),
        }
        sample_metric_results = {}
        for metric_name, (predicted_values, gold_values) in set_fields.items():
            tp, fp, fn = compare_sets(predicted_values, gold_values)
            add_metric_counts(overall_metrics[metric_name], tp, fp, fn)
            add_metric_counts(source_bucket["metrics"][metric_name], tp, fp, fn)
            sample_metric_results[metric_name] = prf_from_counts(tp, fp, fn)

        event_type_counts = compare_event_types(predicted_events, gold_events)
        add_metric_counts(
            overall_metrics["event_type"],
            event_type_counts["tp"],
            event_type_counts["fp"],
            event_type_counts["fn"],
        )
        add_metric_counts(
            source_bucket["metrics"]["event_type"],
            event_type_counts["tp"],
            event_type_counts["fp"],
            event_type_counts["fn"],
        )

        for metric_name, field_name in [
            ("event_topics", "policy_topics"),
            ("institution_links", "government_bodies"),
            ("political_actors", "political_actors"),
            ("political_parties", "political_parties"),
        ]:
            field_counts = compare_event_field_sets(predicted_events, gold_events, field_name)
            add_metric_counts(
                overall_metrics[metric_name],
                field_counts["tp"],
                field_counts["fp"],
                field_counts["fn"],
            )
            add_metric_counts(
                source_bucket["metrics"][metric_name],
                field_counts["tp"],
                field_counts["fp"],
                field_counts["fn"],
            )

        sample_reports.append(
            {
                "record_id": record_id,
                "source_system": source_system,
                "status": "evaluated",
                "title": predicted["metadata"]["title"],
                "metadata_accuracy": round(sample_metadata["correct"] / sample_metadata["total"], 4)
                if sample_metadata["total"]
                else 0.0,
                "event_name_metrics": prf_from_counts(event_tp, event_fp, event_fn),
                "record_topic_metrics": sample_metric_results["record_topics"],
                "record_government_body_metrics": sample_metric_results["record_government_bodies"],
                "record_location_metrics": sample_metric_results["record_locations"],
            }
        )

    overall_summary = {
        name: summarize_metric_bucket(bucket) for name, bucket in overall_metrics.items()
    }
    overall_summary["metadata_accuracy"] = (
        round(metadata_totals["correct"] / metadata_totals["total"], 4)
        if metadata_totals["total"]
        else 0.0
    )

    by_source_summary = {}
    for source_system, payload in sorted(by_source.items()):
        by_source_summary[source_system] = {
            "sample_count": payload["sample_count"],
            "metadata_accuracy": round(
                payload["metadata"]["correct"] / payload["metadata"]["total"], 4
            )
            if payload["metadata"]["total"]
            else 0.0,
            "metrics": {
                name: summarize_metric_bucket(bucket)
                for name, bucket in sorted(payload["metrics"].items())
            },
        }

    return {
        "sample_count": len(
            [sample for sample in sample_reports if sample["status"] == "evaluated"]
        ),
        "missing_prediction_count": len(
            [sample for sample in sample_reports if sample["status"] == "missing_prediction"]
        ),
        "overall": overall_summary,
        "by_source_system": by_source_summary,
        "samples": sample_reports,
    }


def build_markdown_report(report, gold_path, prediction_path):
    lines = [
        "# Extraction Evaluation",
        "",
        f"- Gold standard: `{gold_path}`",
        f"- Prediction input: `{prediction_path}`",
        f"- Evaluated samples: `{report['sample_count']}`",
        f"- Missing predictions: `{report['missing_prediction_count']}`",
        "",
        "## Overall Metrics",
        "",
        f"- Metadata accuracy: `{report['overall']['metadata_accuracy']}`",
    ]
    metric_order = [
        "event_name",
        "event_type",
        "record_topics",
        "event_topics",
        "institution_links",
        "political_actors",
        "political_parties",
        "record_government_bodies",
        "record_locations",
    ]
    for metric_name in metric_order:
        metric = report["overall"][metric_name]
        lines.append(
            f"- {metric_name}: precision `{metric['precision']}`, recall `{metric['recall']}`, f1 `{metric['f1']}`"
        )

    lines.extend(["", "## By Source System", ""])
    for source_system, payload in report["by_source_system"].items():
        lines.append(f"### {source_system}")
        lines.append("")
        lines.append(f"- Samples: `{payload['sample_count']}`")
        lines.append(f"- Metadata accuracy: `{payload['metadata_accuracy']}`")
        for metric_name in metric_order:
            metric = payload["metrics"][metric_name]
            lines.append(
                f"- {metric_name}: precision `{metric['precision']}`, recall `{metric['recall']}`, f1 `{metric['f1']}`"
            )
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def write_markdown(path, content):
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")


def build_parser():
    parser = argparse.ArgumentParser(
        description="Generate and score a gold-standard extraction evaluation sample."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    template_parser = subparsers.add_parser(
        "template", help="Create an editable gold-standard template from current predictions."
    )
    template_parser.add_argument(
        "--predictions",
        type=Path,
        default=find_most_recent("*_kg_records.json") or Path("data/processed/kg_records.json"),
    )
    template_parser.add_argument("--output", type=Path, default=DEFAULT_GOLD_STANDARD_PATH)
    template_parser.add_argument("--per-source", type=int, default=3)
    template_parser.add_argument("--limit", type=int, default=0)
    template_parser.add_argument("--ids", nargs="*", default=None)

    evaluate_parser = subparsers.add_parser(
        "evaluate", help="Score a completed gold-standard file against current predictions."
    )
    evaluate_parser.add_argument(
        "--predictions",
        type=Path,
        default=find_most_recent("*_kg_records.json") or Path("data/processed/kg_records.json"),
    )
    evaluate_parser.add_argument("--gold", type=Path, default=DEFAULT_GOLD_STANDARD_PATH)
    evaluate_parser.add_argument("--json-output", type=Path, default=DEFAULT_JSON_OUTPUT_PATH)
    evaluate_parser.add_argument("--markdown-output", type=Path, default=DEFAULT_MD_OUTPUT_PATH)
    return parser


def run_template(args):
    records = load_json(args.predictions)
    selected_records = select_template_records(
        records,
        ids=args.ids,
        per_source=max(args.per_source, 0),
        limit=max(args.limit, 0),
    )
    template = build_gold_template(selected_records, args.predictions)
    save_json(args.output, template)
    print(
        f"[EXTRACTION-EVAL] Wrote gold-standard template with {len(selected_records)} samples to {args.output}"
    )


def run_evaluation(args):
    prediction_records = load_json(args.predictions)
    gold_standard = load_json(args.gold)
    report = evaluate_samples(prediction_records, gold_standard)
    save_json(args.json_output, report)
    write_markdown(
        args.markdown_output,
        build_markdown_report(report, args.gold, args.predictions),
    )
    print(
        "[EXTRACTION-EVAL] "
        f"Evaluated {report['sample_count']} samples; results saved to {args.json_output} "
        f"and {args.markdown_output}"
    )


def main():
    parser = build_parser()
    args = parser.parse_args()
    if args.command == "template":
        run_template(args)
    elif args.command == "evaluate":
        run_evaluation(args)


if __name__ == "__main__":
    main()
