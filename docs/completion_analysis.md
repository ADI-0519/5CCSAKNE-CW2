# Completion Analysis

This document describes the current completion/enrichment stage in the pipeline and the remaining graph-quality gaps after the latest validated run.

Project scope:

`UK parliamentary and government policy events reported in UK news during 6 March 2026 to 6 April 2026, using Guardian as the core textual reporting source, Parliament/Hansard and GOV.UK as official sources, optional Wikidata enrichment, and OpenAI for constrained extraction support where configured.`

## Current Pipeline State

The current codebase has four source paths feeding the final graph:

1. Guardian article records, used as the core textual reporting source.
2. UK Parliament / Hansard written-statement records, used as official parliamentary source records.
3. GOV.UK records, used as official government source records.
4. Optional Wikidata records for politicians, parties, and government bodies.

The end-to-end pipeline builds a prototype KG from the ontology, source-derived RDF instances, and optional Wikidata triples. It then runs a deterministic completion stage over the merged graph.

The current completion stage is implemented in `src/complete_kg.py`. It does two things:

- adds inverse `news:reportsOn` links for existing `news:reportedByArticle` links
- adds `news:matchedToSourceRecord` links between policy events and aligned source records, including mirrored matches for events already represented in official Parliament or GOV.UK records

This is ontology-constrained graph enrichment. It is not currently a full retrieval-augmented generation pipeline with embeddings or vector search.

## Latest Validated Run

Latest validated run:

- timestamp: `20260420T130554Z`
- normalised source records: `373`
- Guardian articles: `253`
- Parliament source records: `20`
- GOV.UK source records: `100`
- Wikidata entities: `1719` politicians, `967` parties, `490` government bodies
- ontology graph: `190` triples
- source-derived instance KG: `7443` triples
- Wikidata KG: `24950` triples
- prototype KG: `32380` triples
- completed KG: `32453` triples
- query coverage: `20/20`

Completion additions in that run:

- `51` `news:reportsOn` inverse links
- `22` `news:matchedToSourceRecord` links

The completed KG is therefore larger than the prototype KG by `73` triples.

## What Is Covered Well

The current graph is strongest for the event-centred model:

- `news:PolicyEvent`
- `news:ParliamentaryEvent`
- `news:GovernmentPolicyEvent`
- `news:ParliamentaryDebate`
- `news:MinisterialStatement`
- `news:PoliticalActor`
- `news:PoliticalParty`
- `news:OfficialBody`
- `news:GovernmentBody`
- `news:GovernmentDepartment`
- `news:ParliamentaryBody`
- `news:PolicyTopic`
- `news:Location`
- `news:NewsArticle`
- `news:SourceRecord`
- `news:OfficialSourceRecord`

The following properties are materially populated:

- `news:reportedByArticle`
- `news:reportsOn`
- `news:representedInOfficialSource`
- `news:matchedToSourceRecord`
- `news:concernsPolicyTopic`
- `news:involvesActor`
- `news:involvesGovernmentBody`
- `news:issuedByDepartment`
- `news:occursInParliamentaryBody`
- `news:occursInLocation`
- `news:occursOnDate`
- `news:publishedBy`
- `news:hasAuthor`
- `news:publishedDate`
- `news:articleURL`
- `news:sourceIdentifier`
- `news:sourceTitle`
- `news:sourceSystem`

This supports the final CQ set because the questions now focus on policy events, official institutions, source provenance, topics, reporting articles, and cross-source linkage.

## Remaining Gaps

`G1.` Event identity is still partly article-local.

The pipeline creates policy-event nodes from source records and extracted article evidence. Some event names remain broad, so two records about the same real-world event may not always collapse to one canonical event.

`G2.` Cross-source matching is conservative.

`matchedToSourceRecord` links are added only when existing official-source evidence or a title/date/topic match is strong enough. This avoids many false matches but means some genuine links remain absent.

`G3.` Article-extracted actors are not fully disambiguated.

Wikidata provides strong background entities, but article-extracted political actors are still produced mainly from controlled names and extraction heuristics. Full entity resolution between extracted names and Wikidata URIs remains future work.

`G4.` Completion provenance is lightweight.

The graph records the linked source record but does not yet attach confidence scores, evidence spans, or a detailed explanation of why each match was accepted.

`G5.` The current completion stage is not full RAG.

Future RAG work can be added by retrieving relevant source-record and article context before proposing ontology-compatible event matches or missing links. The current implementation should be described more cautiously as graph enrichment or completion.

## Why Completion Matters

Completion improves the query layer without changing the core ontology:

- `news:reportsOn` lets queries start from articles and navigate to events.
- `news:matchedToSourceRecord` supports CQ12, which asks which source systems contributed records matched to policy events.
- Mirroring existing `representedInOfficialSource` evidence into `matchedToSourceRecord` makes official-source integration visible to provenance queries.

The latest run confirms this is enough for all `20/20` competency queries to return at least one row.

## Recommended Backlog

1. Add stronger event canonicalisation so repeated events are reused across articles and official records.
2. Add provenance metadata for completion-generated links, such as match score or match reason.
3. Link article-extracted political actors to Wikidata entities where labels and contextual evidence agree.
4. If RAG is implemented, keep it ontology-constrained: retrieve source evidence, generate candidate triples, validate them against the ontology, then merge only accepted triples.
5. Keep reporting completion results as concrete graph deltas, not as generic claims about AI improvement.

## Final Assessment

The completion stage is implemented and useful, but it is deliberately narrow. The defensible claim is that the pipeline performs deterministic ontology-aligned enrichment over the prototype KG, adding inverse article-event links and cross-source source-record matches that improve CQ coverage and provenance.
