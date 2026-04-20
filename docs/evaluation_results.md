# Evaluation Results

This document records the latest validated evaluation snapshot for the current pipeline.

Evaluated run:

- `20260420T202251Z`

Primary artefacts:

- `data/processed/20260420T202251Z_normalised_articles.json`
- `data/processed/20260420T202251Z_extracted_articles.json`
- `data/processed/20260420T202251Z_kg_records.json`
- `output/20260420T202251Z_instance_kg.ttl`
- `output/20260420T202251Z_wikidata_kg.ttl`
- `output/20260420T202251Z_prototype_kg.ttl`
- `output/20260420T202251Z_completed_kg.ttl`
- `output/20260420T202251Z_query_results.json`

## 1. Structural Results

The pipeline completed all stages successfully.

Source records:

- Guardian records: `253`
- Parliament records: `20`
- GOV.UK records: `459`
- Combined normalised records: `732`

Wikidata enrichment:

- Politicians: `1730`
- Political parties: `968`
- Government bodies: `490`

Generated graph counts:

- Ontology graph: `188` triples
- Source-derived instance KG: `14429` triples
- Wikidata KG: `25064` triples
- Prototype KG: `39545` triples
- Completed KG: `40049` triples

Completion additions:

- `266` `news:reportsOn` inverse links
- `238` `news:matchedToSourceRecord` links
- total delta from prototype to completed KG: `504` triples

Structural judgment:

- The pipeline is runnable end to end from live APIs.
- Raw source snapshots, processed JSON artefacts, generated Turtle files, and query results are all saved.
- The ontology, source-derived RDF, Wikidata RDF, prototype KG, completed KG, and SPARQL queries are aligned around the event-centred vocabulary.
- The final graph supports the current competency-question set without relying on the older article-centric sentiment or follow-up vocabulary.

## 2. Competency Question Results

All `20/20` competency queries returned at least one row when the current query set was run against the completed KG from this snapshot.

| CQ | Row count |
| --- | ---: |
| CQ01 | 15 |
| CQ02 | 25 |
| CQ03 | 11 |
| CQ04 | 233 |
| CQ05 | 3 |
| CQ06 | 4 |
| CQ07 | 8 |
| CQ08 | 4 |
| CQ09 | 193 |
| CQ10 | 12 |
| CQ11 | 81 |
| CQ12 | 11 |
| CQ13 | 48 |
| CQ14 | 12 |
| CQ15 | 7 |
| CQ16 | 8 |
| CQ17 | 11 |
| CQ18 | 11 |
| CQ19 | 1 |
| CQ20 | 8 |

Important judgments:

- `CQ04` confirms that reported policy events can also be represented in official Parliament or GOV.UK source records.
- `CQ11` and `CQ12` confirm that official source records support institution and topic queries.
- `CQ14` now answers a comparative coverage question over parliamentary versus government policy events rather than relying on the old article-analytics vocabulary.
- `CQ17` and `CQ20` exercise multi-hop chains from journalists or departments through articles, policy events, and policy topics.
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

Cache-mode verification:

- `python -m src.main --from-cache` was run against the saved raw snapshots.
- Cached run timestamp: `20260420T202251Z`
- The cached run used the saved Guardian, Parliament, GOV.UK, Wikidata, and OpenAI extraction cache artefacts and reproduced `20/20` query coverage with the same graph counts.
