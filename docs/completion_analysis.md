# Completion Analysis

This document captures the main incompleteness issues already visible in the prototype and suggests a RAG-based strategy for completing them.

## Incomplete Ontology Elements

`O1.` `news:NewsEvent` is modelled but no events are currently extracted or instantiated.

`O2.` `news:BreakingNewsArticle` and `news:OpinionArticle` exist but articles are not classified into these subclasses.

`O3.` `news:hasSentiment` and the sentiment individuals exist but no sentiment values are populated.

`O4.` `news:hasFollowUp` exists but no inter-article continuity or follow-up relation is generated.

`O5.` `news:developedBy`, `news:announced`, `news:involvedIn`, and `news:partOf` are available in the ontology but are not yet extracted from the data.

## Incomplete Instance Elements

`I1.` Publisher entities are represented only by their display names and are not linked to canonical identifiers or websites.

`I2.` Journalist instances are name-based only and do not resolve ambiguity across name variants or duplicate names.

`I3.` Location instances are plain labels and are not grounded to canonical geographic resources such as countries, regions, or external identifiers.

`I4.` Technology instances are keyword-based and do not distinguish between aliases, model families, and broader technology categories.

`I5.` Topic instances are flat labels and do not yet support hierarchy, broader themes, or controlled vocabularies.

## Why These Gaps Matter

- Several competency questions depend on richer cross-article and cross-source identity resolution.
- Event, sentiment, and follow-up modelling are required to move beyond simple mention graphs.
- Completion quality directly affects whether the KG can answer analytical questions instead of only lookup questions.

## RAG-Based Completion Strategy

### Retrieval Stage

- Retrieve the original article text and metadata for the article being enriched.
- Retrieve supporting context from a second source such as a structured API, publisher metadata, or an external knowledge base.
- Retrieve ontology constraints so the completion step knows the allowed classes and properties.

### Generation Stage

- Ask the LLM to propose only triples that use the local ontology.
- Require the LLM to cite the retrieved evidence span for each proposed triple.
- Restrict outputs to a JSON or tabular intermediate form before RDF conversion.

### Validation Stage

- Reject any triple using a property outside the controlled set.
- Check that entity types and property ranges are consistent with the ontology.
- Keep low-confidence triples separate from high-confidence triples.

### Priority Completion Backlog

1. Add canonical grounding for publishers, journalists, locations, and technologies.
2. Add event extraction so `news:NewsEvent`, `news:eventDate`, and `news:eventLocation` become populated.
3. Add article classification for breaking news and opinion.
4. Add sentiment extraction with validation.
5. Add follow-up detection across article clusters.
