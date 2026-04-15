# 5CCSAKNE Coursework 2

Knowledge Engineering coursework repository for building a knowledge graph from structured and unstructured data sources.

## Domain

Current UK politics and policy news, covering articles published between March 6, 2026 and April 6, 2026.

## Data Sources

- **Guardian API** (textual source): full article body text processed with NLP extraction (regex NER, keyword matching, LLM-assisted extraction)
- **Wikidata** (structured source): UK politicians, political parties, and government bodies queried via the public SPARQL endpoint and mapped directly to RDF
- **NewsAPI** (supplementary): structured metadata from additional UK news publishers

## Repository Structure

- `src/`: source code for ingestion, extraction, transformation, and KG construction
- `kg/`: generated Turtle outputs
- `ontology/`: ontology TBox file
- `queries/`: SPARQL queries answering the 20 competency questions
- `docs/`: competency questions, mapping specification, completion analysis, evaluation methodology
- `prompts/`: prompts used for competency questions, extraction, mapping, and completion tasks
- `tests/`: automated tests for the pipeline and validation logic
- `data/`: cached raw API snapshots and processed records (not committed; submitted separately)

## Getting Started

1. Create and activate a Python virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
pre-commit install
```

3. Copy `.env.example` to `.env` and fill in API keys (optional for cached runs):

```
GUARDIAN_API_KEY=...
NEWS_API_KEY=...
OPENAI_API_KEY=...
```

## Running the Pipeline

Use cached snapshots for a reproducible offline run (no API keys needed):

```bash
python -m src.main --from-cache
```

Run against live APIs:

```bash
python -m src.main
```

Skip the Wikidata collection stage:

```bash
python -m src.main --from-cache --skip-wikidata
```

Use a specific Wikidata snapshot:

```bash
python -m src.main --from-cache --wikidata-snapshot data/raw/wikidata/wikidata_entities.json
```

## Pipeline Stages

1. **Collect** — Fetch data from Guardian API, NewsAPI, and Wikidata SPARQL endpoint
2. **Normalise** — Convert Guardian and NewsAPI JSON into a shared article schema
3. **Extract** — Run NLP extraction (entities, topics, events, sentiment) over article text, supplemented by OpenAI
4. **Normalise extracted records** — Validate and clean extraction outputs
5. **Build ontology** — Programmatically construct the TBox (15 classes, 15 properties)
6. **Map news to RDF** — Convert extracted article records to RDF triples (textual source path)
7. **Map Wikidata to RDF** — Direct field-to-property mapping of structured data (no NLP)
8. **Merge** — Combine ontology, news instances, and Wikidata triples into a prototype KG
9. **Enrich** — Complete the KG with inferred sentiment, sections, topics, follow-up links
10. **Query** — Run 20 SPARQL competency queries against the completed KG

## Running Tests

```bash
python -m pytest
```

## Collaboration Rules

- Work through feature branches and open pull requests into `dev`.
- Keep `dev` as the integration branch during development.
- Merge `dev` into `main` only for the final coursework submission.
- Do not commit secrets or private datasets.
