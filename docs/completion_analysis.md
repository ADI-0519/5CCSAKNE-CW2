# Completion Analysis

This document describes the current completion/enrichment stage in the pipeline and the main areas where the graph has been strengthened after the latest validated run.

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

- timestamp: `20260422T202216Z`
- normalised source records: `732`
- Guardian articles: `253`
- Parliament source records: `20`
- GOV.UK source records: `459`
- Wikidata entities: `1715` politicians, `968` parties, `489` government bodies
- ontology graph: `188` triples
- source-derived instance KG: `15095` triples
- Wikidata KG: `25020` triples
- prototype KG: `40125` triples
- completed KG: `40836` triples
- query coverage: `20/20`

Completion additions in that run:

- `274` `news:reportsOn` inverse links
- `236` `news:matchedToSourceRecord` cross-source links
- `2` `news:representedInOfficialSource` links
- `10` `news:involvesActor` links (RAG)
- `14` `news:involvesGovernmentBody` links (RAG)
- `142` `news:concernsPolicyTopic` links (RAG)

The completed KG is therefore larger than the prototype KG by `711` triples.

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

## Current Maturity Notes

`G1.` Event identity is now strongly event-centred, with scope to increase cross-article canonical reuse further.

The pipeline creates policy-event nodes from source records and extracted article evidence. Some event names remain broad, so there is still room to increase canonical reuse for repeated real-world events across multiple articles and source records.

`G2.` Cross-source matching is intentionally conservative.

`matchedToSourceRecord` links are added only when existing official-source evidence or a title/date/topic match is strong enough. This keeps provenance reliable and makes the matched source links easy to audit.

`G3.` Article-extracted actors already benefit from Wikidata background knowledge and can be extended with fuller entity resolution.

Wikidata provides strong background entities, while article-extracted political actors are produced mainly from controlled names and extraction heuristics. A fuller entity-resolution layer would make this even stronger.

`G4.` Completion provenance is already operational and could be extended further.

The graph records linked source records directly; adding confidence scores or evidence spans would make that provenance layer even richer.

## Why Completion Matters

Completion improves the query layer without changing the core ontology:

- `news:reportsOn` lets queries start from articles and navigate to events.
- `news:matchedToSourceRecord` makes cross-source alignment explicit for source-integration audits.
- Mirroring existing `representedInOfficialSource` evidence into `matchedToSourceRecord` keeps official-source integration visible even when the graph is inspected outside the CQ query set.
- `news:involvesActor`, `news:involvesGovernmentBody`, and `news:concernsPolicyTopic` links added by the RAG step make events queryable that were previously invisible to CQs requiring actor or topic filtering. The 10 actor links, 14 department links, and 142 topic links were not present in the prototype KG.

The latest run confirms this is enough for all `20/20` competency queries to return at least one row.

## Recommended Backlog

1. Add stronger event canonicalisation so repeated events are reused across articles and official records.
2. Add provenance metadata for completion-generated links, such as match score or match reason.
3. Link article-extracted political actors to Wikidata entities where labels and contextual evidence agree.
4. Extend the RAG enrichment step to cover `occursInParliamentaryBody` for parliamentary events missing a chamber assignment, using the same retrieve-verbalise-validate pattern already implemented for actor and department links.
5. Keep reporting completion results as concrete graph deltas, not as generic claims about AI improvement.

## Final Assessment

The completion stage now combines deterministic graph enrichment with an LLM-assisted RAG step. The defensible claim is that the pipeline adds inverse article-event links, cross-source source-record matches, and context-grounded actor, department, and topic links that collectively improve CQ coverage and provenance without inventing triples that lack evidential support in the retrieved KG context.
