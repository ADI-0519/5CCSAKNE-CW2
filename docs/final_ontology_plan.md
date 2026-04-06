# Final Ontology Plan

This document defines the recommended target ontology for Coursework 2 after narrowing the project scope to:

`Current UK politics and policy news from March 1, 2026 to April 6, 2026, collected from GuardianAPI and NewsAPI, with OpenAI used for extraction, classification, and completion.`

This plan is designed to maximize marks by aligning the ontology with:

- the coursework brief
- the competency-question requirement
- the lecturer clarifications on ontology extension and automation
- the practical constraints of the current codebase

It should be treated as the target ontology for the project, not just a description of the current prototype.

## 1. High-Mark Design Rules

For this coursework,we wanted to satisfy these criteria:

- It matches the chosen scope precisely.
- It reuses existing ontologies clearly and explicitly.
- It introduces well-justified local extensions.
- It supports the competency questions directly.
- It can be populated by the pipeline or explicitly discussed as incomplete in the completion analysis.
- It is implemented and extended programmatically in the final production workflow.

And should distinguish between:

- conceptual ontology design and evaluation, where Protégé/WebProtégé may still be useful
- production and final implementation, where mappings, extensions, and triple generation should be automated through scripts or structured prompts

## 2. What “Extension” Means in This Coursework

Based on the lecturer guidance, ontology extension in CW2 means:

- identify at least two existing ontologies relevant to the domain
- define your local ontology terms
- explicitly connect your local terms to external terms
- create at least:
  - two subclasses
  - two subproperties
- produce these mappings programmatically in RDF or through structured LLM-assisted generation

Examples:

- `news:NewsArticle rdfs:subClassOf schema:NewsArticle`
- `news:Location rdfs:subClassOf core:Place`
- `news:publishedBy rdfs:subPropertyOf schema:publisher`
- `news:eventLocation rdfs:subPropertyOf core:eventPlace`

## 3. Reused Ontologies

The primary reused ontologies should be:

- `schema.org`
- `BBC Core Concepts`

Optional later extension:

- `PROV-O` for provenance of extraction and completion

Why these are strong choices:

- `schema.org` gives well-known web semantics for articles, publishers, authors, sections, and URLs
- `BBC Core Concepts` gives a clear event/place layer suitable for news event modelling
- both are easy to justify in the report

## 4. Final Domain Focus

The ontology should represent a knowledge graph for:

- current UK politics
- current UK public policy
- government and parliamentary activity
- public-affairs events in the chosen date window

This means the ontology should emphasize:

- articles
- journalists
- publishers
- politicians
- political parties
- government bodies
- topics
- locations
- events
- sentiment
- follow-up article structure

It should not drift into a broad generic “all news” or “tech news” ontology.

## 5. Recommended Classes

### 5.1 Article Classes

- `news:NewsArticle`
  - Main class for all news articles in the KG.
  - `rdfs:subClassOf schema:NewsArticle`

- `news:BreakingNewsArticle`
  - Articles classified as breaking news.
  - `rdfs:subClassOf news:NewsArticle`

- `news:OpinionArticle`
  - Editorials, opinion columns, commentary pieces.
  - `rdfs:subClassOf news:NewsArticle`

### 5.2 Person Classes

- `news:Journalist`
  - A person credited as the author of an article.
  - `rdfs:subClassOf schema:Person`

- `news:Politician`
  - A political actor such as an MP, minister, mayor, party leader, or other political office holder.
  - `rdfs:subClassOf schema:Person`

### 5.3 Organisation Classes

- `news:Organisation`
  - General organisation mentioned in reporting.
  - `rdfs:subClassOf schema:Organization`

- `news:NewsOrganisation`
  - A media organisation or publisher.
  - `rdfs:subClassOf news:Organisation`

- `news:PoliticalParty`
  - A UK political party or political grouping.
  - `rdfs:subClassOf news:Organisation`

- `news:GovernmentBody`
  - A ministry, department, regulator, parliament-related body, or public institution.
  - `rdfs:subClassOf news:Organisation`

### 5.4 Topic and Place Classes

- `news:Topic`
  - A policy or news theme such as taxation, migration, NHS, education, housing, energy, defence.
  - `rdfs:subClassOf schema:Thing`

- `news:Location`
  - Geographic place mentioned in news reporting.
  - `rdfs:subClassOf core:Place`

### 5.5 Event Classes

