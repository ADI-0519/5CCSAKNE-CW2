# Competency Questions

This document captures the 20 competency questions for the current-news KG. The first 10 were written manually. The second 10 were added through LLM-assisted augmentation and then refined to match the ontology and expected query scope.

Each question has a corresponding SPARQL query in `queries/news_competency_queries.rq`.

## Manual Competency Questions

`CQ01.` Which articles mention a target technology such as `AI` or `Robotics`?

`CQ02.` Which organisations are mentioned in articles about a target technology?

`CQ03.` Which journalists authored articles that mention a target organisation?

`CQ04.` Which publishers have published articles about a target topic?

`CQ05.` Which locations are mentioned in articles about a target technology?

`CQ06.` Which technologies are associated with a target organisation through the `news:usesTechnology` relation?

`CQ07.` Which articles mention the same organisation together with multiple technologies?

`CQ08.` Which people are mentioned most often in articles about a target topic?

`CQ09.` Which publishers cover the widest range of topics?

`CQ10.` Which topics co-occur most often with a target technology?

## LLM-Augmented Competency Questions

`CQ11.` Which articles mention both a target technology and a target location?

`CQ12.` Which publishers mention the same organisation across multiple articles?

`CQ13.` Which journalists write most often about a target technology?

`CQ14.` Which locations are most frequently discussed within a target topic?

`CQ15.` Which organisations appear in articles published by more than one publisher?

`CQ16.` Which technologies appear together in the same article?

`CQ17.` Which people and organisations co-occur in the same articles?

`CQ18.` Which articles are tagged with more than one topic?

`CQ19.` Which publishers mention the highest number of unique organisations?

`CQ20.` Which topics have the highest number of articles overall?

## Scope Notes

- The current prototype can already answer article, publisher, author, organisation, technology, topic, and location questions.
- Event-centric questions were deliberately deferred because `news:NewsEvent` is modelled in the ontology but not yet populated by the extraction pipeline.
- Future competency-question iterations should add questions once structured-source ingestion and completion work are in place.
