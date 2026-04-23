import argparse
from pathlib import Path

from src.openai_client import (
    build_cache_path,
    load_cache_payload,
    request_structured_output,
    save_cache_payload,
)
from src.run_queries import execute_queries, load_kg, load_query_definitions

TARGET_IDS = {"CQ04", "CQ11", "CQ12", "CQ16", "CQ18"}

OUTPUT_DIR = Path("output")
FALLBACK_PROTOTYPE = Path("kg/generated/prototype_kg.ttl")
FALLBACK_COMPLETED = Path("kg/generated/completed_kg.ttl")


def find_most_recent(pattern):
    matches = sorted(OUTPUT_DIR.glob(pattern))
    return matches[-1] if matches else None


BASELINE_SCHEMA = {
    "type": "json_schema",
    "name": "baseline_answer",
    "strict": True,
    "schema": {
        "type": "object",
        "properties": {"answer": {"type": "string"}},
        "required": ["answer"],
        "additionalProperties": False,
    },
}

LLM_INSTRUCTIONS = (
    "Answer the following question about UK politics and government policy news "
    "from March to April 2026, using your training knowledge. Be specific and concise."
)


def get_llm_answer(cq_id, title):
    cache_path = build_cache_path("baseline_llm", cq_id)
    cached = load_cache_payload(cache_path)
    if cached is not None:
        return cached.get("answer", "")

    try:
        result = request_structured_output(LLM_INSTRUCTIONS, title, BASELINE_SCHEMA)
    except Exception as exc:
        print(f"[EVAL] LLM request failed for {cq_id}: {exc}")
        return "(LLM unavailable)"
    if result is None:
        return "(LLM unavailable)"

    save_cache_payload(cache_path, result)
    return result.get("answer", "")


def interpret_delta(cq_id, proto_count, completed_count):
    delta = completed_count - proto_count
    if delta == 0 and completed_count == 0:
        return (
            f"neither graph returned results for {cq_id}; "
            "completion added no triples matching this query shape"
        )
    if delta == 0:
        return (
            f"completion did not change the row count for {cq_id}; "
            "the relevant triples were already present in the prototype"
        )
    if delta > 0:
        noun = "row" if delta == 1 else "rows"
        return (
            f"completion added {delta} {noun} for {cq_id} that SPARQL can traverse "
            "but the LLM cannot ground in the actual dataset"
        )
    return (
        f"{cq_id} returned {abs(delta)} fewer rows after completion; "
        "possible query shape mismatch between the two graphs"
    )


def build_table(rows):
    header = "| CQ | prototype count | completed count | delta | LLM answer |"
    sep = "|----|-----------------|-----------------|-------|------------|"
    lines = [header, sep]
    for row in rows:
        llm = row["llm"]
        truncated = llm[:80] + "..." if len(llm) > 80 else llm
        truncated = truncated.replace("\n", " ")
        lines.append(
            f"| {row['cq_id']} | {row['proto']} | {row['completed']} "
            f"| {row['delta']:+d} | {truncated} |"
        )
    return "\n".join(lines)


def run(proto_path, completed_path):
    print(f"[EVAL] loading {proto_path}")
    proto_graph = load_kg(proto_path)
    print(f"[EVAL] loading {completed_path}")
    completed_graph = load_kg(completed_path)

    all_defs = load_query_definitions()
    target_defs = [d for d in all_defs if d.query_id in TARGET_IDS]

    print(f"[EVAL] running {len(target_defs)} queries against prototype")
    proto_results = {
        r["query_id"]: r["row_count"] for r in execute_queries(proto_graph, target_defs)
    }
    print(f"[EVAL] running {len(target_defs)} queries against completed KG")
    completed_results = {
        r["query_id"]: r["row_count"] for r in execute_queries(completed_graph, target_defs)
    }

    titles = {d.query_id: d.title for d in target_defs}

    table_rows = []
    interpretations = []
    for cq_id in sorted(TARGET_IDS):
        proto = proto_results.get(cq_id, 0)
        completed = completed_results.get(cq_id, 0)
        delta = completed - proto
        title = titles.get(cq_id, cq_id)

        print(f"[EVAL] fetching LLM baseline for {cq_id}")
        llm = get_llm_answer(cq_id, title)

        table_rows.append(
            {
                "cq_id": cq_id,
                "proto": proto,
                "completed": completed,
                "delta": delta,
                "llm": llm,
            }
        )
        interpretations.append((cq_id, interpret_delta(cq_id, proto, completed)))

    return table_rows, interpretations


def main():
    parser = argparse.ArgumentParser(
        description="compare KG-backed SPARQL answers to direct LLM baseline for 5 target CQs"
    )
    parser.add_argument("--prototype", type=Path, default=None)
    parser.add_argument("--completed", type=Path, default=None)
    args = parser.parse_args()

    proto_path = args.prototype or (
        FALLBACK_PROTOTYPE
        if FALLBACK_PROTOTYPE.exists()
        else find_most_recent("*_prototype_kg.ttl")
    )
    completed_path = args.completed or (
        FALLBACK_COMPLETED
        if FALLBACK_COMPLETED.exists()
        else find_most_recent("*_completed_kg.ttl")
    )

    table_rows, interpretations = run(proto_path, completed_path)

    table = build_table(table_rows)
    print()
    print(table)
    print()
    for cq_id, interp in interpretations:
        print(f"{cq_id}: {interp}")

    md_lines = ["# baseline comparison: KG-backed SPARQL vs direct LLM\n", table, ""]
    for cq_id, interp in interpretations:
        md_lines.append(f"**{cq_id}**: {interp}")

    out_path = Path("docs/baseline_comparison.md")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(md_lines) + "\n", encoding="utf-8")
    print(f"\n[EVAL] saved to {out_path}")


if __name__ == "__main__":
    main()
