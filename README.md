# 5CCSAKNE Coursework 2

Knowledge Engineering coursework repository for building a knowledge graph from structured and unstructured data sources.

## Repository Structure

- `kg/`: ontology files, mappings, generated triples, and final Turtle outputs
- `docs/`: coursework-ready modelling artefacts such as competency questions and evaluation notes
- `prompts/`: prompts used for competency questions, extraction, mapping, and completion tasks
- `queries/`: SPARQL queries answering the competency questions
- `src/`: source code for ingestion, extraction, transformation, and KG construction
- `tests/`: automated tests for the pipeline and validation logic
- `.github/`: CI, templates, and repository governance files

## Getting Started

1. Create and activate a Python virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
pre-commit install
```

## Running the Pipeline

Use cached raw JSON snapshots for a reproducible offline run:

```bash
.venv/bin/python -m src.main --from-cache
```

Run against the live GuardianAPI and NewsAPI sources:

```bash
.venv/bin/python -m src.main
```

Live API mode reads `NEWS_API_KEY` and `GUARDIAN_API_KEY` from `.env` or the shell environment. By default, live runs save new raw snapshots under `data/raw`.

To run from specific cached snapshots:

```bash
.venv/bin/python -m src.main --from-cache \
  --newsapi-snapshot data/raw/newsapi/20260407T122854Z.json \
  --guardian-snapshot data/raw/guardian/20260407T122859Z.json
```

To run live collection without writing new raw snapshots:

```bash
.venv/bin/python -m src.main --no-save-snapshots
```


## Collaboration Rules

- Work through feature branches and open pull requests into `dev`.
- Keep `dev` as the integration branch during development.
- Merge `dev` into `main` only for the final coursework submission or release.
- Keep prompts, mappings, and report artefacts versioned in the repository.
- Do not commit secrets or private datasets.
- Use the pull request template, CODEOWNERS review assignments, and CI checks in `.github/` before merging.

## Coursework Deliverables

This repository is intended to hold:

- The knowledge graph Turtle files
- Data ingestion and mapping code
- Competency questions and SPARQL query sets
- Prompt logs and documentation
- Completion and evaluation notes
- Tests and validation queries
- Report-linked implementation artefacts
