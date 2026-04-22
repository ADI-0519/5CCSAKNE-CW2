import argparse
import json
from pathlib import Path

DEFAULT_AUDIT_PATH = Path("output/completion_audit.json")
DEFAULT_JSON_OUTPUT = Path("output/rag_evaluation.json")
DEFAULT_MD_OUTPUT = Path("docs/rag_evaluation.md")

OUTPUT_DIR = Path("output")


def find_most_recent_audit():
    matches = sorted(OUTPUT_DIR.glob("*_completion_audit.json"))
    if matches:
        return matches[-1]
    return DEFAULT_AUDIT_PATH


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def save_json(path, payload):
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def uri_to_label(uri):
    fragment = uri.split("#")[-1]
    # strip sub-type prefix (e.g. "topic/", "organisation/", "event/")
    if "/" in fragment:
        fragment = fragment.split("/", 1)[1]
    return fragment.replace("_", " ")


def load_rag_cache(event_uri):
    from src.openai_client import build_cache_path, load_cache_payload

    cache_path = build_cache_path("rag_completion", event_uri)
    return load_cache_payload(cache_path)


def build_entry(audit_entry):
    event_uri = audit_entry["event_uri"]
    proposed = load_rag_cache(event_uri) or {}

    accepted_actors = audit_entry.get("rag_added_actors", [])
    accepted_depts = audit_entry.get("rag_added_departments", [])
    accepted_topics = audit_entry.get("rag_added_topics", [])

    proposed_actors = proposed.get("proposed_actors", [])
    proposed_depts = proposed.get("proposed_departments", [])
    proposed_topics = proposed.get("proposed_topics", [])

    # labels from URIs for readability
    accepted_topic_labels = [uri_to_label(t) for t in accepted_topics]
    accepted_actor_labels = [uri_to_label(a) for a in accepted_actors]
    accepted_dept_labels = [uri_to_label(d) for d in accepted_depts]

    n_proposed = len(proposed_actors) + len(proposed_depts) + len(proposed_topics)
    n_accepted = len(accepted_actors) + len(accepted_depts) + len(accepted_topics)
    n_rejected = n_proposed - n_accepted

    return {
        "event_uri": event_uri,
        "event_label": uri_to_label(event_uri),
        "matched_source_record": audit_entry.get("matched_source_record_uri"),
        "match_score": audit_entry.get("match_score"),
        "proposed_actors": proposed_actors,
        "proposed_departments": proposed_depts,
        "proposed_topics": proposed_topics,
        "accepted_actors": accepted_actor_labels,
        "accepted_departments": accepted_dept_labels,
        "accepted_topics": accepted_topic_labels,
        "n_proposed": n_proposed,
        "n_accepted": n_accepted,
        "n_rejected": n_rejected,
        # placeholder for manual annotation
        "manual_correct": None,
        "manual_notes": "",
    }


def build_report(audit_path):
    audit = load_json(audit_path)
    entries = audit.get("entries", [])

    rag_entries = []
    skipped = 0
    for e in entries:
        has_rag = (
            e.get("rag_added_actors")
            or e.get("rag_added_departments")
            or e.get("rag_added_topics")
        )
        if not has_rag:
            skipped += 1
            continue
        rag_entries.append(build_entry(e))

    total_proposed = sum(e["n_proposed"] for e in rag_entries)
    total_accepted = sum(e["n_accepted"] for e in rag_entries)
    total_rejected = sum(e["n_rejected"] for e in rag_entries)

    actor_accepted = sum(len(e["accepted_actors"]) for e in rag_entries)
    dept_accepted = sum(len(e["accepted_departments"]) for e in rag_entries)
    topic_accepted = sum(len(e["accepted_topics"]) for e in rag_entries)

    return {
        "summary": {
            "events_with_rag_additions": len(rag_entries),
            "events_skipped_no_rag": skipped,
            "total_proposed": total_proposed,
            "total_accepted": total_accepted,
            "total_rejected": total_rejected,
            "accepted_actors": actor_accepted,
            "accepted_departments": dept_accepted,
            "accepted_topics": topic_accepted,
            "acceptance_rate": round(total_accepted / total_proposed, 3) if total_proposed else 0,
        },
        "entries": rag_entries,
    }


def build_markdown(report):
    s = report["summary"]
    lines = [
        "# RAG Completion Evaluation",
        "",
        "## Summary",
        "",
        f"- events with RAG additions: `{s['events_with_rag_additions']}`",
        f"- total proposed values: `{s['total_proposed']}`",
        f"- total accepted after validation: `{s['total_accepted']}`",
        f"- total rejected by validation: `{s['total_rejected']}`",
        f"- acceptance rate (validation filter): `{s['acceptance_rate']:.1%}`",
        f"- accepted actors: `{s['accepted_actors']}`",
        f"- accepted departments: `{s['accepted_departments']}`",
        f"- accepted topics: `{s['accepted_topics']}`",
        "",
        "## Per-event sample",
        "",
        "The table below covers events where at least one RAG triple was accepted. "
        "The `manual_correct` column in `rag_evaluation.json` is left blank for manual annotation.",
        "",
        "| event | accepted actors | accepted departments | accepted topics | proposed | accepted |",
        "| --- | --- | --- | --- | ---: | ---: |",
    ]

    for e in report["entries"]:
        label = e["event_label"][:60]
        actors = ", ".join(e["accepted_actors"]) or "-"
        depts = ", ".join(e["accepted_departments"]) or "-"
        topics = ", ".join(e["accepted_topics"]) or "-"
        lines.append(
            f"| {label} | {actors} | {depts} | {topics} "
            f"| {e['n_proposed']} | {e['n_accepted']} |"
        )

    lines += [
        "",
        "## Precision estimation",
        "",
        "To estimate precision, open `output/rag_evaluation.json`, work through a sample of "
        "entries, and set `manual_correct` to `true` or `false` for each accepted triple. "
        "Precision = correct / total annotated.",
    ]

    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(
        description="evaluate RAG completion additions from completion audit and cache"
    )
    parser.add_argument("--audit", type=Path, default=None)
    parser.add_argument("--json-output", type=Path, default=DEFAULT_JSON_OUTPUT)
    parser.add_argument("--markdown-output", type=Path, default=DEFAULT_MD_OUTPUT)
    args = parser.parse_args()

    audit_path = args.audit or find_most_recent_audit()
    if not Path(audit_path).exists():
        print(f"[RAG-EVAL] audit file not found: {audit_path}")
        return

    print(f"[RAG-EVAL] reading {audit_path}")
    report = build_report(audit_path)

    s = report["summary"]
    print(
        f"[RAG-EVAL] {s['events_with_rag_additions']} events with RAG additions, "
        f"{s['total_accepted']} accepted ({s['acceptance_rate']:.1%} of proposed)"
    )

    save_json(args.json_output, report)
    print(f"[RAG-EVAL] saved {args.json_output}")

    md = build_markdown(report)
    Path(args.markdown_output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.markdown_output).write_text(md, encoding="utf-8")
    print(f"[RAG-EVAL] saved {args.markdown_output}")


if __name__ == "__main__":
    main()