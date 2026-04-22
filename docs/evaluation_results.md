# Evaluation Results

This document records the latest validated evaluation snapshot for the current pipeline.

Evaluated run:

- `20260421T232429Z`

Primary artefacts:

- `data/processed/20260421T232429Z_normalised_articles.json`
- `data/processed/20260421T232429Z_extracted_articles.json`
- `data/processed/20260421T232429Z_kg_records.json`
- `output/20260421T232429Z_instance_kg.ttl`
- `output/20260421T232429Z_wikidata_kg.ttl`
- `output/20260421T232429Z_prototype_kg.ttl`
- `output/20260421T232429Z_completed_kg.ttl`
- `output/20260421T232429Z_query_results.json`
- `output/20260421T232429Z_validation_results.json`
- `output/20260421T232429Z_completion_audit.json`
- `output/20260421T232429Z_kg_summary.json`

## 1. Structural Results

The pipeline completed all stages successfully.

Source records:

- Guardian records: `253`
- Parliament records: `20`
- GOV.UK records: `459`
- Combined normalised records: `732`

Wikidata enrichment:

- Politicians: `1722`
- Political parties: `968`
- Government bodies: `490`

Generated graph counts:

- Ontology graph: `188` triples
- Source-derived instance KG: `15032` triples
- Wikidata KG: `25051` triples
- Prototype KG: `40107` triples
- Completed KG: `40830` triples

Completion additions:

- `272` `news:reportsOn` inverse links
- `237` `news:matchedToSourceRecord` links
- `4` `news:representedInOfficialSource` links
- RAG additions: `13` actor links, `14` department links, `138` topic links
- Total delta from prototype to completed KG: `723` triples

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
| CQ03 | 8 |
| CQ04 | 237 |
| CQ05 | 4 |
| CQ06 | 9 |
| CQ07 | 16 |
| CQ08 | 4 |
| CQ09 | 8 |
| CQ10 | 12 |
| CQ11 | 224 |
| CQ12 | 12 |
| CQ13 | 41 |
| CQ14 | 12 |
| CQ15 | 12 |
| CQ16 | 5 |
| CQ17 | 2 |
| CQ18 | 12 |
| CQ19 | 1 |
| CQ20 | 16 |

Important judgments:

- `CQ04` confirms that reported policy events can also be represented in official Parliament or GOV.UK source records.
- `CQ11` and `CQ12` confirm that official source records support institution and topic queries over the completed graph.
- `CQ17` was tightened to require source-grounded government policy events, reducing weak article-only over-linking.
- `CQ09` intentionally exposes missing links, so a non-zero result is useful for incompleteness analysis rather than a failure.

## 3. Validation and Summary Metrics

Validation:

- Rules checked: `17`
- Failed rules: `0`
- Violations: `0`

Summary metrics:

- Policy events: `271`
- Government policy events: `182`
- Parliamentary events: `6`
- Parliamentary debates: `9`
- Ministerial statements: `66`
- Events with dates: `271` (`100%`)
- Events with topics: `271` (`100%`)
- Events with a government body: `263` (`97.05%`)
- Events linked to official source records: `237` (`87.45%`)

Extraction summary:

- Extracted events: `272`
- Generic fallback events: `31`
- Generic fallback names:
  - `Policy Announcement`: `22`
  - `Ministerial Statement`: `9`
- Confidence counts:
  - `high`: `157`
  - `medium`: `108`
  - `low`: `7`
- Extraction methods:
  - `heuristic`: `254`
  - `openai`: `18`

## 4. Baseline Comparison

The direct LLM baseline comparison was refreshed against the latest prototype and completed graphs.

Reference file:

- `docs/baseline_comparison.md`

Headline results:

- `CQ04`: prototype `233`, completed `237`, delta `+4`
- `CQ11`: prototype `212`, completed `224`, delta `+12`
- `CQ12`: prototype `11`, completed `12`, delta `+1`
- `CQ16`: prototype `5`, completed `5`, delta `+0`
- `CQ18`: prototype `11`, completed `12`, delta `+1`

Interpretation:

- The completed KG improves several query families in ways that a direct LLM answer cannot reliably ground in the actual dataset.
- `CQ16` shows that some actor-party-topic structure was already present before completion, while other target queries measurably benefit from completion and enrichment.

## 5. Evaluation Position

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
