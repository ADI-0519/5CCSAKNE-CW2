# Mapping Specification

This document records how the current pipeline maps GuardianAPI and NewsAPI inputs into the local UK politics and policy ontology.

Project scope:

`A knowledge graph for current UK politics and policy news, using articles published between March 6, 2026 and April 6, 2026 from GuardianAPI and NewsAPI, with Wikidata as a structured data source and OpenAI used for extraction, classification, and completion.`

## Mapping Overview

The mapping process is now multi-stage rather than a single direct source-to-RDF transformation.

The current workflow is:

1. collect article data from GuardianAPI and NewsAPI
2. normalise both APIs into a shared internal article schema
3. run extraction over the normalised records
4. convert extracted records into RDF instances aligned with the ontology
5. enrich the prototype KG with a completion stage

This is important because some ontology terms are populated directly from source metadata, some are created by extraction, and some are only added or strengthened during completion.

## Source Design

The coursework requires at least one textual data source and one structured data source. The project satisfies this through two complementary APIs that provide different kinds of data.

### Textual data source: Guardian API (full article body text)

The Guardian API serves as the primary **textual** data source. It returns the full article body text via the `bodyText` field, which provides complete unstructured natural-language content. This text is the primary input for NLP-based extraction: named entity recognition of people, organisations, locations, and topics; sentiment classification; event detection; and article subtype inference. The pipeline processes this free text using both heuristic pattern matching and LLM-assisted structured extraction to produce ontology-aligned triples.

Key textual fields used for NLP extraction:
- `fields.bodyText` — full unstructured article body (typically 500–2000 words)
- `fields.trailText` — editorial summary paragraph
- `webTitle` — article headline

### Structured data source: Wikidata SPARQL endpoint (entity records)

Wikidata serves as the primary **structured** data source. The pipeline queries the public Wikidata Query Service via SPARQL to retrieve UK politicians, political parties, and government bodies. These are typed entity records with explicit fields that map directly to ontology classes and properties without any NLP processing.

Key structured fields mapped directly to RDF:
- `name` — entity label, mapped to `schema:name`
- `party` — politician's party affiliation, mapped to `schema:memberOf` → `news:PoliticalParty`
- `constituency` — politician's constituency, mapped to `news:Location`
- `gender` — mapped to `schema:gender`
- `date_of_birth` — mapped to `schema:birthDate` (xsd:date)
- `inception` / `dissolved` — party founding and dissolution dates, mapped to `schema:foundingDate` / `schema:dissolutionDate`
- `headquarters` — mapped to `schema:location` → `news:Location`
- `wikidata_uri` — linked via `rdfs:seeAlso` for provenance

### Supplementary source: NewsAPI (JSON metadata records)

NewsAPI provides additional structured article metadata from multiple UK news publishers (BBC News, Reuters, Sky News, Financial Times, The Independent). These records are normalised into the shared article schema alongside Guardian articles and follow the same extraction pipeline. NewsAPI broadens publisher coverage but is limited by developer-tier API access.

### Why these sources are needed

The Guardian API provides rich unstructured text that enables deep entity and relationship extraction through NLP. Wikidata provides structured entity records that populate the KG's political actors, parties, and government bodies through direct field-to-property mapping without NLP. NewsAPI supplements the article corpus with additional publisher coverage.

Guardian articles and NewsAPI articles are normalised into one shared article schema before extraction. Wikidata entities follow a separate direct mapping path into RDF.

## Unified Article Schema

Each collected article is normalised into a record with these fields:

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

This schema is the bridge between raw API payloads and ontology population.

## Stage 1: Direct Source Metadata Mapping

The following ontology terms are populated directly from normalized source metadata.

