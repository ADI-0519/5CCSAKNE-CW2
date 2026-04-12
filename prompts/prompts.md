# Prompt Log

This document records the prompts used in the project and the specific knowledge engineering task each one belongs to. Prompts are grouped into two categories: design-time prompts used during ontology and pipeline development, and runtime prompts executed programmatically by the pipeline during KG construction.

## Design-Time Prompts

These prompts were used during development to inform modelling decisions, generate competency questions, and plan evaluation. They were run manually through an LLM interface and their outputs were reviewed and edited before being incorporated into the project.

### P01: Competency Question Augmentation

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

### P02: Ontology Review Against Reused Vocabularies

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

### P03: Source-to-Ontology Mapping Draft

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

### P04: Completion Analysis

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

### P05: Evaluation Methodology Design

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

## Runtime Prompts

These prompts are executed programmatically by the pipeline during KG construction. They are defined in `src/openai_client.py` and sent to the OpenAI API with strict structured output schemas to ensure ontology-aligned responses. All responses are validated against the schema before being accepted into the graph, and cached locally to avoid repeated API calls.

### P06: LLM-Assisted Entity and Event Extraction

Task: Extract named entities, sentiment, article type, and events from article text to supplement heuristic extraction.

System instruction:

```text
You are an information extraction assistant for a knowledge graph about current UK
politics and policy news. Use only evidence from the supplied article. Do not invent
entities or events. Return only ontology-aligned JSON.
```

User input (JSON payload containing):

```json
{
  "project_scope": "Current UK politics and policy news from March 6, 2026 to April 6, 2026...",
  "allowed_topics": ["Defence", "Economic Policy", "Education", "Election", ...],
  "article": {
    "title": "...",
    "summary": "...",
    "content": "...",
    "section": "...",
    "tags": [],
    "published_at": "..."
  },
  "heuristic_result": { "...existing heuristic extraction output..." },
  "article_text": "...concatenated article text..."
}
```

Required response schema (strict mode, enforced by the OpenAI API):

```json
{
  "people": ["string"],
  "organizations": ["string"],
  "locations": ["string"],
  "topics": ["string"],
  "politicians": ["string"],
  "political_parties": ["string"],
  "government_bodies": ["string"],
  "sentiment": "Negative | Neutral | Positive",
  "article_type": "BreakingNewsArticle | NewsArticle | OpinionArticle",
  "events": [
    {
      "name": "string",
      "type": "EconomicEvent | NewsEvent | PoliticalEvent",
      "date": "string | null",
      "location": "string | null"
    }
  ]
}
```

The pipeline merges LLM outputs with heuristic results, preferring the LLM for sentiment and article type classification while combining entity lists. Only values that pass validation against the ontology are accepted.

Used for: `src/data_extraction.py` (extraction stage, called per article)

### P07: LLM-Assisted KG Completion

Task: Refine sentiment, section, article subtypes, and topic assignments for articles already in the knowledge graph.

System instruction:

```text
You are completing a UK politics and policy news knowledge graph. Use only the supplied
headline, description, and current KG context. Do not invent facts. Return only
JSON-compatible ontology-aligned updates.
```

User input (JSON payload containing):

```json
{
  "project_scope": "Current UK politics and policy news from March 6, 2026 to April 6, 2026...",
  "allowed_topics": ["Defence", "Economic Policy", "Education", "Election", ...],
  "article": {
    "headline": "...",
    "description": "...",
    "existing_topics": ["..."],
    "organizations": ["..."]
  },
  "heuristic_result": {
    "sentiment": "...",
    "section": "...",
    "article_types": ["..."],
    "additional_topics": ["..."]
  }
}
```

Required response schema (strict mode):

```json
{
  "sentiment": "Negative | Neutral | Positive",
  "section": "string",
  "article_types": ["BreakingNewsArticle | NewsArticle | OpinionArticle"],
  "additional_topics": ["string"]
}
```

Completion outputs are merged conservatively: sentiment overrides the heuristic only if valid, section is only set when not already present from the source, article types are unioned, and additional topics are filtered against the allowed topic vocabulary before being added.

Used for: `src/complete_kg.py` (completion/enrichment stage, called per article)
