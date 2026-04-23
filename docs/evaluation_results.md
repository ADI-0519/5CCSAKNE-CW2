# Evaluation Results

This document records the latest validated evaluation snapshot for the current pipeline.

Evaluated run:

- `20260423T110354Z`

Primary artefacts:

- `data/processed/20260423T110354Z_normalised_articles.json`
- `data/processed/20260423T110354Z_extracted_articles.json`
- `data/processed/20260423T110354Z_kg_records.json`
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

- Guardian records: `270`
- Parliament records: `20`
- GOV.UK records: `410`
- Combined normalised records: `700`

Wikidata enrichment:

- Politicians: `1724`
- Political parties: `968`
- Government bodies: `489`

Generated graph counts:

- Ontology graph: `192` triples
- Source-derived instance KG: `13438` triples
- Wikidata KG: `25115` triples
- Prototype KG: `38576` triples
- Completed KG: `39086` triples

Completion additions:

- `194` `news:reportsOn` inverse links
- `157` `news:matchedToSourceRecord` links
- `5` `news:representedInOfficialSource` links
- RAG additions: `7` actor links, `6` department links, `119` topic links
- Total delta from prototype to completed KG: `510` triples

Structural judgment:

- The pipeline is runnable end to end from cached snapshots via `--from-cache`.
- Raw source snapshots, processed JSON artefacts, generated Turtle files, validation reports, summary metrics, and query results are all saved.
- The ontology, source-derived RDF, Wikidata RDF, prototype KG, completed KG, and SPARQL queries are aligned around the event-centred vocabulary.
- The final graph passes all `17` graph validation rules with `0` violations and `0` errors.

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
| CQ07 | 18 |
| CQ08 | 4 |
| CQ09 | 17 |
| CQ10 | 16 |
| CQ11 | 142 |
| CQ12 | 11 |
| CQ13 | 35 |
| CQ14 | 16 |
| CQ15 | 7 |
| CQ16 | 7 |
| CQ17 | 5 |
| CQ18 | 18 |
| CQ19 | 5 |
| CQ20 | 17 |

Important judgments:

- `CQ04` confirms that reported policy events can also be represented in official Parliament or GOV.UK source records.
- `CQ11` and `CQ12` confirm that official source records support institution and topic queries over the completed graph.
- `CQ09` intentionally exposes missing links; its count of `17` reflects events without complete institution grounding in the current snapshot.

## 3. Validation and Summary Metrics

Validation:

- Rules checked: `17`
- Failed rules: `0`
- Violations: `0`

Summary metrics:

- Policy events: `194`
- Government policy events: `171`
- Parliamentary events: `12`
- Parliamentary debates: `7`
- Ministerial statements: `55`
- Events with dates: `194` (`100%`)
- Events with topics: `194` (`100%`)
- Events with a government body: `181` (`93.3%`)
- Events linked to official source records: `153` (`78.87%`)

Extraction summary:

- Extracted events: `194`
- Generic fallback events: `22`
- Generic fallback names:
  - `Policy Announcement`: `19`
  - `Ministerial Statement`: `3`
- Confidence counts:
  - `high`: `138`
  - `medium`: `56`
- Extraction methods:
  - `heuristic`: `193`
  - `openai`: `1`

## 4. Baseline Comparison

The direct LLM baseline is an illustrative contrast, not a controlled evaluation. The LLM answers from training knowledge without being constrained to the same 700 collected records or the same date window, so differences in counts are not straightforwardly interpretable as KG completeness gaps. The comparison is included to show that SPARQL answers are dataset-grounded and auditable in a way that direct LLM answers are not.

Reference file:

- `docs/baseline_comparison.md`

Headline results:

- `CQ04`: prototype `144`, completed `147`, delta `+3`
- `CQ11`: prototype `135`, completed `142`, delta `+7`
- `CQ12`: prototype `11`, completed `11`, delta `+0`
- `CQ16`: prototype `7`, completed `7`, delta `+0`
- `CQ18`: prototype `16`, completed `18`, delta `+2`

Interpretation:

- `CQ04` shows completion benefit, with 3 additional rows from `matchedToSourceRecord` links enabling cross-source traversal that the prototype graph cannot support.
- `CQ11` shows the clearest completion benefit, with 7 additional rows from `matchedToSourceRecord` and `representedInOfficialSource` links enabling cross-source traversal that the prototype graph cannot support.
- `CQ18` also shows completion benefit from additional actor links.
- `CQ12` and `CQ16` show no delta, meaning the relevant triples were already present in the prototype before completion ran.
- A direct LLM answer cannot ground any of these results in the actual dataset; each SPARQL result is traceable to specific triples and source records.

## 5. Performance Benchmark

The benchmark times a full `--from-cache` pipeline run without any data collection or API calls.

- Elapsed time: `24.01` seconds
- Records processed: `700`
- Throughput: `29.15` records/second
- Platform: Linux (WSL2 6.6.87.2-microsoft-standard-WSL2), Python 3.12.3
- Peak memory: `232.2 MB` (RSS, sampled via /proc on WSL2)

The benchmark confirms the pipeline is fast enough for repeated iteration from cache without any meaningful wait cost.

## 6. Evaluation Position

The strongest defensible evaluation claim is:

- the pipeline runs end to end
- the ontology and RDF generation are aligned with the current CQ set
- the completed graph answers all `20` competency queries
- the final graph passes all `17` validation rules with `0` violations
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

- heuristics act as primary extraction; OpenAI extraction is a targeted fallback that fires only when the heuristic result lacks both structured events and an institution or actor. . 193 of 194 events had enough structure for the gate to skip the LLM call entirely.
- the primary LLM contribution in the pipeline is the RAG completion step, which processed `95` events and accepted `132` triples
- OpenAI is used critically for structured extraction support, completion support, and evaluation baselines
- validation, query coverage, completion audit logs, and summary metrics provide the strongest evidence for the current final pipeline
