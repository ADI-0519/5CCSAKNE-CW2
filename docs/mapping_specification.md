# Mapping Specification

This document records how the current pipeline maps source data into the local UK parliamentary and government policy event ontology.

Project scope:

`UK parliamentary and government policy events reported in UK news over a rolling 30-day collection window, using Guardian as the core textual reporting source, Parliament/Hansard and GOV.UK as official sources, optional Wikidata enrichment, and OpenAI for constrained extraction support where configured.`

The submitted cached snapshot covers 23 March 2026 to 22 April 2026 and is fixed for examiner reproducibility.

## Mapping Overview

The pipeline is multi-stage:

1. collect Guardian, Parliament, GOV.UK, and optional Wikidata data
2. normalise source payloads into common records
3. extract KG-ready event, actor, institution, topic, location, article, and source-record fields
4. build the ontology programmatically
5. convert KG-ready records to RDF
6. convert optional Wikidata records to RDF
7. merge ontology, source-derived instances, and enrichment triples into a prototype KG
8. complete the graph with inverse article-event links and source-record matches
9. run SPARQL competency queries

## Source Design

The coursework requires both textual and structured data. The current codebase satisfies this through complementary sources.

### Textual Source: Guardian API

Guardian is the core textual reporting source. The pipeline collects politics and policy articles with full body text and metadata.

Key fields:

- `webTitle`
- `webUrl`
- `webPublicationDate`
- `fields.headline`
- `fields.trailText`
- `fields.bodyText`
- `fields.byline`
- `fields.lastModified`
- `fields.wordcount`
- tags and sections

Guardian text is used for extraction of policy events, political actors, government bodies, policy topics, locations, authors, publishers, and article-event reporting links.

### Official Structured Source: UK Parliament / Hansard

The Parliament written-statements API provides official parliamentary source records. These are normalised into source records and can also produce policy-event evidence.

Mapped role:

- `news:SourceRecord`
- `news:OfficialSourceRecord`
- `news:ParliamentSourceRecord`
- `news:GovernmentPolicyEvent`
- `news:MinisterialStatement`
- `news:representedInOfficialSource`

### Official Structured Source: GOV.UK

The GOV.UK Search API provides government policy records, guidance, announcements, speeches, consultations, and press releases.

Mapped role:

- `news:SourceRecord`
- `news:OfficialSourceRecord`
- `news:GovernmentSourceRecord`
- `news:GovernmentPolicyEvent`
- `news:MinisterialStatement`
- `news:representedInOfficialSource`

### Optional Enrichment Source: Wikidata

Wikidata is queried through SPARQL for UK politicians, political parties, and government bodies. It is mapped directly to RDF without NLP.

Mapped role:

- enriches political actors, parties, government bodies, locations, and external identifiers
- provides structured background data through `rdfs:seeAlso`, `schema:name`, `schema:memberOf`, and related schema.org properties

## Normalised Record Fields

Collected source data is normalised before extraction and RDF conversion. The common fields include:

- `id`
- `source_system`
- `source_name`
- `title`
- `url`
- `published_at`
- `updated_at`
- `author`
- `section`
- `summary`
- `content`
- `tags`
- `word_count`
- `raw_article_type_hint`

Not every field is used in the core ontology. For the current event-centred TBox, the most important fields are `id`, `source_system`, `source_name`, `title`, `url`, `published_at`, `author`, `summary`, `content`, and extracted event/entity fields.

## Direct Metadata Mapping

| Source value | RDF representation | Ontology target | Status |
| --- | --- | --- | --- |
| record `id` | stable URI | `news:NewsArticle` and `news:SourceRecord` URI construction | Implemented |
| `title` | literal headline/name | `schema:headline`, `schema:name`, `news:sourceTitle` | Implemented |
| `url` | URL literal | `news:articleURL`, `schema:url` | Implemented |
| `published_at` | datetime literal | `news:publishedDate`, `schema:datePublished` | Implemented |
| `source_name` | publisher entity | `news:NewsOrganisation`, `news:publishedBy`, `schema:publisher` | Implemented |
| `author` | journalist entity | `news:Journalist`, `news:hasAuthor`, `schema:author` | Implemented |
| `source_system` | source-system literal | `news:sourceSystem` | Implemented |

## Source Record Mapping

Every normalised record with a source system is represented as a source record.

| Source system | RDF classes |
| --- | --- |
| `guardian` | `news:SourceRecord` |
| `parliament` / `hansard` | `news:SourceRecord`, `news:OfficialSourceRecord`, `news:ParliamentSourceRecord` |
| `govuk` / `gov.uk` | `news:SourceRecord`, `news:OfficialSourceRecord`, `news:GovernmentSourceRecord` |

Source-record datatype properties:

- `news:sourceIdentifier`
- `news:sourceTitle`
- `news:sourceSystem`

Official source records are linked to events using:

- `news:representedInOfficialSource`

Completion can add broader integration links using:

- `news:matchedToSourceRecord`

## Event Mapping

Event candidates are created from source records and extracted article evidence.

Mapped classes:

- `news:PolicyEvent`
- `news:ParliamentaryEvent`
- `news:GovernmentPolicyEvent`
- `news:ParliamentaryDebate`
- `news:MinisterialStatement`

