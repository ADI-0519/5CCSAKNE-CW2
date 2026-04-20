# 5CCSAKNE Coursework 2

Knowledge Engineering coursework repository for building a knowledge graph from structured and unstructured data sources.

## Domain

Current UK politics and policy news, covering articles published between March 6, 2026 and April 6, 2026.

## Data Sources

- **Guardian API** (textual source): UK politics and policy reporting, including full article text used for extraction.
- **UK Parliament / Hansard written statements API** (official structured source): parliamentary source records used to ground policy events.
- **GOV.UK Search API** (official structured source): government policy, guidance, announcement, speech, consultation, and press-release records.
- **Wikidata** (optional enrichment source): UK politicians, political parties, and government bodies queried through SPARQL and mapped directly to RDF.

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
OPENAI_API_KEY=...
```

Parliament, GOV.UK, and Wikidata do not require API keys for the current pipeline.

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

1. **Collect** — Fetch Guardian articles, Parliament written statements, GOV.UK records, and optional Wikidata enrichment records.
2. **Normalise** — Convert source payloads into a shared record format with source-system metadata.
3. **Extract** — Create KG-ready policy-event records from text and official-source metadata, with OpenAI used only as constrained extraction support where configured.
4. **Normalise extracted records** — Validate and clean extracted event, actor, institution, topic, location, article, and source-record fields.
5. **Build ontology** — Programmatically construct the event-centred TBox in `ontology/news_ontology.ttl`.
6. **Map source records to RDF** — Convert KG-ready records into article, policy-event, institution, topic, location, and source-record triples.
7. **Map Wikidata to RDF** — Directly map structured Wikidata entities to RDF, without NLP.
8. **Merge** — Combine ontology, source-derived instances, and optional Wikidata triples into `kg/generated/prototype_kg.ttl`.
9. **Enrich** — Add graph-level links such as `news:reportsOn` inverses and `news:matchedToSourceRecord` cross-source matches.
10. **Query** — Run 20 SPARQL competency queries against `kg/generated/completed_kg.ttl`.

## Running Tests

```bash
python -m pytest
```

## Collaboration Rules

- Work through feature branches and open pull requests into `dev`.
- Keep `dev` as the integration branch during development.
- Merge `dev` into `main` only for the final coursework submission.
- Do not commit secrets or private datasets.
