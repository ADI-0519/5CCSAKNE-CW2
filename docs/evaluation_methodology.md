# Evaluation Methodology

This evaluation plan is intended for the current-news KG prototype and should be used in the final report once the remaining ingestion and completion work is finished.

## 1. Structural Correctness

Goal: ensure the KG is well-formed and conforms to the ontology design.

Metrics:

- Turtle parse success rate: percentage of generated Turtle files that parse without error.
- Predicate conformance: percentage of extracted relations using the controlled predicate set.
- Ontology coverage: percentage of generated triples that use local ontology classes or properties rather than falling back to generic terms only.
- Required-field validation pass rate: percentage of records surviving normalisation without missing title, URL, publication date, or source.

Evidence:

- CI logs
- unit and contract tests
- count of triples by namespace

## 2. Extraction and Mapping Quality

Goal: measure how accurate the automated KG-construction pipeline is.

Metrics:

- Entity precision, recall, and F1 for organisations, people, locations, technologies, and topics.
- Relation precision, recall, and F1 for `news:hasAuthor`, `news:publishedBy`, `news:mentionsOrganisation`, `news:mentionsTechnology`, `news:mentionsLocation`, `news:hasTopic`, and `news:usesTechnology`.
- Normalisation accuracy for URL validity, date canonicalisation, and duplicate removal.

Recommended annotation setup:

- Sample 50 to 100 articles.
- Create a gold annotation sheet for entities and relations.
- Score the pipeline output against the gold set.

## 3. Competency-Question Coverage

Goal: determine whether the KG answers the 20 competency questions.

Metrics:

- Query execution rate: percentage of the 20 SPARQL queries that run without errors.
- Query answerability rate: percentage of the 20 queries returning meaningful answers on a representative dataset.
- Manual relevance score: for each query, judge whether the returned answers actually satisfy the associated competency question.

Procedure:

- Run all 20 SPARQL queries over the latest KG.
- Record whether each query returns empty results because of modelling gaps, extraction gaps, or genuine absence of evidence.
- Summarise which competency questions remain unsupported.

## 4. Performance

Goal: quantify the cost of automated KG construction.

Metrics:

- End-to-end runtime per pipeline execution.
- Runtime per stage: collection, extraction, normalisation, RDF conversion, and save.
- Peak memory usage during pipeline execution.
- Number of triples produced per article.

Recommended procedure:

- Run the pipeline on at least three batches of different sizes.
- Record the median runtime and peak memory.
- Report both total cost and per-article cost.

## 5. Baseline Comparison

Goal: compare KG-based answering against direct prompting of an LLM.

Baselines:

- Direct LLM answers to a subset of the 20 competency questions.
- The same questions answered via SPARQL over the KG.

Comparison criteria:

- factual grounding
- answer completeness
- reproducibility
- response format consistency

Expected outcome:

- SPARQL over the KG should be more traceable and easier to verify.
- Direct LLM prompting may be broader but less reproducible and less source-grounded.

## 6. Reporting Format

For the report, include:

- the metric definitions
- the sample sizes
- the annotation procedure
- the results table
- the key failure modes
- the actions taken after evaluation
