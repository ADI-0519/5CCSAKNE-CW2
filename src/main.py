import json
from datetime import UTC, datetime
from pathlib import Path

from src.build_ontology import build_ontology
from src.config import CONFIG
from src.data_collection import collect_all_sources
from src.data_extraction import extract_relevant_information
from src.data_normalisation import (
    normalise_collected_sources,
    normalise_data,
    save_normalised_articles,
)
from src.json_to_rdf import convert_json_to_rdf


def build_timestamp():
    return datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")


def ensure_parent(path):
    path.parent.mkdir(parents=True, exist_ok=True)


def save_json(data, filename):
    output_path = Path(filename)
    ensure_parent(output_path)
    output_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[SAVE] Saved JSON output to {output_path}")
    return output_path


def save_rdf(graph, filename):
    output_path = Path(filename)
    ensure_parent(output_path)
    graph.serialize(destination=str(output_path), format="turtle")
    print(f"[SAVE] Saved {len(graph)} triples to {output_path}")
    return output_path


def main():
    timestamp = build_timestamp()
    print(f"[PIPELINE] Starting news KG pipeline at {timestamp}")
    print(f"[PIPELINE] Scope: {CONFIG['project_scope']}")

    print("[PIPELINE] Stage 1: Collect source data")
    collected_data = collect_all_sources(save_snapshots=True)

    print("[PIPELINE] Stage 2: Normalise source records")
    source_records = normalise_collected_sources(collected_data)
    save_normalised_articles(source_records, filename="normalised_articles.json")
    save_json(
        source_records, f"{CONFIG['PROCESSED_DATA_DIR']}/{timestamp}_normalised_articles.json"
    )

    print("[PIPELINE] Stage 3: Extract KG-ready information")
    extracted_records = extract_relevant_information(source_records)
    save_json(
        extracted_records, f"{CONFIG['PROCESSED_DATA_DIR']}/{timestamp}_extracted_articles.json"
    )

    print("[PIPELINE] Stage 4: Normalise extracted records")
    kg_records = normalise_data(extracted_records)
    save_json(kg_records, f"{CONFIG['PROCESSED_DATA_DIR']}/{timestamp}_kg_records.json")

    print("[PIPELINE] Stage 5: Convert to RDF")
    rdf_graph = convert_json_to_rdf(kg_records)

    print("[PIPELINE] Stage 6: Save knowledge graph")
    save_rdf(rdf_graph, f"{CONFIG['GENERATED_KG_DIR']}/new_kg.ttl")
    save_rdf(rdf_graph, f"output/{timestamp}_kg.ttl")

    print("[PIPELINE] Done.")


if __name__ == "__main__":
    main()
