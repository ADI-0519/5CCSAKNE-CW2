# Final Ontology Plan

This document records the implemented target ontology for the current coursework pipeline.

Project scope:

`UK parliamentary and government policy events reported in UK news during 23 March 2026 to 22 April 2026, using Guardian as the core textual reporting source, Parliament/Hansard and GOV.UK as official sources, optional Wikidata enrichment, and OpenAI for constrained extraction support where configured.`

The ontology is event-centred. It is not a general all-news ontology and does not treat article analytics such as sentiment or follow-up chains as part of the defended core TBox.

## 1. Design Principles

The ontology is designed to:

- represent policy events rather than only articles
- distinguish parliamentary events from government policy events
- link events to political actors, departments, parliamentary bodies, policy topics, locations, and source records
- keep source provenance visible through `news:SourceRecord`
- reuse external ontology terms through subclasses and subproperties
- support all 20 competency questions in `docs/competency_questions.md`
- be generated programmatically by `src/build_ontology.py`

## 2. Reused Ontologies

The ontology reuses:

- `schema.org` for articles, people, organisations, publishers, dates, URLs, names, and membership links
- BBC Core Concepts for event and place alignment

Examples:

- `news:NewsArticle rdfs:subClassOf schema:NewsArticle`
- `news:PoliticalActor rdfs:subClassOf schema:Person`
- `news:OfficialBody rdfs:subClassOf schema:Organization`
- `news:PolicyEvent rdfs:subClassOf core:Event`
- `news:Location rdfs:subClassOf core:Place`
- `news:publishedBy rdfs:subPropertyOf schema:publisher`
- `news:hasAuthor rdfs:subPropertyOf schema:author`
- `news:memberOfParty rdfs:subPropertyOf schema:memberOf`
- `news:occursInLocation rdfs:subPropertyOf core:eventPlace`

## 3. Implemented Classes

Event layer:

- `news:PolicyEvent`
- `news:ParliamentaryEvent`
- `news:GovernmentPolicyEvent`
- `news:ParliamentaryDebate`
- `news:MinisterialStatement`

Actor and institution layer:

- `news:PoliticalActor`
- `news:PoliticalParty`
- `news:OfficialBody`
- `news:GovernmentBody`
- `news:GovernmentDepartment`
- `news:ParliamentaryBody`

Topic and place layer:

- `news:PolicyTopic`
- `news:Location`

Reporting and provenance layer:

- `news:NewsArticle`
- `news:NewsOrganisation`
- `news:Journalist`
- `news:SourceRecord`
- `news:OfficialSourceRecord`
- `news:ParliamentSourceRecord`
- `news:GovernmentSourceRecord`

## 4. Implemented Object Properties

- `news:concernsPolicyTopic`: event to policy topic
- `news:involvesActor`: event to political actor
- `news:involvesGovernmentBody`: event to government body
- `news:issuedByDepartment`: ministerial statement to issuing department
- `news:occursInParliamentaryBody`: parliamentary event to parliamentary body
- `news:occursInLocation`: event to location
- `news:memberOfParty`: political actor to political party
- `news:reportedByArticle`: event to reporting article
- `news:reportsOn`: article to reported event, inverse of `news:reportedByArticle`
- `news:publishedBy`: article to news organisation
- `news:hasAuthor`: article to journalist
- `news:representedInOfficialSource`: event to official source record
- `news:matchedToSourceRecord`: event to aligned source record

## 5. Implemented Datatype Properties

- `news:occursOnDate`: event date, range `xsd:date`
- `news:publishedDate`: article publication timestamp, range `xsd:dateTime`
- `news:articleURL`: article URL, range `xsd:anyURI`
- `news:sourceIdentifier`: source-record identifier, range `xsd:string`
- `news:sourceTitle`: source-record title, range `xsd:string`
- `news:sourceSystem`: source system name, range `xsd:string`

## 6. Why OfficialBody Exists

`news:OfficialBody` is the broad public-institution class. It keeps the model semantically cleaner than making parliamentary bodies subclasses of executive government bodies.

The hierarchy is:

- `news:OfficialBody`
- `news:GovernmentBody rdfs:subClassOf news:OfficialBody`
- `news:GovernmentDepartment rdfs:subClassOf news:GovernmentBody`
- `news:ParliamentaryBody rdfs:subClassOf news:OfficialBody`

This supports Parliament and GOV.UK sources without conflating Parliament with executive government.

## 7. Terms Deliberately Left Out Of The Core Ontology

The defended core ontology does not currently include:

- `news:hasSentiment`
- `news:hasTopic`
- `news:hasFollowUp`
- `news:OpinionArticle`
- `news:BreakingNewsArticle`
- article section/update timestamp properties

Those terms belong to an article-analytics or future enrichment layer, not the current event-centred TBox. The implemented pipeline now attaches topics to events through `news:concernsPolicyTopic`, not to articles through `news:hasTopic`.

## 8. Coursework Requirement Coverage

The implemented ontology satisfies the extension requirement through multiple subclasses and subproperties.

Subclass examples:

- `news:PolicyEvent rdfs:subClassOf core:Event`
- `news:Location rdfs:subClassOf core:Place`
- `news:NewsArticle rdfs:subClassOf schema:NewsArticle`
- `news:PoliticalActor rdfs:subClassOf schema:Person`
- `news:OfficialBody rdfs:subClassOf schema:Organization`
- `news:GovernmentDepartment rdfs:subClassOf news:GovernmentBody`
- `news:ParliamentaryBody rdfs:subClassOf news:OfficialBody`

Subproperty examples:

- `news:concernsPolicyTopic rdfs:subPropertyOf schema:about`
- `news:issuedByDepartment rdfs:subPropertyOf news:involvesGovernmentBody`
- `news:occursInLocation rdfs:subPropertyOf core:eventPlace`
- `news:memberOfParty rdfs:subPropertyOf schema:memberOf`
- `news:publishedBy rdfs:subPropertyOf schema:publisher`
- `news:hasAuthor rdfs:subPropertyOf schema:author`
- `news:publishedDate rdfs:subPropertyOf schema:datePublished`
- `news:articleURL rdfs:subPropertyOf schema:url`

## 9. Relationship To The Pipeline

The ontology is generated by `src/build_ontology.py` and written to `ontology/news_ontology.ttl` during Stage 5 of `python -m src.main`.

The instance pipeline then uses the same vocabulary:

- `src/json_to_rdf.py` creates article, event, topic, institution, actor, location, and source-record triples
- `src/wikidata_to_rdf.py` maps optional structured Wikidata data into compatible entity triples
- `src/complete_kg.py` adds graph-level inverse and source-matching links
- `queries/news_competency_queries.rq` queries the completed graph using this vocabulary

## 10. Future Extensions

Future work may add:

- richer provenance for completion links
- confidence scores or evidence spans
- stronger entity resolution between article-extracted actors and Wikidata entities
- a separate article-analytics module if sentiment, follow-up chains, or article subtypes become required again

Those extensions should remain separate from the core event ontology unless new competency questions explicitly require them.
