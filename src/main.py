import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

from rdflib import Graph

from src.build_ontology import OUTPUT_PATH as ONTOLOGY_OUTPUT_PATH
from src.build_ontology import build_ontology
from src.complete_kg import DEFAULT_OUTPUT_PATH as COMPLETED_KG_PATH
from src.complete_kg import enrich_graph
from src.config import CONFIG
from src.data_collection import collect_all_sources, load_cached_sources
from src.data_extraction import extract_relevant_information
from src.data_normalisation import (
    normalise_collected_sources,
    normalise_data,
    save_normalised_articles,
)
from src.json_to_rdf import convert_json_to_rdf
from src.run_queries import execute_queries, load_query_definitions, save_results
from src.wikidata_collection import collect_wikidata, load_cached_wikidata
from src.wikidata_to_rdf import convert_wikidata_to_rdf

INSTANCE_KG_PATH = Path(CONFIG["GENERATED_KG_DIR"]) / "new_kg.ttl"
WIKIDATA_KG_PATH = Path(CONFIG["GENERATED_KG_DIR"]) / "wikidata_kg.ttl"
PROTOTYPE_KG_PATH = Path(CONFIG["GENERATED_KG_DIR"]) / "prototype_kg.ttl"
LATEST_QUERY_RESULTS_PATH = Path("output/query_results.json")


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


def merge_graphs(*graphs):
    merged = Graph()
    for graph in graphs:
        for prefix, namespace in graph.namespace_manager.namespaces():
            merged.bind(prefix, namespace)
        for triple in graph:
            merged.add(triple)
    return merged


def build_arg_parser():
    parser = argparse.ArgumentParser(
        description="Build the UK parliamentary and government policy event KG."
    )
    parser.add_argument(
        "--from-cache",
        action="store_true",
        help="Load the latest saved raw JSON snapshots instead of calling external APIs.",
    )
    parser.add_argument(
        "--guardian-snapshot",
        type=Path,
        default=None,
        help="Optional path to a cached Guardian JSON snapshot.",
    )
    parser.add_argument(
        "--parliament-snapshot",
        type=Path,
        default=None,
        help="Optional path to a cached Parliament/Hansard JSON snapshot.",
    )
    parser.add_argument(
        "--govuk-snapshot",
        type=Path,
        default=None,
        help="Optional path to a cached GOV.UK JSON snapshot.",
    )
    parser.add_argument(
        "--newsapi-snapshot",
        type=Path,
        default=None,
        help="Optional path to a cached NewsAPI JSON snapshot used only for legacy migration.",
    )
    parser.add_argument(
        "--include-legacy-newsapi",
        action="store_true",
        help="Include legacy NewsAPI collection/loading alongside the three core sources.",
    )
    parser.add_argument(
        "--no-save-snapshots",
        action="store_true",
        help="Do not write fresh raw API snapshots during live collection.",
    )
    parser.add_argument(
        "--wikidata-snapshot",
        type=Path,
        default=None,
        help="Optional path to a cached Wikidata JSON snapshot.",
    )
    parser.add_argument(
        "--skip-wikidata",
        action="store_true",
        help="Skip the Wikidata structured data collection stage.",
    )
    return parser


