# Evaluation Methodology

This evaluation plan is for the fixed-scope UK politics and policy news KG:

`A knowledge graph for current UK politics and policy news, using articles published between March 1, 2026 and April 6, 2026 from GuardianAPI and NewsAPI, with OpenAI used for extraction, classification, and completion.`

The evaluation should compare:

- the base KG produced by [main.py](/home/kasim/5CCSAKNE-CW2/src/main.py)
- the enriched KG produced by [complete_kg.py](/home/kasim/5CCSAKNE-CW2/src/complete_kg.py)

## 1. Structural Correctness

Goal: confirm that the KG is valid RDF and remains aligned with the ontology.

Metrics:

- Turtle parse success rate.
- Number of generated triples.
- Triples per article.
- Namespace conformance: percentage of application-specific triples using `news:` terms.
- Required field pass rate after normalisation.

Evidence:

- unit tests
- ontology tests
- RDF conversion tests
- successful parsing of `news_ontology.ttl`, `new_kg.ttl`, and `completed_kg.ttl`

## 2. Competency-Question Coverage

Goal: measure how well the current KG supports the 20 final competency questions.

Method:

- Use the CQ coverage table in [cq_coverage_table.md](/home/kasim/5CCSAKNE-CW2/docs/cq_coverage_table.md) as the baseline expectation.
- Run all 20 SPARQL queries over the base KG and again over the completed KG.
- For each CQ, label the result as `answered`, `partially answered`, or `unanswered`.
- Record whether failure is caused by missing ontology population, weak extraction quality, or genuine absence of evidence.

Metrics:

- Query parse success rate.
- Query execution success rate.
- Answerability rate on the base KG.
- Answerability rate on the completed KG.
- Improvement in answerability after completion.

## 3. Extraction And Classification Quality

Goal: assess the quality of the current extraction pipeline for the entities and metadata that matter to the final ontology.

Priority entity and metadata types:

- journalists
- publishers
- people
- organisations
- locations
- topics
- section labels
- article update timestamps

Planned advanced types:

- politicians
- political parties
- government bodies
- political events
- economic events
- sentiment
- article subtype

Recommended annotation setup:

- Sample 30 to 50 articles from the fixed dataset.
- Create a small gold sheet with expected people, organisations, locations, topics, and key article metadata.
- For the completion layer, separately annotate sentiment, subtype, and follow-up on a smaller subset if time is limited.

Metrics:

- Entity precision, recall, and F1 for people, organisations, locations, and topics.
- Metadata accuracy for author, publisher, section, publication date, update timestamp, and word count.
- Classification accuracy for sentiment, article subtype, and any later political-actor typing.

## 4. Completion Quality

Goal: evaluate whether completion actually improves the KG rather than just adding noisy triples.

Method:

- Compare the base KG and completed KG on the same CQ/query set.
- Manually inspect a sample of completion-generated triples.
- Track which completions are heuristic and which later become LLM-assisted.

Metrics:

- Number of completion triples added.
- Percentage of completion triples that pass ontology validation.
- Precision of sampled completion triples.
- Number of previously unsupported or partially supported CQs improved by completion.

## 5. Performance

Goal: quantify the runtime cost of the pipeline.

Metrics:

- End-to-end runtime of `main.py`.
- End-to-end runtime of `complete_kg.py`.
- Runtime per stage: collection, extraction, normalisation, RDF generation, completion.
- Number of articles successfully processed.
- Triples generated per article.

Recommended procedure:

- Run the pipeline at least three times on the fixed window.
- Report median runtime.
- Record article counts and triple counts for each run.
- Note when NewsAPI returns plan-related restrictions for the fixed date window.

## 6. Baseline Comparison

Goal: compare KG-based answers with direct LLM answers.

Method:

- Select 5 to 10 representative CQs.
- Ask the LLM to answer them directly from the same source material.
- Compare those answers with SPARQL results over the KG.

Comparison criteria:

- factual grounding
- reproducibility
- traceability back to article metadata
- consistency of answer format

Expected conclusion:

- KG plus SPARQL should be more reproducible and easier to audit.
- Direct LLM answers may be broader, but they will be less structurally grounded.

## 7. Minimum Results Tables To Produce

The final evaluation write-up should include:

- a CQ support table for all 20 questions
- a base-KG versus completed-KG comparison table
- a small manual quality audit table
- a runtime and triple-count table
