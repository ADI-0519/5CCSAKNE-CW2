# 5CCSAKNE Coursework 2

Knowledge Engineering coursework repository for building a knowledge graph from structured and unstructured data sources.

## Repository Structure

- `kg/`: ontology files, mappings, generated triples, and final Turtle outputs
- `prompts/`: prompts used for competency questions, extraction, mapping, and completion tasks
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


## Collaboration Rules

- Work through feature branches and open pull requests into `main`.
- Keep prompts, mappings, and report artefacts versioned in the repository.
- Do not commit secrets or private datasets.
- Use the branch protection checklist in `.github/REPOSITORY_SETUP.md` after creating the GitHub repository.

## Coursework Deliverables

This repository is intended to hold:

- The knowledge graph Turtle files
- Data ingestion and mapping code
- Prompt logs and documentation
- Tests and validation queries
- Report-linked implementation artefacts