- `news:NewsEvent`
  - A real-world event covered by one or more articles.
  - `rdfs:subClassOf core:Event`

- `news:PoliticalEvent`
  - Elections, debates, parliamentary votes, speeches, cabinet announcements, party leadership events, protests, legislation-related events.
  - `rdfs:subClassOf news:NewsEvent`

- `news:EconomicEvent`
  - Budget announcements, fiscal statements, inflation-related announcements, tax policy updates, spending reviews.
  - `rdfs:subClassOf news:NewsEvent`

### 5.6 Sentiment Class

- `news:Sentiment`
  - A controlled sentiment classification used for article analysis.

Recommended named individuals:

- `news:Positive`
- `news:Negative`
- `news:Neutral`

## 6. Recommended Properties

### 6.1 Article Metadata Properties

- `news:hasAuthor`
  - Links an article to a journalist.
  - `rdfs:subPropertyOf schema:author`

- `news:publishedBy`
  - Links an article to its publisher.
  - `rdfs:subPropertyOf schema:publisher`

- `news:publishedDate`
  - Publication date/time of an article.
  - `rdfs:subPropertyOf schema:datePublished`

- `news:hasUpdateTimestamp`
  - Last known update timestamp of an article.
  - `rdfs:subPropertyOf schema:dateModified`

- `news:hasSection`
  - Editorial section such as politics, opinion, or UK news.
  - `rdfs:subPropertyOf schema:articleSection`

- `news:articleURL`
  - Canonical article URL.
  - `rdfs:subPropertyOf schema:url`

- `news:wordCount`
  - Number of words in the article representation.

### 6.2 Mention and Topic Properties

- `news:hasTopic`
  - Links an article to a topic.
  - `rdfs:subPropertyOf schema:about`

- `news:mentionsPerson`
  - Links an article to a person mentioned in its content.
  - `rdfs:subPropertyOf schema:mentions`

- `news:mentionsOrganisation`
  - Links an article to an organisation mentioned in its content.
  - `rdfs:subPropertyOf schema:mentions`

- `news:mentionsLocation`
  - Links an article to a location mentioned in its content.
  - `rdfs:subPropertyOf schema:mentions`

### 6.3 Analytical Properties

- `news:hasSentiment`
  - Links an article to a sentiment class.

- `news:hasFollowUp`
  - Links an article to a later follow-up article on the same story.

### 6.4 Professional Affiliation Property

- `news:worksFor`
  - Links a journalist to a news organisation.
  - `rdfs:subPropertyOf schema:worksFor`

### 6.5 Event Properties

- `news:coversEvent`
  - Links an article to an event it covers.
  - `rdfs:subPropertyOf core:notablyAssociatedWith`

- `news:eventDate`
  - Date or dateTime of the event.
  - `rdfs:subPropertyOf core:startDate`

- `news:eventLocation`
  - Links an event to a place.
  - `rdfs:subPropertyOf core:eventPlace`

## 7. Recommended Domains and Ranges

These should stay simple, sensible, and query-friendly.

- `news:hasAuthor`
  - domain: `news:NewsArticle`
  - range: `news:Journalist`

- `news:publishedBy`
  - domain: `news:NewsArticle`
  - range: `news:NewsOrganisation`

- `news:publishedDate`
  - domain: `news:NewsArticle`
  - range: `xsd:dateTime`

- `news:hasUpdateTimestamp`
  - domain: `news:NewsArticle`
  - range: `xsd:dateTime`

- `news:hasSection`
  - domain: `news:NewsArticle`
  - range: `xsd:string`

- `news:articleURL`
  - domain: `news:NewsArticle`
  - range: `xsd:anyURI`

- `news:wordCount`
  - domain: `news:NewsArticle`
  - range: `xsd:integer`

- `news:hasTopic`
  - domain: `news:NewsArticle`
  - range: `news:Topic`

- `news:mentionsPerson`
  - domain: `news:NewsArticle`
  - range: `schema:Person`

- `news:mentionsOrganisation`
  - domain: `news:NewsArticle`
  - range: `news:Organisation`

- `news:mentionsLocation`
  - domain: `news:NewsArticle`
  - range: `news:Location`

- `news:hasSentiment`
  - domain: `news:NewsArticle`
  - range: `news:Sentiment`

- `news:hasFollowUp`
  - domain: `news:NewsArticle`
  - range: `news:NewsArticle`