| Unified field | Source | RDF representation | Ontology target | Status |
| --- | --- | --- | --- | --- |
| `id` | Normalisation | Article URI | `news:NewsArticle` | `Implemented` |
| `url` | GuardianAPI / NewsAPI | URL literal | `news:articleURL`, `schema:url` | `Implemented` |
| `title` | GuardianAPI / NewsAPI | Headline literal | `schema:headline` | `Implemented` |
| `published_at` | GuardianAPI / NewsAPI | Publication timestamp | `news:publishedDate`, `schema:datePublished` | `Implemented` |
| `updated_at` | GuardianAPI metadata or fallback logic | Update timestamp | `news:hasUpdateTimestamp`, `schema:dateModified` | `Implemented` |
| `source_name` | GuardianAPI / NewsAPI | Publisher entity and link | `news:NewsOrganisation`, `news:publishedBy`, `schema:publisher` | `Implemented` |
| `author` | Guardian byline / NewsAPI author | Journalist entity and link | `news:Journalist`, `news:hasAuthor`, `schema:author` | `Implemented` |
| `section` | Guardian section / normalized source metadata | Section literal | `news:hasSection`, `schema:articleSection` | `Implemented` |
| `summary` | Guardian trail text / NewsAPI description | Description literal | `schema:description` | `Implemented` |
| `word_count` | Guardian field or estimated count | Integer literal | `news:wordCount`, `schema:wordCount` | `Implemented` |

## Stage 1b: Wikidata Structured Mapping

The following ontology terms are populated directly from Wikidata SPARQL results through field-to-property mapping. No NLP is involved.

| Wikidata field | Entity type | RDF representation | Ontology target | Status |
| --- | --- | --- | --- | --- |
| `name` | Politician | Person URI + label | `news:Politician`, `schema:Person`, `schema:name` | `Implemented` |
| `party` | Politician | Party URI + membership link | `news:PoliticalParty`, `schema:memberOf` | `Implemented` |
| `constituency` | Politician | Location URI + label | `news:Location`, `schema:Place`, `schema:name` | `Implemented` |
| `gender` | Politician | Gender literal | `schema:gender` | `Implemented` |
| `date_of_birth` | Politician | Date literal | `schema:birthDate` | `Implemented` |
| `wikidata_uri` | All | seeAlso link | `rdfs:seeAlso` | `Implemented` |
| `description` | All | Description literal | `schema:description` | `Implemented` |
| `name` | Party | Organisation URI + label | `news:PoliticalParty`, `news:Organisation`, `schema:Organization`, `schema:name` | `Implemented` |
| `inception` | Party | Date literal | `schema:foundingDate` | `Implemented` |
| `dissolved` | Party | Date literal | `schema:dissolutionDate` | `Implemented` |
| `headquarters` | Party / Body | Location URI + label | `news:Location`, `schema:location` | `Implemented` |
| `leader` | Party | Person URI + label | `news:Politician`, `schema:Person`, `schema:name` | `Implemented` |
| `name` | Government body | Organisation URI + label | `news:GovernmentBody`, `news:Organisation`, `schema:Organization`, `schema:name` | `Implemented` |

## Stage 2: Extraction-Based Mapping

The following ontology terms are populated through the extraction layer over the normalised article records.

### Topic mapping

Topics are produced from:

- text matches in title, summary, and content
- Guardian tags
- section-level hints

Mapped ontology terms:

- `news:Topic`
- `news:hasTopic`
- `schema:about`

Status:

- `Implemented`

### Person and political-actor mapping

People are extracted from article text, then refined into political subtypes where possible.

Mapped ontology terms:

- `schema:Person`
- `news:mentionsPerson`
- `news:Politician`

Status:

- `Implemented`, but still partly heuristic

Important note:

Not every person mention is confidently typed as a politician. The subtype mapping exists and is used, but it is still incomplete for ambiguous names.

### Organisation mapping

Organisations are extracted from article text and then refined into political subtypes.

Mapped ontology terms:

- `news:Organisation`
- `news:mentionsOrganisation`
- `news:PoliticalParty`
- `news:GovernmentBody`

Status:

- `Implemented`, but still partly heuristic

### Location mapping

Locations are extracted from article text and linked as both generic place mentions and event locations when relevant.

Mapped ontology terms:

- `news:Location`
- `news:mentionsLocation`

Status:

- `Implemented`

### Article subtype mapping

Article subtype is inferred from:

- source article-type hints
- section information
- article title and text heuristics
- optional OpenAI refinement

Mapped ontology terms:

