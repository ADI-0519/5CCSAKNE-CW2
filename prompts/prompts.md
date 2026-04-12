# Prompt Log

## P00: Initial Plan 
Task: Generate an overall plan then refine it. 

Prompts:
-hey gpt get yourself familiar with our coursework content. this group chat is mean to focus on this knowledge engineering course. Our plan is to work on current news, where we write a python script to use LLM for data extraction and normalization from data sources, producing suitable output for importing into our own ontology. Ideal pipeline will be: data sources -> Python + AI extraction -> validated JSON -> RDF/OWL generation -> upload/import into WebProtégé.
-Based on this and our coursework description, produce a plan on who should be working on what. For roles please check our coursework specification.
-wrtie me a concrete plan on the whole pipeline, so I can used to implement the code clearly
-We don't need Webprotege now, remove it from the plan
-implement the unfinished code based on this plan

Justification:
Moving our initial idea into a more concrete planning. Starting with the pipeline we discussed, giving it to AI for a concrete overall plan generation. Then, fine-tune it based on what we want and what we have. After that, modify it lively based on the change of situations. At the end, after putting initial pipeline and main.py, we asked AI to finish unfinished code part. All modification has been checked manually. 

Used for: Planning



## P01: Competency Question Augmentation
Task: Generate 10 additional competency questions that complement the manual set.

Prompts:
You are helping with a knowledge-engineering coursework on the domain of current news.
We already have 10 manually written competency questions for a news knowledge graph.
Generate 10 additional competency questions that:
- stay within the same domain
- are answerable from a KG built around articles, journalists, organisations, locations, technologies, topics, and publishers
- complement the manual questions instead of repeating them
- vary the query style, including counting, comparison, co-occurrence, and trend questions

Return the result as a numbered list.
For each question, add a one-line justification explaining what new information need it covers.

Justification:
# TODO: Add justification

Used for: `docs/competency_questions.md`



## P02: Ontology Review Against Reused Vocabularies
Task: Check the local ontology against Schema.org and BBC Core Concepts.

Prompts:
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

Justification:
# TODO: Add justification

Used for: `docs/mapping_specification.md` and the ontology/RDF alignment refactor.



## P03: Source-to-Ontology Mapping Draft
Task: Turn source fields and extracted entities into an explicit mapping specification.

Prompts:
Given a news API response with fields such as source.name, author, title, url, publishedAt,
description, content, plus extracted entities (organisation, person, location, technology, topic),
produce a mapping table from source data to ontology classes and properties.

Include:
- source field or extraction output
- ontology class or property
- expected RDF representation
- validation notes and ambiguity warnings

Justification:
# TODO: Add justification

Used for: `docs/mapping_specification.md`



## P04: Completion Analysis
Task: Identify incompleteness in both the ontology and the instance layer.

Analyse the current-news KG prototype and identify:
- at least 5 incomplete ontology elements
- at least 5 incomplete instance-level elements

For each item, explain:
- why it is incomplete
- how it affects competency-question coverage
- what additional retrieval or enrichment source could help complete it

Then propose a RAG-based completion workflow that constrains outputs to the ontology.

Justification:
# TODO: Add justification

Used for: `docs/completion_analysis.md`



## P05: Evaluation Methodology Design
Task: Define a quantitative evaluation strategy for the automated KG-construction pipeline.

Prompts:
Design an evaluation methodology for an automated current-news KG pipeline.
It should cover:
- performance metrics such as runtime, memory, and triples produced
- quality metrics for entity extraction, relation extraction, and competency-question coverage
- a comparison between SPARQL over the KG and direct prompting of an LLM
- what data should be sampled manually for annotation

Return the methodology as a concise, coursework-ready plan.

Justification:
# TODO: Add justification

Used for: `docs/evaluation_methodology.md`


## P06: Report Generation
Task: Generate Useful report draft then refine it.

Prompts:
-Read and understand my project. Then generate a complete report for it.
-Analysis this coursework description and modify the report based on it.
-Reduce the report from 25 pages to at most 8 pages, keep the important information.
-check again for this coursework description, make sure the report has everything that was required to be written in the report. Add and modify if there are things missing

Justification:
Start with a complete report which includes everything. Then modify the report based on the coureswork description. After that, reduce the page count to a reasonable number. At the end, double check with the missing information in the description. All content has been check manually.  

Used for: `/Report.tex`