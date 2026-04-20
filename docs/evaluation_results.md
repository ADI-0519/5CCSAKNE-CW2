# Evaluation Results

This document records the latest validated evaluation snapshot for the current pipeline.

Evaluated run:

- `20260420T130554Z`

Primary artefacts:

- `data/processed/20260420T130554Z_normalised_articles.json`
- `data/processed/20260420T130554Z_extracted_articles.json`
- `data/processed/20260420T130554Z_kg_records.json`
- `output/20260420T130554Z_instance_kg.ttl`
- `output/20260420T130554Z_wikidata_kg.ttl`
- `output/20260420T130554Z_prototype_kg.ttl`
- `output/20260420T130554Z_completed_kg.ttl`
- `output/20260420T130554Z_query_results.json`

## 1. Structural Results

The pipeline completed all stages successfully.

Source records:

- Guardian records: `253`
- Parliament records: `20`
- GOV.UK records: `100`
- Combined normalised records: `373`

Wikidata enrichment:

- Politicians: `1719`
- Political parties: `967`
- Government bodies: `490`

Generated graph counts:

- Ontology graph: `190` triples
- Source-derived instance KG: `7443` triples
- Wikidata KG: `24950` triples
- Prototype KG: `32380` triples
- Completed KG: `32453` triples

Completion additions:

- `51` `news:reportsOn` inverse links
- `22` `news:matchedToSourceRecord` links
- total delta from prototype to completed KG: `73` triples

Structural judgment:

- The pipeline is runnable end to end from live APIs.
- Raw source snapshots, processed JSON artefacts, generated Turtle files, and query results are all saved.
- The ontology, source-derived RDF, Wikidata RDF, prototype KG, completed KG, and SPARQL queries are aligned around the event-centred vocabulary.
- The final graph supports the current competency-question set without relying on the older article-centric sentiment or follow-up vocabulary.

## 2. Competency Question Results

All `20/20` competency queries returned at least one row in the latest run.

| CQ | Row count |
| --- | ---: |
| CQ01 | 21 |
| CQ02 | 4 |
| CQ03 | 11 |
| CQ04 | 22 |
| CQ05 | 6 |
| CQ06 | 7 |
| CQ07 | 7 |
| CQ08 | 4 |
| CQ09 | 50 |
| CQ10 | 12 |
| CQ11 | 1 |
| CQ12 | 2 |
| CQ13 | 39 |
| CQ14 | 1 |
| CQ15 | 2 |
| CQ16 | 8 |
| CQ17 | 5 |
| CQ18 | 11 |
| CQ19 | 3 |
| CQ20 | 3 |

Important judgments:

- `CQ04` confirms that reported policy events can also be represented in official Parliament or GOV.UK source records.
- `CQ12` confirms that matched source-record provenance is populated after completion.
- `CQ14` now answers a comparative coverage question over parliamentary versus government policy events rather than relying on the old article-analytics vocabulary.
- `CQ17` and `CQ20` exercise multi-hop chains from publishers or journalists through articles to policy events and government departments.
- `CQ09` intentionally exposes missing links, so a non-zero result is useful for incompleteness analysis rather than a failure.

## 3. Evaluation Position

The strongest defensible evaluation claim is:

- the pipeline runs end to end
- the ontology and RDF generation are aligned with the current CQ set
- the completed graph answers all 20 competency queries
- official-source records are integrated into the KG rather than only stored as raw data
- the completion stage improves navigability and provenance through `reportsOn` and `matchedToSourceRecord`

The graph is strongest for:

- event-to-topic links
- event-to-institution links
- event-to-source-record links
- article-to-event reporting links
- publisher and journalist metadata
- official source provenance

The graph is weaker for:

- canonical event identity across multiple articles
- complete political-actor disambiguation
- recall of cross-source event matches
- provenance metadata explaining why a completion link was accepted

## 4. Recommended Final Framing

The final report should frame the system as a working automated KG pipeline with an event-centred ontology. It should avoid old claims about supplementary news-source coverage, sentiment analysis, article subtype classification, or follow-up links as core graph outputs.

If RAG is added later, it should be evaluated separately and described as an extension to the current completion stage, not retroactively treated as part of this evaluated run.
