# Mapping Specification

This document records the current source-to-ontology mapping for the fixed coursework scope:

`A knowledge graph for current UK politics and policy news, using articles published between March 6, 2026 and April 6, 2026 from GuardianAPI and NewsAPI, with OpenAI used for extraction, classification, and completion.`

## Source Design

The project uses the two APIs in a unified way:

- `Textual source data`: article title, summary, and content/snippet from GuardianAPI and NewsAPI.
- `Structured source data`: publisher name, publication date, update timestamp, section, tags, URL, author/byline, and word count metadata from the same APIs.

Both APIs are normalized into one shared article schema before extraction and RDF generation.

## Unified Schema

Each collected article is normalized into a record with these fields:

- `id`
- `source_name`
- `source_system`
- `title`
- `url`
- `published_at`
- `updated_at`
- `author`
- `section`
- `tags`
- `summary`
- `content`
- `word_count`
- `raw_article_type_hint`

## Current Mapping Table

| Unified field or derived signal | Source or stage | RDF representation | Ontology target | Status |
| --- | --- | --- | --- | --- |
| `id` + `url` | Collection + normalisation | Article URI and canonical URL literal | `news:NewsArticle`, `news:articleURL` | `Implemented` |
| `title` | GuardianAPI / NewsAPI | Headline literal | `schema:headline` | `Implemented` |
| `published_at` | GuardianAPI / NewsAPI | Publication datetime literal | `news:publishedDate` | `Implemented` |
| `updated_at` | GuardianAPI metadata or fallback to publication time | Update datetime literal | `news:hasUpdateTimestamp` | `Implemented` |
| `source_name` | GuardianAPI / NewsAPI | Publisher entity with label | `news:NewsOrganisation`, `news:publishedBy` | `Implemented` |
| `author` | Guardian byline / NewsAPI author | Journalist entity with label | `news:Journalist`, `news:hasAuthor` | `Implemented` |
| `section` | Guardian section / normalized NewsAPI section | Section literal | `news:hasSection` | `Implemented` |
| `summary` + `content` | Guardian text fields / NewsAPI snippet text | Description literal | `schema:description` | `Implemented` |
| `word_count` | Guardian field or estimated count | Integer literal | `news:wordCount` | `Implemented` |
| `tags` + keyword topics | Extraction | Topic entity with label | `news:Topic`, `news:hasTopic` | `Implemented` |
| Person mentions | Extraction | Mentioned person entity with label | `schema:Person`, `news:mentionsPerson` | `Implemented` |
| Organisation mentions | Extraction | Mentioned organisation entity with label | `news:Organisation`, `news:mentionsOrganisation` | `Implemented` |
| Location mentions | Extraction | Mentioned location entity with label | `news:Location`, `news:mentionsLocation` | `Implemented` |
| `raw_article_type_hint` + enrichment rules | Collection + completion | Article subtype assertion | `news:BreakingNewsArticle`, `news:OpinionArticle` | `Partial` |
| Sentiment label | Completion | Sentiment link to controlled individual | `news:hasSentiment` | `Partial` |
| Follow-up story signal | Completion | Inter-article link | `news:hasFollowUp` | `Partial` |
| Political actor classification | Planned extraction / completion | Person subtype assertion | `news:Politician` | `Missing` |
| Political party classification | Planned extraction / completion | Organisation subtype assertion | `news:PoliticalParty` | `Missing` |
| Government body classification | Planned extraction / completion | Organisation subtype assertion | `news:GovernmentBody` | `Missing` |
| Event extraction | Planned extraction / completion | Event node plus links from article | `news:NewsEvent`, `news:PoliticalEvent`, `news:EconomicEvent`, `news:coversEvent`, `news:eventDate`, `news:eventLocation` | `Missing` |
| Journalist affiliation | Planned derivation / completion | Journalist to publisher link | `news:worksFor` | `Missing` |

## External Ontology Alignment

| Local term | External alignment | Role in the project |
| --- | --- | --- |
| `news:NewsArticle` | `rdfs:subClassOf schema:NewsArticle` | Main article class for all collected records. |
| `news:Journalist` | `rdfs:subClassOf schema:Person` | Author entities. |
| `news:Organisation` | `rdfs:subClassOf schema:Organization` | General organisations mentioned in articles. |
| `news:NewsOrganisation` | `rdfs:subClassOf news:Organisation` | Publisher entities. |
| `news:Politician` | `rdfs:subClassOf schema:Person` | Planned refinement for political actors. |
| `news:PoliticalParty` | `rdfs:subClassOf news:Organisation` | Planned refinement for party mentions. |
| `news:GovernmentBody` | `rdfs:subClassOf news:Organisation` | Planned refinement for departments, ministries, and parliamentary bodies. |
| `news:Topic` | `rdfs:subClassOf schema:Thing` | Policy and politics themes. |
| `news:Location` | `rdfs:subClassOf core:Place` | Geographic mentions. |
| `news:NewsEvent` | `rdfs:subClassOf core:Event` | Generic covered event class. |
| `news:PoliticalEvent` | `rdfs:subClassOf news:NewsEvent` | Planned political event subtype. |
| `news:EconomicEvent` | `rdfs:subClassOf news:NewsEvent` | Planned economic event subtype. |
| `news:hasAuthor` | `rdfs:subPropertyOf schema:author` | Article-to-journalist relation. |
| `news:publishedBy` | `rdfs:subPropertyOf schema:publisher` | Article-to-publisher relation. |
| `news:hasTopic` | `rdfs:subPropertyOf schema:about` | Article-to-topic relation. |
| `news:mentionsPerson` | `rdfs:subPropertyOf schema:mentions` | Typed person mention relation. |
| `news:mentionsOrganisation` | `rdfs:subPropertyOf schema:mentions` | Typed organisation mention relation. |
| `news:mentionsLocation` | `rdfs:subPropertyOf schema:mentions` | Typed location mention relation. |
| `news:publishedDate` | `rdfs:subPropertyOf schema:datePublished` | Publication timestamp. |
| `news:hasSection` | `rdfs:subPropertyOf schema:articleSection` | Section metadata. |
| `news:articleURL` | `rdfs:subPropertyOf schema:url` | Canonical article URL. |
| `news:worksFor` | `rdfs:subPropertyOf schema:worksFor` | Planned journalist affiliation relation. |
| `news:eventLocation` | `rdfs:subPropertyOf core:eventPlace` | Planned event-place mapping. |
| `news:eventDate` | `rdfs:subPropertyOf core:startDate` | Planned event-date mapping. |
| `news:coversEvent` | `rdfs:subPropertyOf core:notablyAssociatedWith` | Planned article-to-event mapping. |

## Key Modelling Notes

- The final CQ set is centred on politics and policy, not on generic current news and not on technology.
- Author, publisher, topic, section, update timestamp, word count, and URL are already strong enough to support several coursework queries.
- Event modelling, political-actor typing, and journalist affiliation are the main remaining gaps between the ontology design and the populated KG.
- The final scoped ontology now excludes legacy technology-only relations that are not populated by the politics-and-policy pipeline.
