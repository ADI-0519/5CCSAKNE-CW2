import os
from datetime import datetime

from src.data_collection import load_data_from_url
from src.data_extraction import extract_relevant_information
from src.data_normalisation import normalise_data
from src.json_to_rdf import convert_json_to_rdf
from src.config import CONFIG


def save_rdf_to_file(rdf_graph, filename):
    print(f"[SAVE] Serializing RDF graph to {filename}...")
    parent = os.path.dirname(filename)
    if parent:
        os.makedirs(parent, exist_ok=True)
    rdf_graph.serialize(destination=filename, format="turtle")
    print(f"[SAVE] Saved {len(rdf_graph)} triples to {filename}.")


def main():
    print(f"[PIPELINE] Starting news-to-RDF pipeline ({CONFIG['today']})")

    print("[PIPELINE] Stage 1: Collect")
    raw_data = load_data_from_url(CONFIG["url_headlines"])

    print("[PIPELINE] Stage 2: Extract")
    extracted_data = extract_relevant_information(raw_data)

    print("[PIPELINE] Stage 3: Normalise")
    normalised_data = normalise_data(extracted_data)

    print("[PIPELINE] Stage 4: Convert to RDF")
    rdf_graph = convert_json_to_rdf(normalised_data)

    print("[PIPELINE] Stage 5: Save")
    save_rdf_to_file(rdf_graph, "kg/new_kg.ttl")

    timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    save_rdf_to_file(rdf_graph, f"output/{timestamp}_kg.ttl")

    print("[PIPELINE] Done.")


if __name__ == "__main__":
    main()