Mapped properties:

- `schema:name`
- `news:occursOnDate`
- `news:reportedByArticle`
- `news:concernsPolicyTopic`
- `news:involvesActor`
- `news:involvesGovernmentBody`
- `news:issuedByDepartment`
- `news:occursInParliamentaryBody`
- `news:occursInLocation`
- `news:representedInOfficialSource`

The event-classification rules are implemented in `src/json_to_rdf.py`.

## Actor, Institution, Topic, And Location Mapping

| Extracted value | RDF class | Main links |
| --- | --- | --- |
| political actor | `news:PoliticalActor`, `schema:Person` | `news:involvesActor` |
| political party | `news:PoliticalParty` | `news:memberOfParty` |
| official body | `news:OfficialBody` | event institution links |
| government body | `news:GovernmentBody` | `news:involvesGovernmentBody` |
| government department | `news:GovernmentDepartment` | `news:involvesGovernmentBody`, `news:issuedByDepartment` |
| parliamentary body | `news:ParliamentaryBody` | `news:occursInParliamentaryBody` |
| policy topic | `news:PolicyTopic` | `news:concernsPolicyTopic` |
| location | `news:Location` | `news:occursInLocation` |

## Wikidata Mapping

Wikidata records follow a direct field-to-property mapping.

| Wikidata field | RDF representation | Status |
| --- | --- | --- |
| politician `name` | `news:PoliticalActor`, `schema:Person`, `schema:name` | Implemented |
| politician `party` | `news:PoliticalParty`, `news:memberOfParty` / `schema:memberOf` | Implemented |
| `constituency` | `news:Location`, `schema:name` | Implemented |
| `gender` | `schema:gender` | Implemented |
| `date_of_birth` | `schema:birthDate` | Implemented |
| party `name` | `news:PoliticalParty`, `schema:Organization`, `schema:name` | Implemented |
| `inception` | `schema:foundingDate` | Implemented |
| `dissolved` | `schema:dissolutionDate` | Implemented |
| `headquarters` | `schema:location` | Implemented |
| `leader` | `news:PoliticalActor`, `schema:name` | Implemented |
| government body `name` | `news:GovernmentBody`, `news:OfficialBody`, `schema:name` | Implemented |
| `wikidata_uri` | `rdfs:seeAlso` | Implemented |

## Completion Mapping

After the prototype graph is built, `src/complete_kg.py` enriches the graph.

Implemented completion mappings:

- for each `event news:reportedByArticle article`, add `article news:reportsOn event`
- for each event already linked through `news:representedInOfficialSource`, add the corresponding `news:matchedToSourceRecord` link
- for strong title/date/topic matches between events and official-source records, add `news:matchedToSourceRecord`
- for very strong official matches, add `news:representedInOfficialSource`
- for events missing actor, department, or topic links, retrieve the event's KG neighbourhood via SPARQL, verbalise it, and prompt OpenAI to propose `news:involvesActor`, `news:involvesGovernmentBody`, and `news:concernsPolicyTopic` values constrained to the ontology vocabulary; accepted proposals are validated by slug-term overlap with the retrieved context before writing

Current completion does not populate article sentiment, article follow-up chains, or article topic links. Those are outside the defended core ontology.

## External Ontology Alignment

| Local term | External alignment |
| --- | --- |
| `news:PolicyEvent` | `rdfs:subClassOf core:Event` |
| `news:Location` | `rdfs:subClassOf core:Place` |
| `news:NewsArticle` | `rdfs:subClassOf schema:NewsArticle` |
| `news:PoliticalActor` | `rdfs:subClassOf schema:Person` |
| `news:Journalist` | `rdfs:subClassOf schema:Person` |
| `news:PoliticalParty` | `rdfs:subClassOf schema:Organization` |
| `news:OfficialBody` | `rdfs:subClassOf schema:Organization` |
| `news:SourceRecord` | `rdfs:subClassOf schema:CreativeWork` |
| `news:concernsPolicyTopic` | `rdfs:subPropertyOf schema:about` |
| `news:occursInLocation` | `rdfs:subPropertyOf core:eventPlace` |
| `news:occursOnDate` | `rdfs:subPropertyOf core:startDate` |
| `news:memberOfParty` | `rdfs:subPropertyOf schema:memberOf` |
| `news:publishedBy` | `rdfs:subPropertyOf schema:publisher` |
| `news:hasAuthor` | `rdfs:subPropertyOf schema:author` |
| `news:publishedDate` | `rdfs:subPropertyOf schema:datePublished` |
| `news:articleURL` | `rdfs:subPropertyOf schema:url` |

## Key Modelling Notes

- The mapping is event-centred and official-source aware.
- Guardian is the main textual source, while Parliament and GOV.UK provide official source records.
- Wikidata enriches background political entities but is optional in the pipeline.
- Policy topics attach to events through `news:concernsPolicyTopic`.
- Cross-source integration is represented through `news:representedInOfficialSource` and `news:matchedToSourceRecord`.
- The RAG completion step adds actor, department, and topic links for events where those properties are missing, using retrieved KG context to constrain and validate proposals.
