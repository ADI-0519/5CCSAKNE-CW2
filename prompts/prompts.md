# Prompt Log

## P01: Competency Question Augmentation
Task: Generate 10 additional competency questions that complement the manual set.

```text
You are helping with a knowledge-engineering coursework on the domain of current news.
We already have 10 manually written competency questions for a news knowledge graph.
Generate 10 additional competency questions that:
- stay within the same domain
- are answerable from a KG built around articles, journalists, organisations, locations, technologies, topics, and publishers
- complement the manual questions instead of repeating them
- vary the query style, including counting, comparison, co-occurrence, and trend questions

Return the result as a numbered list.
For each question, add a one-line justification explaining what new information need it covers.
```

Used for: `docs/competency_questions.md`

## P02: Ontology Review Against Reused Vocabularies
Task: Check the local ontology against Schema.org and BBC Core Concepts.

```text
Review this ontology draft for a current-news knowledge graph.
The ontology reuses Schema.org and BBC Core Concepts.

Identify:
1. classes that should be aligned more explicitly
2. properties that should become typed subproperties rather than generic relations
3. missing modelling distinctions between publishers and mentioned organisations
4. any class or property defined in the ontology but not represented in the generated RDF

Return:
- concrete modelling issues
- a revised alignment proposal
- the minimum code changes needed in the RDF generation step
```

Used for: `docs/mapping_specification.md` and the ontology/RDF alignment refactor.

## P03: Source-to-Ontology Mapping Draft
Task: Turn source fields and extracted entities into an explicit mapping specification.

```text
Given a news API response with fields such as source.name, author, title, url, publishedAt,
description, content, plus extracted entities (organisation, person, location, technology, topic),
produce a mapping table from source data to ontology classes and properties.

Include:
- source field or extraction output
- ontology class or property
- expected RDF representation
- validation notes and ambiguity warnings
```

Used for: `docs/mapping_specification.md`

## P04: Completion Analysis
Task: Identify incompleteness in both the ontology and the instance layer.

```text
Analyse the current-news KG prototype and identify:
- at least 5 incomplete ontology elements
- at least 5 incomplete instance-level elements

For each item, explain:
- why it is incomplete
- how it affects competency-question coverage
- what additional retrieval or enrichment source could help complete it

Then propose a RAG-based completion workflow that constrains outputs to the ontology.
```

Used for: `docs/completion_analysis.md`

## P05: Evaluation Methodology Design
Task: Define a quantitative evaluation strategy for the automated KG-construction pipeline.

```text
Design an evaluation methodology for an automated current-news KG pipeline.
It should cover:
- performance metrics such as runtime, memory, and triples produced
- quality metrics for entity extraction, relation extraction, and competency-question coverage
- a comparison between SPARQL over the KG and direct prompting of an LLM
- what data should be sampled manually for annotation

Return the methodology as a concise, coursework-ready plan.
```

Used for: `docs/evaluation_methodology.md`
