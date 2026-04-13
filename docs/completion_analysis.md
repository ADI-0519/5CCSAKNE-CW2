# Completion Analysis

This document explains what remains incomplete in the UK politics and policy knowledge graph after the main extraction pipeline, what the current completion stage already does, and what still needs to be improved for the final coursework submission.

Project scope:

`A knowledge graph for current UK politics and policy news, using articles published between March 6, 2026 and April 6, 2026 from GuardianAPI and NewsAPI, with Wikidata as a structured data source and OpenAI used for extraction, classification, and completion.`

## Current Pipeline State

The current codebase now has three data paths feeding into the KG:

1. a textual extraction pipeline over normalised Guardian and NewsAPI article records (NLP-based)
2. a direct structured mapping from Wikidata entity records (no NLP)
3. a completion/enrichment stage over the merged prototype RDF graph

This means completion is no longer a purely theoretical stage. It is already implemented in the pipeline and runs after ontology construction, instance graph generation, and Wikidata integration.

### What the base extraction stage already adds (textual path)

The extraction pipeline over Guardian and NewsAPI articles currently produces:

- article instances with publication date, URL, author, publisher, section, summary, content, tags, and word count
- article subtype labels such as `news:NewsArticle`, `news:OpinionArticle`, and `news:BreakingNewsArticle`
- people, organisations, locations, and topics
- typed political actors where they can be recognised heuristically:
  - `news:Politician`
  - `news:PoliticalParty`
  - `news:GovernmentBody`
- sentiment labels
- event candidates with:
  - event name
  - event type
  - event date
  - event location
- follow-up candidates

The extraction stage is mainly heuristic, but it now also supports optional OpenAI-based extraction with a cached fallback. This means the project already uses AI in a structured and programmatic way rather than as a manual post-processing step.

### What the Wikidata structured mapping adds

The Wikidata collection and mapping stage queries the public Wikidata SPARQL endpoint and directly maps structured entity records to RDF without any NLP processing. This provides:

- UK politicians with party affiliation, constituency, gender, and date of birth
- political parties with founding date, dissolution date, headquarters, and leader
- government bodies with headquarters
- `rdfs:seeAlso` links back to Wikidata URIs for provenance

This substantially strengthens the KG's coverage of political actors, parties, and government bodies beyond what heuristic extraction from article text alone can achieve.

### What the completion stage already adds

The completion stage currently operates over the prototype KG and enriches it with:

- `news:hasSentiment`
- `news:hasSection`
- `news:wordCount`
- `news:hasUpdateTimestamp`
- additional topic assignments
- article subtype reinforcement
- inferred `news:hasFollowUp` links

This stage can also use OpenAI completion in a constrained JSON format, with local response caching, to refine heuristic outputs.

So the current system is best described as:

- extraction first
- RDF graph construction second
- graph completion/enrichment third

That is important because the remaining completion discussion should now focus on what is still missing after both extraction and enrichment, not after extraction alone.

## What Is Already Covered Well

The following parts of the ontology are now populated to a useful extent:

- `news:NewsArticle`
- `news:OpinionArticle`
- `news:BreakingNewsArticle`
- `news:Journalist`
- `news:NewsOrganisation`
- `news:Organisation`
- `news:Topic`
- `news:Location`
- `news:Sentiment`
- `news:NewsEvent`
- `news:PoliticalEvent`
- `news:EconomicEvent`

And the following properties are also materially populated:

- `news:hasAuthor`
- `news:publishedBy`
- `news:hasTopic`
- `news:mentionsPerson`
- `news:mentionsOrganisation`
- `news:mentionsLocation`
- `news:publishedDate`
- `news:hasUpdateTimestamp`
- `news:hasSection`
- `news:articleURL`
- `news:coversEvent`
- `news:eventDate`
- `news:eventLocation`
- `news:hasSentiment`
- `news:wordCount`
- `news:hasFollowUp`

This is a much richer state than the earlier prototype, where event modelling, typed political actors, and completion outputs were mostly absent.

## Remaining Incomplete Ontology Elements

The ontology is now largely aligned with the implemented pipeline, but a few important terms remain weakly populated or unpopulated.

`O1.` Event modelling exists, but event identity is still weak.

The system now creates event candidates and event triples, but many events are still generic or article-local rather than canonically resolved across multiple articles. This weakens questions that depend on multiple publishers covering the same event.

`O2.` `news:NewsEvent`, `news:PoliticalEvent`, and `news:EconomicEvent` are populated, but not yet strongly normalised.

The issue is no longer whether events exist at all. The real issue is whether event instances are specific, stable, and reusable enough for strong cross-article querying.

`O3.` Provenance and confidence are not modelled for completion outputs.

The current ontology and pipeline do not yet attach confidence scores, evidence spans, or source provenance to completion-generated assertions. This is especially relevant for AI-assisted extraction and enrichment.

`O4.` No inverse or symmetric properties are declared.

The ontology does not yet declare inverse properties (e.g. an inverse of `news:hasAuthor`) or mark symmetric relationships. This limits some advanced SPARQL reasoning patterns and would be needed for a production-grade ontology.

