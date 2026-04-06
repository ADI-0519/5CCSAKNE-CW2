# Mapping Specification

This document records both the source-to-ontology mapping used by the pipeline and the alignment of the local ontology to reused external vocabularies.

## Source-to-Ontology Mapping

| Source or extraction output | RDF representation | Ontology target | Notes |
| --- | --- | --- | --- |
| `article.url` | Article URI and `news:articleURL` literal | `news:NewsArticle`, `news:articleURL` | Stable article identifiers are minted from the canonical URL. |
| `article.title` | Literal headline | `schema:headline` | Kept as a literal for direct display and querying. |
| `article.publishedAt` | DateTime literal | `news:publishedDate` | Also asserted as `schema:datePublished` via the subproperty mapping. |
| `article.source.name` | Publisher IRI plus label | `news:NewsOrganisation`, `news:publishedBy` | Publisher is modelled as an entity, not a literal. |
| `article.author` | Author IRI plus label | `news:Journalist`, `news:hasAuthor` | Author is modelled as an entity, not a literal. |
| `article.description` or `article.content` | Summary literal | `schema:description` | Used as the article summary in the prototype. |
| Extracted organisation mentions | Mentioned organisation IRI plus label | `news:Organisation`, `news:mentionsOrganisation` | Distinct from `news:NewsOrganisation`, which is reserved for publishers. |
| Extracted person mentions | Person IRI plus label | `schema:Person`, `news:mentionsPerson` | Authors are additionally typed as `news:Journalist`. |
| Extracted location mentions | Location IRI plus label | `news:Location`, `news:mentionsLocation` | Locations are mentioned entities, not article metadata. |
| Extracted technology mentions | Technology IRI plus label | `news:Technology`, `news:mentionsTechnology` | Technology mentions are now typed explicitly instead of using a generic predicate. |
| Extracted topic labels | Topic IRI plus label | `news:Topic`, `news:hasTopic` | Topics are treated as article themes rather than generic mentions. |
| Organisation and technology co-occurrence | Relation triple | `news:usesTechnology` | This is a heuristic signal and should later be replaced or validated by stronger extraction. |

## External Ontology Alignment

| Local term | External alignment | Reason |
| --- | --- | --- |
| `news:NewsArticle` | `rdfs:subClassOf schema:NewsArticle` | Core class for news items. |
| `news:Journalist` | `rdfs:subClassOf schema:Person` | Preserves interoperability for person metadata. |
| `news:Organisation` | `rdfs:subClassOf schema:Organization` | Covers general organisations mentioned in reporting. |
| `news:NewsOrganisation` | `rdfs:subClassOf news:Organisation` | Distinguishes publishers from other organisations. |
| `news:Technology` | `rdfs:subClassOf schema:Thing` | Supports technology entities referenced by articles. |
| `news:Topic` | `rdfs:subClassOf schema:Thing` | Topics are modelled as named thematic entities. |
| `news:NewsEvent` | `rdfs:subClassOf core:Event` | Prepares the ontology for later event extraction. |
| `news:Location` | `rdfs:subClassOf core:Place` | Reuses the BBC place abstraction for geographic mentions. |
| `news:hasAuthor` | `rdfs:subPropertyOf schema:author` | Keeps custom semantics while remaining interoperable. |
| `news:publishedBy` | `rdfs:subPropertyOf schema:publisher` | Models publisher relations as entity links rather than literals. |
| `news:hasTopic` | `rdfs:subPropertyOf schema:about` | Treats topics as the article’s aboutness relation. |
| `news:mentionsPerson` | `rdfs:subPropertyOf schema:mentions` | Typed mention relation for people. |
| `news:mentionsOrganisation` | `rdfs:subPropertyOf schema:mentions` | Typed mention relation for organisations. |
| `news:mentionsLocation` | `rdfs:subPropertyOf schema:mentions` | Typed mention relation for locations. |
| `news:mentionsTechnology` | `rdfs:subPropertyOf schema:mentions` | Typed mention relation for technologies. |
| `news:publishedDate` | `rdfs:subPropertyOf schema:datePublished` | Keeps date semantics in the local ontology. |
| `news:articleURL` | `rdfs:subPropertyOf schema:url` | Keeps canonical URLs queryable in both namespaces. |
| `news:eventLocation` | `rdfs:subPropertyOf core:eventPlace` | Reuses BBC Core Concepts for event place modelling. |
| `news:eventDate` | `rdfs:subPropertyOf core:startDate` | Reuses BBC Core Concepts for event date modelling. |
| `news:coversEvent` | `rdfs:subPropertyOf core:notablyAssociatedWith` | Connects articles to covered events. |

## Key Modelling Decisions

- Publishers are represented as IRIs so that articles can link to `news:NewsOrganisation` instances.
- Mentioned organisations are separated from publishers by introducing `news:Organisation`.
- Technology mentions use a typed property and class, which closes a previous gap between the TBox and ABox.
- Topic links are modelled with `news:hasTopic` instead of the previous generic `mentions` relation.
- The pipeline now produces a combined KG that merges ontology triples and instance triples into the final Turtle output.