- `news:NewsArticle`
- `news:OpinionArticle`
- `news:BreakingNewsArticle`

Status:

- `Implemented`

### Sentiment mapping

Sentiment is first inferred heuristically and can later be refined in the completion stage.

Mapped ontology terms:

- `news:Sentiment`
- `news:hasSentiment`

Status:

- `Implemented`

### Event mapping

The extractor now creates article-level event candidates from policy, election, parliamentary, and economic cues in article text.

Mapped ontology terms:

- `news:NewsEvent`
- `news:PoliticalEvent`
- `news:EconomicEvent`
- `news:coversEvent`
- `news:eventDate`
- `news:eventLocation`

Status:

- `Implemented`, but event identity is still relatively weak and partly generic

### Follow-up mapping

The extractor creates candidate follow-up keys, and the RDF layer materialises cross-article follow-up links.

Mapped ontology term:

- `news:hasFollowUp`

Status:

- `Implemented`

## Stage 3: Completion-Based Mapping

After the prototype graph is built, the completion stage enriches it further.

The current completion layer adds or strengthens:

- `news:hasSentiment`
- `news:hasSection`
- `news:wordCount`
- `news:hasUpdateTimestamp`
- additional `news:hasTopic` links
- subtype reinforcement for `news:OpinionArticle` and `news:BreakingNewsArticle`
- `news:hasFollowUp`

This stage is partly heuristic and can also use OpenAI completion with cached structured outputs.

Status:

- `Implemented`

## Current Mapping Table

| Unified field or derived signal | Source or stage | RDF representation | Ontology target | Status |
| --- | --- | --- | --- | --- |
| `id` + `url` | Collection + normalisation | Article URI and canonical URL literal | `news:NewsArticle`, `news:articleURL` | `Implemented` |
| `title` | GuardianAPI / NewsAPI | Headline literal | `schema:headline` | `Implemented` |
| `published_at` | GuardianAPI / NewsAPI | Publication datetime literal | `news:publishedDate` | `Implemented` |
| `updated_at` | GuardianAPI metadata or completion fallback | Update datetime literal | `news:hasUpdateTimestamp` | `Implemented` |
| `source_name` | GuardianAPI / NewsAPI | Publisher entity with label | `news:NewsOrganisation`, `news:publishedBy` | `Implemented` |
| `author` | Guardian byline / NewsAPI author | Journalist entity with label | `news:Journalist`, `news:hasAuthor` | `Implemented` |
| `section` | Guardian section / completion refinement | Section literal | `news:hasSection` | `Implemented` |
| `summary` + `content` | Guardian text fields / NewsAPI snippet text | Description literal | `schema:description` | `Implemented` |
| `word_count` | Guardian field, estimated count, or completion enrichment | Integer literal | `news:wordCount` | `Implemented` |
| `tags` + topic cues | Extraction + completion | Topic entity with label | `news:Topic`, `news:hasTopic` | `Implemented` |
| Person mentions | Extraction | Mentioned person entity with label | `schema:Person`, `news:mentionsPerson` | `Implemented` |
| Politician typing | Extraction | Person subtype assertion | `news:Politician` | `Implemented` |
| Organisation mentions | Extraction | Mentioned organisation entity with label | `news:Organisation`, `news:mentionsOrganisation` | `Implemented` |
| Political party typing | Extraction | Organisation subtype assertion | `news:PoliticalParty` | `Implemented` |
| Government body typing | Extraction | Organisation subtype assertion | `news:GovernmentBody` | `Implemented` |
| Location mentions | Extraction | Mentioned location entity with label | `news:Location`, `news:mentionsLocation` | `Implemented` |
| Article subtype hints + rules | Extraction + completion | Article subtype assertion | `news:BreakingNewsArticle`, `news:OpinionArticle` | `Implemented` |
| Sentiment label | Extraction + completion | Sentiment link to controlled individual | `news:hasSentiment` | `Implemented` |
| Event extraction | Extraction | Event node plus links from article | `news:NewsEvent`, `news:PoliticalEvent`, `news:EconomicEvent`, `news:coversEvent`, `news:eventDate`, `news:eventLocation` | `Implemented` |
| Follow-up story signal | Extraction + RDF + completion | Inter-article link | `news:hasFollowUp` | `Implemented` |
| Journalist affiliation | RDF derivation from author and publisher | Journalist to publisher link | `news:worksFor` | `Implemented` |
| Wikidata politician fields | Wikidata SPARQL (direct mapping) | Person URI with party, constituency, gender, DOB | `news:Politician`, `schema:Person`, `schema:memberOf` | `Implemented` |
| Wikidata party fields | Wikidata SPARQL (direct mapping) | Organisation URI with founding date, HQ, leader | `news:PoliticalParty`, `news:Organisation` | `Implemented` |
| Wikidata government body fields | Wikidata SPARQL (direct mapping) | Organisation URI with HQ | `news:GovernmentBody`, `news:Organisation` | `Implemented` |

