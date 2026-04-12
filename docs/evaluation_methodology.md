# Evaluation Methodology

This document defines how the UK politics and policy knowledge graph should be evaluated in a way that matches the current codebase and pipeline.

Project scope:

`A knowledge graph for current UK politics and policy news, using articles published between March 6, 2026 and April 6, 2026 from GuardianAPI and NewsAPI, with OpenAI used for extraction, classification, and completion.`

The current pipeline now produces several distinct artefacts:

- a normalised article set
- extracted KG-ready records
- an ontology graph
- an instance graph
- a merged prototype KG
- a completed/enriched KG
- a query result set over the completed KG

So evaluation should no longer focus on only one generated graph. It should compare the system across stages, especially:

- the prototype KG before completion
- the completed KG after enrichment

## 1. Structural Correctness

Goal: confirm that the pipeline produces syntactically valid and structurally coherent outputs at each stage.

### What to check

- all JSON artefacts are generated successfully
- all Turtle outputs parse successfully
- ontology, prototype KG, and completed KG are all valid RDF graphs
- expected namespaces and ontology terms appear in the final graph
- the required article fields survive collection, normalisation, extraction, and RDF conversion

### Metrics

- JSON generation success rate
- Turtle parse success rate
- total triple count
- triples per article
- percentage of articles that retain required metadata:
  - title
  - URL
  - publication date
  - publisher
  - section
  - word count

### Evidence sources

- pipeline smoke tests
- normalisation tests
- RDF tests
- successful execution of the end-to-end pipeline in `src/main.py`

## 2. Competency-Question Coverage

Goal: measure how well the generated KG supports the final set of competency questions.

### Method

- use the final 20 competency questions as the evaluation target
- run the full SPARQL query set over the completed KG
- record whether each query:
  - executes successfully
  - returns meaningful rows
  - is only partially supported because the graph is incomplete or noisy

### Labels

Each CQ should be classified as:

- `answered`
- `partially answered`
- `unanswered`

### Metrics

- query parse success rate
- query execution success rate
- answerability rate on the prototype KG
- answerability rate on the completed KG
- improvement in answerability after completion

### Why this matters

This is the most important evaluation category for coursework quality because it connects:

- ontology design
- extraction quality
- completion quality
- SPARQL usefulness

## 3. Extraction And Classification Quality

Goal: assess how accurate the extraction stage is for the ontology elements that matter most to the final KG.

### Core extracted elements

- journalists/authors
- publishers
- people
- politicians
- organisations
- political parties
- government bodies
- locations
- topics
- article subtype
- sentiment
- event candidates

### Manual evaluation setup

- sample 30 to 50 articles from the fixed dataset
- include both Guardian and NewsAPI articles
- create a small gold sheet with the expected:
  - author
  - publisher
  - people
  - organisations
  - locations
  - topics
  - sentiment
  - article subtype
  - key events where obvious

If time is limited, priority should go to:

- political actors
- topics
- sentiment
- article subtype
- event candidates

### Metrics

- precision, recall, and F1 for people, organisations, locations, and topics
- classification accuracy for:
  - politicians
  - political parties
  - government bodies
  - sentiment
  - article subtype
- event extraction precision on the manually reviewed sample
- metadata accuracy for:
  - author
  - publisher
  - publication date
  - section
  - update timestamp
  - word count

### Practical note

The extraction layer is now partly heuristic and partly OpenAI-assisted. Evaluation should therefore describe whether errors are mostly caused by:

- heuristic over-generation
- weak event grounding
- incomplete actor typing
- poor LLM refinement

## 4. Completion Quality

Goal: determine whether the completion stage genuinely improves the graph.

The current completion stage already enriches the prototype KG with:

- sentiment
- section
- word count
- update timestamp
- additional topics
- article subtype reinforcement
- follow-up links

and it can optionally use OpenAI completion with cached structured outputs.

### Method

- compare prototype KG and completed KG on the same query set
- inspect a sample of completion-generated triples manually
- separate heuristic completions from OpenAI-assisted completions where possible

### Metrics

- number of completion triples added
- number of articles affected by completion
- percentage of completion triples that are ontology-compatible
- precision of sampled completion triples
- number of CQs improved after completion

### Important remaining quality questions

- are added topics relevant rather than over-broad?
- are subtype corrections sensible?
- are follow-up links meaningful?
- does OpenAI completion improve quality or merely add noise?

## 5. Cross-Source Evaluation

Goal: show that the system genuinely works across more than one source and identify source-specific weaknesses.

### Method

- compare Guardian and NewsAPI records after normalisation and extraction
- compare the kinds of metadata available from each
- compare whether one source produces cleaner entities or more useful topics/events

### Metrics

- number of articles collected per source
- number of usable articles per source after normalisation
- coverage of key fields by source:
  - author
  - section
  - summary
  - content
  - tags
  - word count
- extraction quality by source on the manual sample

### Important context

NewsAPI developer-tier limits restrict retrieval to the first 100 results in the project window. This should be treated as a documented data-source limitation rather than as a pipeline failure.

## 6. Performance And Reproducibility

Goal: quantify runtime cost and show that the system can be rerun consistently.

### Metrics

- end-to-end runtime of `src/main.py`
- runtime of each major stage:
  - collection
  - normalisation
  - extraction
  - ontology build
  - RDF conversion
  - completion
  - query execution
- number of articles processed
- total triples generated
- triples per article

### Reproducibility checks

- confirm that raw snapshots are saved under `data/raw`
- confirm that processed JSON artefacts are saved under `data/processed`
- confirm that the same cached raw snapshots can be reused with offline mode
- confirm that OpenAI outputs can be cached and reused rather than recomputed every run

This is especially important because the coursework values automation and reproducibility, not just a one-off demonstration.

## 7. Baseline Comparison With Direct LLM Answers

Goal: compare KG-based answering with direct LLM answering on a smaller subset of questions.

### Method

- select 5 to 10 representative competency questions
- answer them directly from the article texts with the LLM
- compare those answers with SPARQL results over the completed KG

### Comparison criteria

- factual grounding
- traceability to source metadata
- reproducibility
- consistency of answer format
- ease of auditing

### Expected conclusion

The KG plus SPARQL approach should be more reproducible and structurally auditable, while direct LLM answers may be more fluent but less transparent.

## 8. Minimum Tables And Figures To Produce

The final evaluation section should include at least:

- a CQ support table for all 20 competency questions
- a prototype-KG versus completed-KG comparison table
- a manual quality-audit table for the sampled articles
- a per-source article-count table
- a runtime and triple-count table

## Final Evaluation Position

The current project is now advanced enough that evaluation should not be framed as "does the pipeline run at all?".

The more important questions are:

- how accurate is the extraction?
- how much does completion improve the graph?
- how many competency questions are genuinely answerable?
- how reproducible is the pipeline under API and model constraints?

That framing is much closer to the actual maturity of the codebase and much stronger for the final submission.
