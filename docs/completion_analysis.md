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

The current completion stage is implemented in `src/complete_kg.py` and runs three steps in sequence.

The first step adds inverse `news:reportsOn` links for all existing `news:reportedByArticle` triples. This is fully deterministic.

The second step adds `news:matchedToSourceRecord` and `news:representedInOfficialSource` links between policy events and official Parliament or GOV.UK source records. Matching uses a scoring heuristic based on title similarity, event type, and date agreement.

The third step is an LLM-assisted enrichment step. For each policy event missing `involvesActor`, `involvesGovernmentBody`, or `concernsPolicyTopic`, the pipeline retrieves the event's immediate KG neighbourhood via SPARQL (article headlines, publisher names, topic names, and matched source titles), verbalises the retrieved context as a natural language sentence, and sends it to OpenAI with instructions to propose missing property values constrained to the ontology vocabulary. Proposed actors are filtered against a blocklist of institutional terms and validated by slug-term overlap with the retrieved context before any triple is written. The step implements the retrieve-verbalise-prompt-validate pattern described in the Week 11 slides.

## Latest Validated Run

Latest validated run:

- timestamp: `20260420T202251Z`
- normalised source records: `732`
- Guardian articles: `253`
- Parliament source records: `20`
- GOV.UK source records: `459`
- Wikidata entities: `1730` politicians, `967` parties, `490` government bodies
- ontology graph: `188` triples
- source-derived instance KG: `14429` triples
- Wikidata KG: `25064` triples
- prototype KG: `39510` triples
- completed KG: `40279` triples
- query coverage: `20/20`

Completion additions in that run:

- `255` `news:reportsOn` inverse links
- `236` `news:matchedToSourceRecord` cross-source links
- `35` `news:involvesActor` links (RAG)
- `91` `news:involvesGovernmentBody` links (RAG)
- `144` `news:concernsPolicyTopic` links (RAG)

The completed KG is therefore larger than the prototype KG by `769` triples.

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

## Why Completion Matters

Completion improves the query layer without changing the core ontology:

- `news:reportsOn` lets queries start from articles and navigate to events.
- `news:matchedToSourceRecord` makes cross-source alignment explicit for source-integration audits.
- Mirroring existing `representedInOfficialSource` evidence into `matchedToSourceRecord` keeps official-source integration visible even when the graph is inspected outside the CQ query set.
- `news:involvesActor`, `news:involvesGovernmentBody`, and `news:concernsPolicyTopic` links added by the RAG step make events queryable that were previously invisible to CQs requiring actor or topic filtering. The 35 actor links, 91 department links, and 144 topic links were not present in the prototype KG.

The latest run confirms this is enough for all `20/20` competency queries to return at least one row.

## Recommended Backlog

1. Add stronger event canonicalisation so repeated events are reused across articles and official records.
2. Add provenance metadata for completion-generated links, such as match score or match reason.
3. Link article-extracted political actors to Wikidata entities where labels and contextual evidence agree.
4. Extend the RAG enrichment step to cover `occursInParliamentaryBody` for parliamentary events missing a chamber assignment, using the same retrieve-verbalise-validate pattern already implemented for actor and department links.
5. Keep reporting completion results as concrete graph deltas, not as generic claims about AI improvement.

## Final Assessment

The completion stage now combines deterministic graph enrichment with an LLM-assisted RAG step. The defensible claim is that the pipeline adds inverse article-event links, cross-source source-record matches, and context-grounded actor, department, and topic links that collectively improve CQ coverage and provenance without inventing triples that lack evidential support in the retrieved KG context.
