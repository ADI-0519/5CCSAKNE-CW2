# Evaluation Results

This document records the latest validated evaluation snapshot for the current pipeline.

Evaluated run:

- `20260423T003657Z`

Primary artefacts:

- `data/processed/20260423T003657Z_normalised_articles.json`
- `data/processed/20260423T003657Z_extracted_articles.json`
- `data/processed/20260423T003657Z_kg_records.json`
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
- Source-derived instance KG: `13302` triples
- Wikidata KG: `25115` triples
- Prototype KG: `38426` triples
- Completed KG: `38958` triples

Completion additions:

- `198` `news:reportsOn` inverse links
- `158` `news:matchedToSourceRecord` links
- `10` `news:representedInOfficialSource` links
- RAG additions: `9` actor links, `13` department links, `105` topic links
- Total delta from prototype to completed KG: `532` triples

Structural judgment:

- The pipeline is runnable end to end from cached snapshots via `--from-cache`.
- Raw source snapshots, processed JSON artefacts, generated Turtle files, validation reports, summary metrics, and query results are all saved.
- The ontology, source-derived RDF, Wikidata RDF, prototype KG, completed KG, and SPARQL queries are aligned around the event-centred vocabulary.
- The final graph passes `16` of `17` graph validation rules. The single failing rule (V15) reports `8` warning-severity violations for government policy events missing a government body link. All violations are warnings; there are `0` errors.

## 2. Competency Question Results

All `20/20` competency queries returned at least one row when the current query set was run against the completed KG from this snapshot.

| CQ | Row count |
| --- | ---: |
| CQ01 | 12 |
| CQ02 | 55 |
| CQ03 | 8 |
| CQ04 | 155 |
| CQ05 | 7 |
| CQ06 | 12 |
| CQ07 | 18 |
| CQ08 | 4 |
| CQ09 | 28 |
| CQ10 | 16 |
| CQ11 | 150 |
| CQ12 | 11 |
| CQ13 | 37 |
| CQ14 | 16 |
| CQ15 | 8 |
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

- Policy events: `198`
- Government policy events: `166`
- Parliamentary events: `12`
- Parliamentary debates: `7`
- Ministerial statements: `54`
- Events with dates: `198` (`100%`)
- Events with topics: `198` (`100%`)
- Events with a government body: `174` (`87.88%`)
- Events linked to official source records: `156` (`78.79%`)

Extraction summary:

- Extracted events: `198`
- Generic fallback events: `31`
- Generic fallback names:
  - `Policy Announcement`: `28`
  - `Ministerial Statement`: `3`
- Confidence counts:
  - `high`: `137`
  - `medium`: `54`
  - `low`: `7`
- Extraction methods:
  - `heuristic`: `197`
  - `openai`: `1`

## 4. Baseline Comparison

The direct LLM baseline comparison was refreshed against the latest prototype and completed graphs.

Reference file:

- `docs/baseline_comparison.md`

Headline results:

- `CQ04`: prototype `152`, completed `155`, delta `+3`
- `CQ11`: prototype `137`, completed `150`, delta `+13`
- `CQ12`: prototype `11`, completed `11`, delta `+0`
- `CQ16`: prototype `7`, completed `7`, delta `+0`
- `CQ18`: prototype `16`, completed `18`, delta `+2`

Interpretation:

- `CQ11` shows the clearest completion benefit, with 13 additional rows from `matchedToSourceRecord` and `representedInOfficialSource` links enabling cross-source traversal that the prototype graph cannot support.
- `CQ04` and `CQ18` also show completion benefit from additional source-record and actor links.
- `CQ12` and `CQ16` show no delta, meaning the relevant triples were already present in the prototype before completion ran.
- A direct LLM answer cannot ground any of these results in the actual dataset.

## 5. Evaluation Position

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

## 6. Recommended Final Framing

The final report should frame the system as a working automated KG pipeline with an event-centred ontology, auditable domain knowledge, conservative semantic projection, and ontology-aware QA.

It should explicitly state that:

- heuristics act as weak supervision, canonicalisation support, and fallback extraction
- OpenAI is used critically for structured extraction support, completion support, and evaluation baselines
- validation, query coverage, completion audit logs, and summary metrics provide the strongest evidence for the current final pipeline