def main():
    args = build_arg_parser().parse_args()
    timestamp = build_timestamp()
    print(f"[PIPELINE] Starting CW2 KG pipeline at {timestamp}")
    print(f"[PIPELINE] Scope: {CONFIG['project_scope']}")

    # ------------------------------------------------------------------
    # Stage 1: Collect all source data (textual + structured)
    # ------------------------------------------------------------------
    print("[PIPELINE] Stage 1a: Collect core source data (Guardian + Parliament + GOV.UK)")
    if args.from_cache:
        print("[PIPELINE] Mode: offline cached snapshots")
        collected_data = load_cached_sources(
            guardian_snapshot=args.guardian_snapshot,
            parliament_snapshot=args.parliament_snapshot,
            govuk_snapshot=args.govuk_snapshot,
            newsapi_snapshot=args.newsapi_snapshot,
            include_legacy_newsapi=args.include_legacy_newsapi,
        )
    else:
        print("[PIPELINE] Mode: live API collection")
        collected_data = collect_all_sources(
            save_snapshots=not args.no_save_snapshots,
            include_legacy_newsapi=args.include_legacy_newsapi,
        )

    print("[PIPELINE] Stage 1b: Collect optional Wikidata enrichment data")
    wikidata_data = None
    if args.skip_wikidata:
        print("[PIPELINE] Wikidata stage skipped (--skip-wikidata)")
    elif args.from_cache or args.wikidata_snapshot:
        wikidata_data = load_cached_wikidata(snapshot_path=args.wikidata_snapshot)
    else:
        wikidata_data = collect_wikidata(save_snapshot=not args.no_save_snapshots)

    # ------------------------------------------------------------------
    # Stage 2: Normalise news source records
    # ------------------------------------------------------------------
    print("[PIPELINE] Stage 2: Normalise collected source records")
    source_records = normalise_collected_sources(collected_data)
    save_normalised_articles(source_records, filename="normalised_articles.json")
    save_json(
        source_records, f"{CONFIG['PROCESSED_DATA_DIR']}/{timestamp}_normalised_articles.json"
    )

    # ------------------------------------------------------------------
    # Stage 3: Extract KG-ready information (NLP over textual sources)
    # ------------------------------------------------------------------
    print("[PIPELINE] Stage 3: Extract KG-ready information")
    extracted_records = extract_relevant_information(source_records)
    save_json(
        extracted_records, f"{CONFIG['PROCESSED_DATA_DIR']}/{timestamp}_extracted_articles.json"
    )

    # ------------------------------------------------------------------
    # Stage 4: Normalise extracted records
    # ------------------------------------------------------------------
    print("[PIPELINE] Stage 4: Normalise extracted records")
    kg_records = normalise_data(extracted_records)
    save_json(kg_records, f"{CONFIG['PROCESSED_DATA_DIR']}/{timestamp}_kg_records.json")

    # ------------------------------------------------------------------
    # Stage 5: Build ontology (TBox)
    # ------------------------------------------------------------------
    print("[PIPELINE] Stage 5: Build ontology")
    ontology_graph = build_ontology()
    save_rdf(ontology_graph, ONTOLOGY_OUTPUT_PATH)

    # ------------------------------------------------------------------
    # Stage 6: Convert news records to RDF (textual source → RDF)
    # ------------------------------------------------------------------
    print("[PIPELINE] Stage 6: Convert KG-ready records to RDF instances")
    instance_graph = convert_json_to_rdf(kg_records)
    save_rdf(instance_graph, INSTANCE_KG_PATH)
    save_rdf(instance_graph, f"output/{timestamp}_instance_kg.ttl")

    # ------------------------------------------------------------------
    # Stage 7: Map Wikidata to RDF (structured source → RDF, no NLP)
    # ------------------------------------------------------------------
    print("[PIPELINE] Stage 7: Map optional Wikidata enrichment to RDF")
    wikidata_graph = Graph()
    if wikidata_data is not None:
        wikidata_graph = convert_wikidata_to_rdf(wikidata_data)
        save_rdf(wikidata_graph, WIKIDATA_KG_PATH)
        save_rdf(wikidata_graph, f"output/{timestamp}_wikidata_kg.ttl")
    else:
        print("[PIPELINE] No Wikidata data to map (skipped)")

    # ------------------------------------------------------------------
    # Stage 8: Merge all graphs into prototype KG
    # ------------------------------------------------------------------
    print("[PIPELINE] Stage 8: Merge ontology, source-derived instances, and enrichment triples")
    prototype_graph = merge_graphs(ontology_graph, instance_graph, wikidata_graph)
    save_rdf(prototype_graph, PROTOTYPE_KG_PATH)
    save_rdf(prototype_graph, f"output/{timestamp}_prototype_kg.ttl")

    # ------------------------------------------------------------------
    # Stage 9: Enrich / complete the KG
    # ------------------------------------------------------------------
    print("[PIPELINE] Stage 9: Enrich the KG")
    completed_graph = enrich_graph(prototype_graph)
    save_rdf(completed_graph, COMPLETED_KG_PATH)
    save_rdf(completed_graph, f"output/{timestamp}_completed_kg.ttl")

    # ------------------------------------------------------------------
    # Stage 10: Run SPARQL competency queries
    # ------------------------------------------------------------------
    print("[PIPELINE] Stage 10: Run competency queries")
    query_results = execute_queries(completed_graph, load_query_definitions())
    timestamped_results = Path("output") / f"{timestamp}_query_results.json"
    save_results(query_results, LATEST_QUERY_RESULTS_PATH)
    save_results(query_results, timestamped_results)

    answered_queries = sum(1 for result in query_results if result["row_count"] > 0)
    print(
        f"[PIPELINE] Query coverage: {answered_queries}/{len(query_results)} "
        "queries returned at least one row."
    )

    print("[PIPELINE] Done.")


if __name__ == "__main__":
    main()
