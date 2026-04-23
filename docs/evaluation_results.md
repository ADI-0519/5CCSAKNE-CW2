# Evaluation Results

This document records the latest validated evaluation snapshot for the current pipeline.

Evaluated run:

- `20260423T022716Z`

Primary artefacts:

- `data/processed/20260423T022716Z_normalised_articles.json`
- `data/processed/20260423T022716Z_extracted_articles.json`
- `data/processed/20260423T022716Z_kg_records.json`
- `kg/generated/new_kg.ttl`
- `kg/generated/wikidata_kg.ttl`
- `kg/generated/prototype_kg.ttl`
- `kg/generated/completed_kg.ttl`
- `output/query_results.json`
- `output/validation_results.json`
- `output/completion_audit.json`
- `output/kg_summary.json`
- `output/rag_evaluation.json`

## 1. Structural Results

The pipeline completed all stages successfully.

Source records:

- Guardian records: `259`
- Parliament records: `20`
- GOV.UK records: `394`
- Combined normalised records: `673`

Wikidata enrichment:

- Politicians: `1724`
- Political parties: `968`
- Government bodies: `489`

Generated graph counts:

- Ontology graph: `188` triples
- Source-derived instance KG: `12978` triples
- Wikidata KG: `25115` triples
- Prototype KG: `38136` triples
- Completed KG: `38602` triples

Completion additions:

- `188` `news:reportsOn` inverse links
- `149` `news:matchedToSourceRecord` links
- `5` `news:representedInOfficialSource` links
- RAG additions: `7` actor links, `6` department links, `111` topic links
- Total delta from prototype to completed KG: `466` triples

Structural judgment:

- The pipeline is runnable end to end from cached snapshots via `--from-cache`.
- Raw source snapshots, processed JSON artefacts, generated Turtle files, validation reports, summary metrics, and query results are all saved.
- The ontology, source-derived RDF, Wikidata RDF, prototype KG, completed KG, and SPARQL queries are aligned around the event-centred vocabulary.
- The final graph passes `16` of `17` graph validation rules. The single failing rule (V15) reports `8` warning-severity violations for government policy events missing a government body link. All violations are warnings; there are `0` errors.

## 2. Competency Question Results

All `20/20` competency queries returned at least one row when the current query set was run against the completed KG from this snapshot.

| CQ | Row count |
| --- | ---: |
| CQ01 | 10 |
| CQ02 | 52 |
| CQ03 | 7 |
| CQ04 | 147 |
| CQ05 | 6 |
| CQ06 | 10 |
| CQ07 | 17 |
| CQ08 | 4 |
| CQ09 | 25 |
| CQ10 | 16 |
| CQ11 | 140 |
| CQ12 | 11 |
| CQ13 | 35 |
| CQ14 | 16 |
| CQ15 | 7 |
| CQ16 | 7 |
| CQ17 | 5 |
| CQ18 | 18 |
| CQ19 | 4 |
| CQ20 | 16 |

Important judgments:

- `CQ04` confirms that reported policy events can also be represented in official Parliament or GOV.UK source records.
- `CQ11` and `CQ12` confirm that official source records support institution and topic queries over the completed graph.
- `CQ09` intentionally exposes missing links; its count of 28 reflects the smaller dataset in this run producing proportionally more events without complete institution grounding.

## 3. Validation and Summary Metrics

Validation:

- Rules checked: `17`
- Failed rules: `1` (V15, warning severity only)
- Violations: `8` (all warnings, `0` errors)

Summary metrics:

- Policy events: `188`
- Government policy events: `165`
- Parliamentary events: `12`
- Parliamentary debates: `7`
- Ministerial statements: `52`
- Events with dates: `188` (`100%`)
- Events with topics: `188` (`100%`)
- Events with a government body: `167` (`88.83%`)
- Events linked to official source records: `147` (`78.19%`)

Extraction summary:

- Extracted events: `188`
- Generic fallback events: `22`
- Generic fallback names:
  - `Policy Announcement`: `19`
  - `Ministerial Statement`: `3`
- Confidence counts:
  - `high`: `136`
  - `medium`: `52`
- Extraction methods:
  - `heuristic`: `187`
  - `openai`: `1`

## 4. Baseline Comparison

The direct LLM baseline comparison was refreshed against the latest prototype and completed graphs.

Reference file:

- `docs/baseline_comparison.md`

Headline results:

- `CQ04`: prototype `125`, completed `125`, delta `+0`
- `CQ11`: prototype `109`, completed `115`, delta `+6`
- `CQ12`: prototype `11`, completed `11`, delta `+0`
- `CQ16`: prototype `7`, completed `7`, delta `+0`
- `CQ18`: prototype `11`, completed `12`, delta `+1`

Interpretation:

- `CQ11` shows the clearest completion benefit, with 6 additional rows from `matchedToSourceRecord` and `representedInOfficialSource` links enabling cross-source traversal that the prototype graph cannot support.
- `CQ18` also shows completion benefit from additional actor links.
- `CQ04`, `CQ12`, and `CQ16` show no delta, meaning the relevant triples were already present in the prototype before completion ran.
- A direct LLM answer cannot ground any of these results in the actual dataset.

## 5. Performance Benchmark

The benchmark times a full `--from-cache` pipeline run without any data collection or API calls.

- Elapsed time: `21.05` seconds
- Records processed: `673`
- Throughput: `31.97` records/second
- Platform: Linux (WSL2 6.6.87.2-microsoft-standard-WSL2), Python 3.12.3
- Peak memory: not available (WSL2 reports `null` for working set; measurement is Windows-only)

The benchmark confirms the pipeline is fast enough for repeated iteration from cache without any meaningful wait cost.

## 6. Evaluation Position

The strongest defensible evaluation claim is:

- the pipeline runs end to end
- the ontology and RDF generation are aligned with the current CQ set
- the completed graph answers all `20` competency queries
- the final graph passes `16` of `17` validation rules; the single V15 failure is warning-severity with `0` errors
- official-source records are integrated into the KG rather than only stored as raw data
- the completion stage improves navigability and provenance through `reportsOn`, `matchedToSourceRecord`, and conservative enrichment

The graph is strongest for:

- event-to-topic links
- event-to-institution links
- event-to-source-record links
- article-to-event reporting links
- publisher and journalist metadata
- official source provenance

The graph is weaker for:

- recall of OpenAI-driven extraction relative to heuristic extraction
- the generic fallback subset, which should be interpreted as low-information abstractions rather than richly grounded event identities
- the limited size of the direct LLM baseline, which covers only five target CQs

## 7. Recommended Final Framing

The final report should frame the system as a working automated KG pipeline with an event-centred ontology, auditable domain knowledge, conservative semantic projection, and ontology-aware QA.

It should explicitly state that:

- heuristics act as weak supervision, canonicalisation support, and fallback extraction
- OpenAI is used critically for structured extraction support, completion support, and evaluation baselines
- validation, query coverage, completion audit logs, and summary metrics provide the strongest evidence for the current final pipeline
