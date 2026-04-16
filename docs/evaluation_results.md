## Evaluation Results

This document records a concrete evaluation snapshot for the latest validated pipeline run.

Evaluated run:

- `20260415T205507Z`

Primary artefacts:

- [20260415T205507Z_kg_records.json](data/processed/20260415T205507Z_kg_records.json)
- [20260415T205507Z_completed_kg.ttl](output/20260415T205507Z_completed_kg.ttl)
- [20260415T205507Z_query_results.json](output/20260415T205507Z_query_results.json)

## 1. Structural Results

- Total KG-ready records: `264`
- Source split:
  - `261` Guardian
  - `3` NewsAPI
- Article subtype split: see kg_records.json
- Records with event candidates: see kg_records.json

Generated graph counts:

- Instance KG: `32547` triples
- Wikidata KG: `24307` triples
- Prototype KG: `56573` triples
- Completed KG: `56998` triples
- Wikidata entities: `1722` politicians, `964` parties, `489` government bodies

Structural judgment:

- The pipeline completed successfully with all three data sources.
- The ontology, instance graph, prototype KG, completed KG, and query result outputs were all generated.
- The current ontology, RDF output, and SPARQL layer are internally aligned on `news:eventDate` as `xsd:date`.
- The collection window is dynamically computed as the 30 days prior to the run date, ensuring the pipeline remains reproducible without hardcoded date constraints.

## 2. Competency Question Results

All `20/20` competency queries returned at least one row in the latest run.

| CQ | Row count |
| --- | --- |
| CQ01 | 132 |
| CQ02 | 2 |
| CQ03 | 2261 |
| CQ04 | 547 |
| CQ05 | 212 |
| CQ06 | 12 |
| CQ07 | 14 |
| CQ08 | 254 |
| CQ09 | 2 |
| CQ10 | 378 |
| CQ11 | 15 |
| CQ12 | 26 |
| CQ13 | 394 |
| CQ14 | 246 |
| CQ15 | 259 |
| CQ16 | 2 |
| CQ17 | 36755 |
| CQ18 | 50 |
| CQ19 | 5 |
| CQ20 | 1269 |

Important judgments:

- `CQ02` now returns two publishers: The Guardian and one NewsAPI source, confirming multi-source coverage.
- `CQ16` similarly returns two publishers with distinct topic ranges.
- `CQ17` and `CQ20` are highly combinatorial ranking queries — result counts reflect the full cross-product of co-mentions and should be interpreted as ranked lists rather than absolute counts.
- `CQ19` returns five events covered by more than one article, confirming the event layer is populated and functional.
- `CQ10` follow-up link counts reflect heuristic matching and should be treated as approximate.

## 3. Manual Audit Snapshot

A stratified audit sample was taken from the latest run across:

- `NewsArticle`
- `OpinionArticle`
- `BreakingNewsArticle`
- all retained NewsAPI articles

### Strengths

- Core metadata is generally preserved correctly from source to KG:
  - title
  - publisher
  - publication date
  - URL
  - section
- Political topics are often sensible for clearly political reporting.
- Event canonicalisation improved cross-publisher event grouping enough to support `CQ19`.
- Source filtering removed many previously off-scope NewsAPI publishers.
- Wikidata entity typing correctly classifies political parties and government bodies, enabling CQ04, CQ05, and CQ20.

### Weaknesses

- Person and organisation extraction still over-generates in some cases.
- Some location extraction is clearly noisy.
- Some event labels remain too generic or synthetic.
- Follow-up links improved substantially but are still heuristic.
- A small amount of off-scope or weakly related NewsAPI material still remains.

Concrete examples from the sample:

1. `Rachel Reeves rules out universal support on energy bills`
   Good overall topic fit, but extracted people include suspicious names such as `Markets Authority`.

2. `Senior Labour figures warn government amid fears of 'political earthquake' in London`
   Election/event structure is useful, but people and location lists contain noisy labels like `London Exclusive` and `Deltapoll`.

3. `UK has detained 76 'age-disputed' children under one in, one out scheme`
   Correctly captures immigration focus, but event extraction includes an arguably spurious `Election` event.

4. `Pressure mounts on UK government to ban Kanye West after Wireless Festival backlash`
   Useful for showing that cross-source policy-event coverage now exists, but it is still only weakly political and should be described honestly as borderline scope.

5. `Trump endorses ex-UK political aide Steve Hilton for California governor`
   Retains a relevant `Election` event, but the article is still only indirectly about UK politics.

## 4. Evaluation Position For The Report

The strongest defensible evaluation claim is:

- the system works end to end
- the ontology and query layer are aligned
- all competency questions are executable and return results
- the graph is most reliable for metadata, publisher/author information, broad topics, article subtype, sentiment, and major political/economic event groupings
- the graph is less reliable for fine-grained entity precision, weakly grounded events, and follow-up-link semantics

This should be framed as a successful automated KG pipeline with identifiable heuristic limitations, not as a perfect information-extraction system.

## 5. What Still Needs To Be Added

To complete the evaluation section properly, the team should still add:

- a manually annotated audit sheet using the sample in [manual_audit_template.csv](data/evaluation/manual_audit_template.csv)
- a short table comparing prototype KG versus completed KG triple counts
- performance metrics: pipeline execution time and memory usage

## 6. Recommended Final Framing

If space is tight, the final report should emphasise:

1. automation and reproducibility
2. ontology-to-pipeline alignment
3. measurable CQ support
4. honest error analysis on sampled articles
5. the fact that OpenAI is used in a constrained, cached, structured way rather than as an opaque one-off assistant