- `news:worksFor`
  - domain: `news:Journalist`
  - range: `news:NewsOrganisation`

- `news:coversEvent`
  - domain: `news:NewsArticle`
  - range: `news:NewsEvent`

- `news:eventDate`
  - domain: `news:NewsEvent`
  - range: `xsd:dateTime`

- `news:eventLocation`
  - domain: `news:NewsEvent`
  - range: `news:Location`

## 8. Coursework Requirement Coverage

This ontology plan is deliberately structured to satisfy the ontology-related marking points strongly.

### 8.1 Classes and Properties

It gives:

- a clear domain-specific class hierarchy
- a disciplined property set
- strong links to likely competency questions

### 8.2 Extensions

It clearly exceeds the minimum requirement for:

- subclasses
- subproperties

Examples of subclass extension:

- `news:NewsArticle rdfs:subClassOf schema:NewsArticle`
- `news:Journalist rdfs:subClassOf schema:Person`
- `news:Organisation rdfs:subClassOf schema:Organization`
- `news:Location rdfs:subClassOf core:Place`
- `news:NewsEvent rdfs:subClassOf core:Event`

Examples of subproperty extension:

- `news:hasAuthor rdfs:subPropertyOf schema:author`
- `news:publishedBy rdfs:subPropertyOf schema:publisher`
- `news:hasTopic rdfs:subPropertyOf schema:about`
- `news:mentionsPerson rdfs:subPropertyOf schema:mentions`
- `news:eventLocation rdfs:subPropertyOf core:eventPlace`
- `news:eventDate rdfs:subPropertyOf core:startDate`

## 9. What Should Not Be in the Final Ontology

To maximise marks, we will avoid ontology drift.

Unless your final CQ set or data pipeline truly needs them, deprioritize or remove:

- generic tech-news classes and properties
- very broad innovation/product relations
- loosely justified generic associations that are hard to populate or explain

In practice, that means the current generic-news ontology should likely drop or reduce emphasis on:

- `Technology`
- `mentionsTechnology`
- `usesTechnology`
- `developedBy`
- `announced`
- `involvedIn`
- `partOf`
- `NaturalDisasterEvent`

These are not bad modelling ideas in general, but they are weaker for this narrowed UK politics/policy scope.

## 10. What Must Be Covered by Competency Questions

For the ontology to score well, the CQ set should collectively cover:

- article authorship
- article publishers
- article dates
- article sections
- article updates
- article word counts
- topics
- person mentions
- organisation mentions
- location mentions
- event coverage
- event dates
- event locations
- journalist affiliation
- sentiment
- follow-up links
- article subclasses

If a class or property is important in the ontology, it should:

- appear in at least one competency question, or
- be explicitly discussed as incomplete in the completion analysis

## 11. Relationship to the Pipeline

The ontology should not be reduced to match the current weak prototype exactly.

Instead, it should represent:

- the intended final system
- the concepts required by the competency questions
- the concepts that the pipeline can plausibly populate through:
  - API metadata
  - text extraction
  - structured prompts
  - completion/RAG

This means some terms may be:

- populated immediately
- populated later in the pipeline
- partially populated and discussed in completion analysis

That is acceptable and academically strong, provided it is clearly documented.

## 12. Automation Requirement

This ontology may be designed and inspected in Protégé/WebProtégé, but the final implementation should show that:

- ontology extensions are represented in RDF/Turtle
- mappings to reused ontologies are generated or maintained programmatically
- instance generation is automated
- data integration from sources is automated

Your final documentation should explicitly explain:

- which parts were automated
- which parts remained manual
- why any remaining manual work could not be reasonably automated

## 13. Reproducibility Requirement

The lecturer guidance strongly suggests keeping local copies of the data.

So the final workflow should aim to include:

- locally saved GuardianAPI JSON snapshots
- locally saved NewsAPI JSON snapshots
- cleaned/normalized JSON used by the RDF pipeline

This improves:

- reproducibility
- marking reliability
- stability if the APIs change or fail


## 14. Final Recommendation

This ontology is the best current target because it is:

- narrower than generic news
- richer than a weak metadata-only schema
- directly reusable in code
- strong enough for high marks
- well aligned with the lecturer's clarifications on semantic extension and automation

It should now become the source of truth for:

- the ontology rewrite
- the competency-question rewrite
- the SPARQL rewrite
- the mapping documentation
- the completion analysis
