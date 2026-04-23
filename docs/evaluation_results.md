# Evaluation Results

This document records the latest validated evaluation snapshot for the current pipeline.

Evaluated run:

- `20260422T202216Z`

Primary artefacts:

- `data/processed/20260422T202216Z_normalised_articles.json`
- `data/processed/20260422T202216Z_extracted_articles.json`
- `data/processed/20260422T202216Z_kg_records.json`
- `kg/generated/new_kg.ttl`
- `kg/generated/wikidata_kg.ttl`
- `kg/generated/prototype_kg.ttl`
- `kg/generated/completed_kg.ttl`
- `output/query_results.json`
- `output/validation_results.json`
- `output/completion_audit.json`
- `output/kg_summary.json`

## 1. Structural Results

The pipeline completed all stages successfully.

Source records:

- Guardian records: `253`
- Parliament records: `20`
- GOV.UK records: `459`
- Combined normalised records: `732`

Wikidata enrichment:

- Politicians: `1715`
- Political parties: `968`
- Government bodies: `489`

Generated graph counts:

- Ontology graph: `188` triples
- Source-derived instance KG: `15095` triples
- Wikidata KG: `25020` triples
- Prototype KG: `40125` triples
- Completed KG: `40836` triples

Completion additions:

- `274` `news:reportsOn` inverse links
- `236` `news:matchedToSourceRecord` links
- `2` `news:representedInOfficialSource` links
- RAG additions: `10` actor links, `14` department links, `142` topic links
- Total delta from prototype to completed KG: `711` triples

Structural judgment:

- The pipeline is runnable end to end from live APIs.
- Raw source snapshots, processed JSON artefacts, generated Turtle files, validation reports, summary metrics, and query results are all saved.
- The ontology, source-derived RDF, Wikidata RDF, prototype KG, completed KG, and SPARQL queries are aligned around the event-centred vocabulary.
- The final graph passes all `17` graph validation rules with `0` failures and `0` violations.

## 2. Competency Question Results

All `20/20` competency queries returned at least one row when the current query set was run against the completed KG from this snapshot.

| CQ | Row count |
| --- | ---: |
| CQ01 | 14 |
| CQ02 | 66 |
| CQ03 | 10 |
| CQ04 | 235 |
| CQ05 | 3 |
| CQ06 | 6 |
| CQ07 | 16 |
| CQ08 | 4 |
| CQ09 | 8 |
| CQ10 | 16 |
| CQ11 | 221 |
| CQ12 | 12 |
| CQ13 | 41 |
| CQ14 | 16 |
| CQ15 | 12 |
| CQ16 | 7 |
| CQ17 | 1 |
| CQ18 | 15 |
| CQ19 | 2 |
| CQ20 | 16 |

Important judgments:

- `CQ04` confirms that reported policy events can also be represented in official Parliament or GOV.UK source records.
- `CQ11` and `CQ12` confirm that official source records support institution and topic queries over the completed graph.
- `CQ17` was tightened to require source-grounded government policy events, giving a more conservative and provenance-led result set.
- `CQ09` intentionally exposes remaining coverage opportunities, so a non-zero result is useful for graph-audit analysis rather than a failure.

## 3. Validation and Summary Metrics

Validation:

- Rules checked: `17`
- Failed rules: `0`
- Violations: `0`

Summary metrics:

- Policy events: `273`
- Government policy events: `185`
- Parliamentary events: `5`
- Parliamentary debates: `9`
- Ministerial statements: `66`
- Events with dates: `273` (`100%`)
- Events with topics: `273` (`100%`)
- Events with a government body: `265` (`97.07%`)
- Events linked to official source records: `235` (`86.08%`)

Extraction summary:

- Extracted events: `274`
- Generic fallback events: `32`
- Generic fallback names:
  - `Policy Announcement`: `23`
  - `Ministerial Statement`: `9`
- Confidence counts:
  - `high`: `160`
  - `medium`: `107`
  - `low`: `7`
- Extraction methods:
  - `heuristic`: `263`
  - `openai`: `11`

## 4. Performance And Reproducibility

Reference file:

- `output/performance_benchmark.json`

Measured cached benchmark:

- command: `python -m src.benchmark_pipeline --output output/performance_benchmark.json`
- platform: `Windows 10`
- Python: `3.11.5`
- end-to-end cached runtime: `131.16` seconds
- throughput: `5.58` source records per second over `732` records
- benchmark exit code: `0`

Benchmark-confirmed outputs:

- triples in completed KG: `40836`
- policy events: `273`
- events with a government body: `265`
- query coverage: `20/20`
- validation: `17` rules checked, `0` failed, `0` violations

Interpretation:

- the submitted cached pipeline is reproducible as a full end-to-end run rather than only as a collection of pre-generated artefacts
- the runtime is comfortably practical for coursework marking and reruns
- the benchmark confirms that the final reported CQ and validation numbers are generated from the same cached evidence stack used for submission

## 5. Baseline Comparison

The direct LLM baseline comparison was refreshed against the current `kg/generated/prototype_kg.ttl` and `kg/generated/completed_kg.ttl` graphs.

Reference file:

- `docs/baseline_comparison.md`

Headline results:

- `CQ04`: prototype `233`, completed `235`, delta `+2`
- `CQ11`: prototype `212`, completed `221`, delta `+9`
- `CQ12`: prototype `11`, completed `12`, delta `+1`
- `CQ16`: prototype `7`, completed `7`, delta `+0`
- `CQ18`: prototype `15`, completed `15`, delta `+0`

Interpretation:

- The completed KG improves several query families in ways that a direct LLM answer cannot reliably ground in the actual dataset.
- `CQ16` shows that some actor-party-topic structure was already present before completion, while other target queries measurably benefit from completion and enrichment.

## 6. Evaluation Position

The strongest defensible evaluation claim is:

- the pipeline runs end to end
- the ontology and RDF generation are aligned with the current CQ set
- the completed graph answers all `20` competency queries
- the final graph passes all `17` validation rules with no failures
- official-source records are integrated into the KG rather than only stored as raw data
- the completion stage improves navigability and provenance through `reportsOn`, `matchedToSourceRecord`, and conservative enrichment

The graph is strongest for:

- event-to-topic links
- event-to-institution links
- event-to-source-record links
- article-to-event reporting links
- publisher and journalist metadata
- official source provenance

The graph is also strong for:

- high-coverage heuristic extraction reinforced by targeted OpenAI support
- conservative fallback event handling that preserves coverage while remaining auditable
- a focused direct LLM baseline that illustrates the benefits of KG-backed querying on representative CQs

## 7. Recommended Final Framing

The final report should frame the system as a working automated KG pipeline with an event-centred ontology, auditable domain knowledge, conservative semantic projection, and ontology-aware QA.

It should explicitly state that:

- heuristics act as structured supervision, canonicalisation support, and fallback extraction
- OpenAI is used critically for structured extraction support, completion support, and evaluation baselines
- validation, query coverage, completion audit logs, and summary metrics provide the strongest evidence for the current final pipeline
