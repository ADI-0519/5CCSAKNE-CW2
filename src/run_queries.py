import argparse
import json
from dataclasses import dataclass
from pathlib import Path

from rdflib import Graph

from src.config import CONFIG
from src.data_normalisation import normalise_name

DEFAULT_QUERY_PATH = Path("queries/news_competency_queries.rq")
DEFAULT_KG_CANDIDATES = (
    Path("kg/generated/prototype_kg.ttl"),
    Path("kg/generated/new_kg.ttl"),
)


@dataclass(frozen=True)
class QueryDefinition:
    query_id: str
    title: str
    query_text: str


def split_header(header_line):
    if not header_line.startswith("# CQ"):
        raise ValueError(f"Invalid query header: {header_line!r}")

    header = header_line[2:].strip()
    query_id, _, title = header.partition(":")
    return query_id.strip(), title.strip()


def load_query_definitions(query_file=DEFAULT_QUERY_PATH):
    query_path = Path(query_file)
    if not query_path.exists():
        raise FileNotFoundError(f"Query file not found: {query_path}")

    raw = query_path.read_text(encoding="utf-8")
    raw = raw.replace("{DATE_START}", CONFIG["date_start"])
    raw = raw.replace("{DATE_END}", CONFIG["date_end"])
    lines = raw.splitlines()
    prefix_lines = []
    definitions = []
    current_header = None
    current_lines = []

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("PREFIX ") and current_header is None:
            prefix_lines.append(line)
            continue

        if stripped.startswith("# CQ"):
            if current_header is not None:
                query_id, title = split_header(current_header)
                definitions.append(
                    QueryDefinition(
                        query_id=query_id,
                        title=title,
                        query_text="\n".join(prefix_lines + [""] + current_lines).strip(),
                    )
                )
            current_header = stripped
            current_lines = []
            continue

        if current_header is not None:
            current_lines.append(line)

    if current_header is not None:
        query_id, title = split_header(current_header)
        definitions.append(
            QueryDefinition(
                query_id=query_id,
                title=title,
                query_text="\n".join(prefix_lines + [""] + current_lines).strip(),
            )
        )

    if not definitions:
        raise ValueError(f"No competency queries found in {query_path}")

    return definitions


def load_kg(kg_path):
    kg_file = Path(kg_path)
    if not kg_file.exists():
        raise FileNotFoundError(f"KG file not found: {kg_file}")

    graph = Graph(store="Oxigraph")
    graph.parse(data=kg_file.read_text(encoding="utf-8"), format="turtle")
    return graph


def choose_default_kg():
    for candidate in DEFAULT_KG_CANDIDATES:
        if candidate.exists():
            return candidate
    raise FileNotFoundError(
        "No KG file found. Expected one of: "
        + ", ".join(str(candidate) for candidate in DEFAULT_KG_CANDIDATES)
    )


def term_to_string(term):
    return None if term is None else str(term)


def normalise_result_value(variable_name, value):
    if value is None:
        return None
    return normalise_name(value)


def deduplicate_rows(rows):
    seen = set()
    deduped = []
    for row in rows:
        key = json.dumps(row, sort_keys=True, ensure_ascii=False)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(row)
    return deduped


def execute_queries(graph, query_definitions):
    results = []
    for definition in query_definitions:
        query_result = graph.query(definition.query_text)
        rows = []
        variables = [str(var) for var in query_result.vars]

        for row in query_result:
            rows.append(
                {
                    str(var): normalise_result_value(str(var), term_to_string(row[var]))
                    for var in query_result.vars
                }
            )

        rows = deduplicate_rows(rows)

        results.append(
            {
                "query_id": definition.query_id,
                "title": definition.title,
                "variables": variables,
                "row_count": len(rows),
                "rows": rows,
            }
        )

    return results


def save_results(results, output_path):
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")


def build_arg_parser():
    parser = argparse.ArgumentParser(description="Run competency-question SPARQL queries.")
    parser.add_argument(
        "--kg",
        type=Path,
        default=None,
        help="Path to the Turtle KG file. Defaults to prototype_kg.ttl or new_kg.ttl if present.",
    )
    parser.add_argument(
        "--queries",
        type=Path,
        default=DEFAULT_QUERY_PATH,
        help="Path to the .rq file containing the competency queries.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional path to write query results as JSON.",
    )
    return parser


def main():
    parser = build_arg_parser()
    args = parser.parse_args()

    kg_path = args.kg or choose_default_kg()
    definitions = load_query_definitions(args.queries)
    graph = load_kg(kg_path)
    results = execute_queries(graph, definitions)

    answered = sum(1 for result in results if result["row_count"] > 0)
    print(f"[QUERIES] KG: {kg_path}")
    print(f"[QUERIES] Executed {len(results)} competency queries.")
    print(f"[QUERIES] {answered} queries returned at least one row.")

    for result in results:
        print(f"[QUERIES] {result['query_id']}: {result['row_count']} rows")

    if args.output:
        save_results(results, args.output)
        print(f"[QUERIES] Saved JSON results to {args.output}")


if __name__ == "__main__":
    main()
