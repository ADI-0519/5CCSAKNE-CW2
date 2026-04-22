# Evaluation Results

This document records the latest validated evaluation snapshot for the current pipeline.

Evaluated run:

- `20260422T172612Z`

Primary artefacts:

- `data/processed/20260422T172612Z_normalised_articles.json`
- `data/processed/20260422T172612Z_extracted_articles.json`
- `data/processed/20260422T172612Z_kg_records.json`
- `output/20260422T172612Z_instance_kg.ttl`
- `output/20260422T172612Z_wikidata_kg.ttl`
- `output/20260422T172612Z_prototype_kg.ttl`
- `output/20260422T172612Z_completed_kg.ttl`
- `output/20260422T172612Z_query_results.json`
- `output/20260422T172612Z_validation_results.json`
- `output/20260422T172612Z_completion_audit.json`
- `output/20260422T172612Z_kg_summary.json`
- `output/rag_evaluation.json`

## 1. Structural Results

The pipeline completed all stages successfully.

Source records:

- Guardian records: `253`
- Parliament records: `20`
- GOV.UK records: `459`
- Combined normalised records: `732`

Wikidata enrichment:

- Politicians: `1765`
- Political parties: `1006`
- Government bodies: `483`

Generated graph counts:

- Ontology graph: `188` triples
- Source-derived instance KG: `14862` triples
- Wikidata KG: `25020` triples
- Prototype KG: `39895` triples
- Completed KG: `40600` triples

Completion additions:

- `274` `news:reportsOn` inverse links
- `236` `news:matchedToSourceRecord` links
- `2` `news:representedInOfficialSource` links
- RAG additions: `9` actor links, `15` department links, `139` topic links
- Total delta from prototype to completed KG: `705` triples

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
| CQ03 | 11 |
| CQ04 | 235 |
| CQ05 | 3 |
| CQ06 | 6 |
| CQ07 | 16 |
| CQ08 | 4 |
| CQ09 | 8 |
| CQ10 | 16 |
| CQ11 | 222 |
| CQ12 | 12 |
| CQ13 | 41 |
| CQ14 | 16 |
| CQ15 | 9 |
| CQ16 | 8 |
| CQ17 | 1 |
| CQ18 | 15 |
| CQ19 | 2 |
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

## 4. Baseline Comparison

The direct LLM baseline comparison was refreshed against the latest prototype and completed graphs.

Reference file:

- `docs/baseline_comparison.md`

Headline results:

- `CQ04`: prototype `134`, completed `134`, delta `+0`
- `CQ11`: prototype `117`, completed `123`, delta `+6`
- `CQ12`: prototype `11`, completed `11`, delta `+0`
- `CQ16`: prototype `7`, completed `7`, delta `+0`
- `CQ18`: prototype `11`, completed `12`, delta `+1`

Interpretation:

- `CQ11` shows the clearest completion benefit, with 6 additional rows from `matchedToSourceRecord` links enabling cross-source traversal that the prototype graph cannot support.
- `CQ04`, `CQ12`, and `CQ16` show no delta, meaning the relevant triples were already present in the prototype before completion ran.
- A direct LLM answer cannot ground any of these results in the actual dataset.

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
