import os
from datetime import UTC, datetime

from src.build_ontology import build_ontology
from src.config import CONFIG
from src.data_collection import collect_politics_news_dataset
from src.data_extraction import extract_relevant_information
from src.data_normalisation import normalise_data
from src.json_to_rdf import convert_json_to_rdf


def save_rdf_to_file(rdf_graph, filename):
    print(f"[SAVE] Serializing RDF graph to {filename}...")
    parent = os.path.dirname(filename)
    if parent:
        os.makedirs(parent, exist_ok=True)
    rdf_graph.serialize(destination=filename, format="turtle")
    print(f"[SAVE] Saved {len(rdf_graph)} triples to {filename}.")


def main():
    print("[PIPELINE] Starting fixed-scope UK politics/policy pipeline")
    print(f"[PIPELINE] Scope: {CONFIG['scope_sentence']}")

    print("[PIPELINE] Stage 1: Collect")
    raw_data = collect_politics_news_dataset()

    print("[PIPELINE] Stage 2: Extract")
    extracted_data = extract_relevant_information(raw_data)

    print("[PIPELINE] Stage 3: Normalise")
    normalised_data = normalise_data(extracted_data)

    print("[PIPELINE] Stage 4: Convert to RDF")
    rdf_graph = convert_json_to_rdf(normalised_data)

    print("[PIPELINE] Stage 5: Merge ontology and instance data")
    kg_graph = build_ontology()
    for triple in rdf_graph:
        kg_graph.add(triple)

    print("[PIPELINE] Stage 6: Save")
    save_rdf_to_file(kg_graph, "kg/generated/new_kg.ttl")

    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    save_rdf_to_file(kg_graph, f"output/{timestamp}_kg.ttl")

    print("[PIPELINE] Done.")


if __name__ == "__main__":
    main()
