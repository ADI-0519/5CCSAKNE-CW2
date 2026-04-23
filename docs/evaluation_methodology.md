# Evaluation Methodology

This document defines how the current UK parliamentary and government policy event KG should be evaluated.

Project scope:

`UK parliamentary and government policy events reported in UK news over a rolling 30-day collection window, using Guardian as the core textual reporting source, Parliament/Hansard and GOV.UK as official sources, optional Wikidata enrichment, and OpenAI for constrained extraction support where configured.`

The submitted cached snapshot covers 23 March 2026 to 22 April 2026 and is fixed for examiner reproducibility.

The pipeline produces these artefacts:

- raw source snapshots under `data/raw/`
- normalised source records
- extracted KG-ready records
- ontology graph in `ontology/news_ontology.ttl`
- source-derived instance KG
- optional Wikidata enrichment KG
- merged prototype KG
- completed/enriched KG
- SPARQL query results over the completed KG

## 1. Structural Correctness

Goal: confirm that every generated artefact is syntactically valid and aligned with the current ontology.

Checks:

- all JSON artefacts are generated
- all Turtle outputs parse as RDF graphs
- expected namespaces appear in the final graph
- the ontology declares the classes and properties used by the RDF pipeline
- source records are typed as `news:SourceRecord`, `news:ParliamentSourceRecord`, or `news:GovernmentSourceRecord`
- policy events carry dates, topics, article links, and institution links where source evidence supports them

Metrics:

- total records by source
- total triples by graph stage
- number of ontology triples
- number of policy events
- number of official source records
- number of completed graph links added

Evidence sources:

- `python -m src.main`
- `python -m pytest`
- `kg/generated/*.ttl`
- `output/*_query_results.json`
- `output/rag_evaluation.json`

## 2. Competency-Question Coverage

Goal: measure whether the generated KG supports the final 20 competency questions.

Method:

- run `queries/news_competency_queries.rq` against `kg/generated/completed_kg.ttl`
- record whether each query executes successfully
- record row counts
- classify whether each result is clean, noisy, or diagnostic

Metrics:

- query parse success rate
- query execution success rate
- number of queries returning at least one row
- row counts per CQ
- whether completion improves answerability for source-matching CQs

Latest validated result:

- `20/20` current queries returned at least one row against the completed KG from run `20260423T121805Z`

## 3. Extraction And Mapping Quality

Goal: assess how accurately the pipeline maps source evidence into ontology terms.

Core elements to inspect:

- article metadata: title, URL, publication date, publisher, author
- source records: identifier, title, system, source subclass
- event classes: `PolicyEvent`, `ParliamentaryEvent`, `GovernmentPolicyEvent`, `ParliamentaryDebate`, `MinisterialStatement`
- actors: `PoliticalActor`
- institutions: `OfficialBody`, `GovernmentBody`, `GovernmentDepartment`, `ParliamentaryBody`
- topics: `PolicyTopic`
- places: `Location`
- links: `reportedByArticle`, `representedInOfficialSource`, `matchedToSourceRecord`, `concernsPolicyTopic`, `involvesGovernmentBody`

Manual audit setup:

- sample records across Guardian, Parliament, and GOV.UK
- check whether event labels, dates, topics, and institution links are plausible
- check whether official-source records are represented accurately
- check whether article-event links reflect the article headline and content
- inspect a subset of `matchedToSourceRecord` links for false positives

Recommended metrics:

- metadata accuracy
- event-type precision
- topic precision
- institution-link precision
- official-source match precision
- number of missing source or modelling links found by CQ09 and source-integration audits

## 4. Completion Quality

Goal: determine whether graph enrichment improves queryability without adding unsupported assertions.

The current completion stage adds:

- `news:reportsOn` inverse links from existing `news:reportedByArticle` triples
- `news:matchedToSourceRecord` links for official-source matching
- occasional additional `news:representedInOfficialSource` links when a match score is strong enough
- `news:involvesActor`, `news:involvesGovernmentBody`, and `news:concernsPolicyTopic` links via an LLM-assisted RAG step for events missing those properties

Method:

- compare prototype KG and completed KG triple counts
- count completion-added links
- run the CQ suite against the completed KG
- manually inspect a sample of matched source records

Latest validated result:

- prototype KG: `38596` triples
- completed KG: `39101` triples
- completion delta: `505` triples
- `reportsOn` links added: `194`
- `matchedToSourceRecord` links added: `157`

Important quality questions:

- are matched source records from the correct source system?
- do source-record titles support the event they are matched to?
- do completion-added source matches improve provenance without inflating false matches?
- what is the precision of RAG-added actor, department, and topic triples? (auditable via `output/rag_evaluation.json`)

## 5. Cross-Source Evaluation

Goal: show that the system integrates textual reporting and official structured sources.

Sources to compare:

- Guardian: textual news reporting source
- Parliament/Hansard: official parliamentary source records
- GOV.UK: official government policy source records
- Wikidata: optional structured enrichment for political background entities

Metrics:

- number of records by source
- number of official source records represented in RDF
- number of events linked to official source records
- number of events matched to source records after completion
- number of publishers and articles reporting policy events

Latest validated source counts:

- Guardian: `270`
- Parliament: `20`
- GOV.UK: `410`
- Wikidata: `1724` politicians, `968` parties, `489` government bodies

## 6. Performance And Reproducibility

Goal: show that the pipeline can be rerun and audited.

Checks:

- live run works with configured API keys
- cached run works with `python -m src.main --from-cache`
- raw snapshots are saved under `data/raw/`
- processed JSON files are saved under `data/processed/`
- generated KGs are saved under `kg/generated/` and `output/`
- query results are saved in `output/query_results.json` and timestamped files

Metrics:

- end-to-end runtime
- total records processed
- total triples generated
- query coverage
- test pass count

## 7. LLM Baseline Comparison

Goal: illustrate the difference between KG-backed SPARQL answers and direct LLM answers on a small subset of competency questions.

This is an illustrative contrast, not a controlled evaluation. The LLM answers from training knowledge without any constraint to the same 700 collected records or the same date window. A discrepancy between a SPARQL row count and an LLM answer could reflect KG incompleteness, LLM hallucination, or simply a different scope of knowledge, so it is not straightforwardly interpretable as one being more correct than the other.

Method:

- choose 5 representative CQs
- ask an LLM to answer from training knowledge
- compare the structure and grounding of those answers with SPARQL results

Comparison criteria:

- reproducibility
- source traceability
- consistency of answer format
- ease of auditing
- failure modes

Framing:

The KG/SPARQL approach produces answers that are grounded in and traceable to the collected dataset. Direct LLM answers may be fluent but cannot be tied to a specific record, triple, or source document.

## Final Evaluation Position

The project should be evaluated as a working automated KG pipeline, not as a one-off manual graph. The strongest evidence is the successful live run, valid generated RDF artefacts, deterministic completion delta, passing tests, and `20/20` competency-query coverage.