`O5.` `news:worksFor` affiliations are inferred per-article rather than canonically asserted.

The pipeline materialises `news:worksFor` triples whenever an author and publisher co-occur on an article, so the property is populated. However, affiliation is derived article-by-article rather than from a canonical journalist profile, which means a journalist who writes for multiple outlets would have multiple `worksFor` triples without temporal scoping or a primary affiliation marker.

## Remaining Incomplete Instance Elements

`I1.` Cross-source coverage is now multi-source but with different strengths.

The article corpus is Guardian-heavy because NewsAPI developer-tier access is restricted. However, the Wikidata structured source now provides broad coverage of UK politicians, political parties, and government bodies independently of article extraction. The KG draws from both textual and structured sources as required by the coursework.

`I2.` Political-actor typing is present but still incomplete for article-extracted mentions.

The Wikidata path now provides strong baseline coverage of politicians, parties, and government bodies through direct structured mapping. However, political actors mentioned in article text are still typed heuristically, and some actors extracted from articles will remain under generic person or organisation types when they cannot be matched to known entities.

`I3.` Event instances are present but still somewhat generic.

Some event nodes are still broad placeholders, such as policy-style events inferred from article language rather than clearly named canonical events. This makes event-based CQs only partially robust.

`I4.` Completion outputs are not yet evidence-grounded in storage.

OpenAI completion and heuristic completion can improve sentiment, section, article subtype, and topics, but the stored graph does not yet preserve why a given completion was accepted.

`I5.` Journalist identity is not deduplicated across sources.

The same journalist may appear under slightly different name forms (e.g. "Jessica Elgot" vs "Jessica Elgot and Rajeev Syal") and the pipeline creates separate person nodes for each variant. This weakens journalist-centric competency questions.

## Why These Remaining Gaps Matter

These gaps do not stop the system from producing a useful KG, but they weaken the more ambitious competency questions.

- CQs about politicians, parties, and government bodies are now much better supported than before, but still depend on the quality of heuristic or LLM-assisted typing.
- CQs about events across multiple publishers depend on better event identity resolution.
- CQs involving journalist affiliation are now supported via `news:worksFor` triples, but could be strengthened with canonical journalist profiles and name deduplication.
- CQs using sentiment and article subtype are now supported, but their quality still depends on heuristic or LLM classification accuracy.
- CQs involving follow-up links are now more realistic, but still heuristic rather than fully editorially grounded.

So the completion stage is no longer about making the KG minimally functional. It is now about improving quality, confidence, and semantic consistency.

## Practical Completion Strategy

The current codebase already implements a lightweight retrieve-generate-merge pattern. For the final submission, the completion strategy should be described as a constrained enrichment loop rather than a free-form chatbot step.

### 1. Retrieve

For each article or candidate entity, retrieve:

- the article headline, summary, and content
- source metadata such as section, author, publisher, tags, publication date, and update timestamp
- existing KG context:
  - people
  - organisations
  - locations
  - topics
  - event candidates

This gives the completion stage both textual evidence and structured graph context.

### 2. Generate

Use OpenAI to produce only ontology-compatible JSON outputs.

The current implementation already uses strict structured response formats for:

- extraction
- completion

The most valuable completion tasks are:

- refining sentiment when heuristic polarity is weak
- refining article subtype classification
- refining section assignment
- proposing additional topics
- later, extending this to stronger actor typing and event grounding

### 3. Validate

Before adding completions to the graph:

- reject values outside the ontology
- canonicalise labels and dates
- merge only recognised article types and sentiment values
- avoid overwriting strong source evidence with weaker generated guesses

This is already partly reflected in the current code, where OpenAI completion is merged into heuristic outputs only for allowed fields and allowed values.

### 4. Store

Accepted completions are currently merged directly into the enriched graph.

For a stronger final version, the project should either:

- keep completion outputs in a separate enrichment layer before merge, or
- attach completion provenance and confidence metadata

This is one of the clearest remaining areas for improvement.

## Recommended Completion Backlog

The most important remaining completion tasks are:

1. Deduplicate journalist names and consolidate `news:worksFor` into canonical affiliation triples.
2. Improve event grounding so the same real-world event is reused across related articles.
3. Extend OpenAI completion beyond section, sentiment, subtype, and extra topics into stronger political-actor and event refinement.
4. Add confidence or provenance tracking for completion-derived triples.
5. Evaluate completion quality on a small manually reviewed article sample.

## Final Assessment

The completion stage is now a real implemented component of the KG pipeline, not just a proposed extension.

That is a strong improvement over the earlier prototype. However, the most important remaining issue is no longer the existence of completion itself. The real issue is completion quality and traceability:

- how reliably political actors are typed
- how specific event instances are
- how well cross-article event identity is maintained
- how transparently AI-assisted enrichments are justified

So the final submission should present completion as:

- an implemented enrichment layer
- already useful for sentiment, section, subtype, topic expansion, and follow-up links
- but still improvable in event grounding, journalist affiliation, and provenance-aware AI enrichment