## External Ontology Alignment

| Local term | External alignment | Role in the project |
| --- | --- | --- |
| `news:NewsArticle` | `rdfs:subClassOf schema:NewsArticle` | Main article class for all collected records. |
| `news:Journalist` | `rdfs:subClassOf schema:Person` | Author entities. |
| `news:Politician` | `rdfs:subClassOf schema:Person` | Typed political actors. |
| `news:Organisation` | `rdfs:subClassOf schema:Organization` | General organisations mentioned in articles. |
| `news:NewsOrganisation` | `rdfs:subClassOf news:Organisation` | Publisher entities. |
| `news:PoliticalParty` | `rdfs:subClassOf news:Organisation` | Party mentions. |
| `news:GovernmentBody` | `rdfs:subClassOf news:Organisation` | Departments, ministries, and parliamentary bodies. |
| `news:Topic` | `rdfs:subClassOf schema:Thing` | Policy and politics themes. |
| `news:Location` | `rdfs:subClassOf schema:Place` | Geographic mentions. |
| `news:NewsEvent` | `rdfs:subClassOf schema:Event` or local event hierarchy | Covered event class. |
| `news:PoliticalEvent` | `rdfs:subClassOf news:NewsEvent` | Political event subtype. |
| `news:EconomicEvent` | `rdfs:subClassOf news:NewsEvent` | Economic event subtype. |
| `news:hasAuthor` | `rdfs:subPropertyOf schema:author` | Article-to-journalist relation. |
| `news:publishedBy` | `rdfs:subPropertyOf schema:publisher` | Article-to-publisher relation. |
| `news:hasTopic` | `rdfs:subPropertyOf schema:about` | Article-to-topic relation. |
| `news:mentionsPerson` | `rdfs:subPropertyOf schema:mentions` | Typed person mention relation. |
| `news:mentionsOrganisation` | `rdfs:subPropertyOf schema:mentions` | Typed organisation mention relation. |
| `news:mentionsLocation` | `rdfs:subPropertyOf schema:mentions` | Typed location mention relation. |
| `news:publishedDate` | `rdfs:subPropertyOf schema:datePublished` | Publication timestamp. |
| `news:hasUpdateTimestamp` | `rdfs:subPropertyOf schema:dateModified` | Update timestamp. |
| `news:hasSection` | `rdfs:subPropertyOf schema:articleSection` | Section metadata. |
| `news:articleURL` | `rdfs:subPropertyOf schema:url` | Canonical article URL. |
| `news:worksFor` | `rdfs:subPropertyOf schema:worksFor` | Journalist affiliation relation. |

## Key Modelling Notes

- The mapping is now explicitly politics-and-policy focused rather than generic current-news or technology-news focused.
- Guardian and NewsAPI articles are treated as complementary textual sources and are normalised before ontology population.
- Wikidata provides a separate structured data path: entity records are mapped directly to RDF without NLP extraction, populating politicians, political parties, and government bodies.
- The current system combines deterministic metadata mapping, direct structured mapping, heuristic extraction, and constrained OpenAI-assisted refinement.
- The most important remaining weakness is not the absence of mapped ontology terms. It is the quality and stability of some mapped values, especially event identity, actor typing for ambiguous cases, and provenance for completion outputs.
