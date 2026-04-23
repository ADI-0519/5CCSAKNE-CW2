# Completion Analysis

This document describes the current completion/enrichment stage in the pipeline and the remaining graph-quality gaps after the latest validated run.

Project scope:

`UK parliamentary and government policy events reported in UK news over a rolling 30-day collection window, using Guardian as the core textual reporting source, Parliament/Hansard and GOV.UK as official sources, optional Wikidata enrichment, and OpenAI for constrained extraction support where configured.`

The submitted cached snapshot covers 23 March 2026 to 22 April 2026 and is fixed for examiner reproducibility.

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

- timestamp: `20260423T121805Z`
- normalised source records: `700`
- Guardian articles: `270`
- Parliament source records: `20`
- GOV.UK source records: `410`
- Wikidata entities: `1724` politicians, `968` parties, `489` government bodies
- ontology graph: `192` triples
- source-derived instance KG: `13458` triples
- Wikidata KG: `25115` triples
- prototype KG: `38596` triples
- completed KG: `39101` triples
- query coverage: `20/20`

Completion additions in that run:

- `194` `news:reportsOn` inverse links
- `157` `news:matchedToSourceRecord` cross-source links
- `5` `news:representedInOfficialSource` links
- `7` `news:involvesActor` links (RAG)
- `6` `news:involvesGovernmentBody` links (RAG)
- `114` `news:concernsPolicyTopic` links (RAG)

The completed KG is therefore larger than the prototype KG by `505` triples.

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

## Incomplete Ontology Elements

`O1.` No formal property characteristics on most object properties.

`news:involvesActor` and `news:memberOfParty` are declared `owl:IrreflexiveProperty` and `news:publishedBy` and `news:occursOnDate` are declared `owl:FunctionalProperty`. Beyond these four, the remaining object properties carry no formal axioms such as cardinality restrictions, so the reasoner has no basis to detect further constraint violations.

`O2.` No disjointness axioms between event subclasses.

`news:GovernmentPolicyEvent` and `news:ParliamentaryEvent` are not declared `owl:disjointWith`. In the domain they represent conceptually distinct event types with different provenance, but the ontology does not formally enforce this separation, so a reasoning step cannot flag instances typed as both.

`O3.` No cardinality constraint on `news:occursOnDate` beyond functional.

`news:occursOnDate` is declared functional, which enforces at most one date per event. The ontology does not separately enforce that at least one date is always present; a `PolicyEvent` with no date passes the TBox without a violation, making the date-completeness guarantee informal rather than axiomatic.

`O4.` No provenance vocabulary for completion-generated links.

The ontology has no class or datatype property to record a confidence score, evidence span, or extraction method alongside completion-generated triples. All assertions written by the RAG step are treated as equally certain in the graph, which limits post-hoc auditability.

`O5.` No temporal ordering or sequencing property.

The ontology models individual events with dates but has no property to link related events in order, such as a parliamentary debate preceding a policy announcement. This limits the expressiveness of the event-centred model for questions about causal or procedural event sequences.

## Incomplete Instance Elements

`I1.` Event identity is still partly article-local.

The pipeline creates policy-event nodes from source records and extracted article evidence. Some event names remain broad, so two records about the same real-world event may not always collapse to one canonical event node.

`I2.` Cross-source matching is conservative.

`news:matchedToSourceRecord` links are added only when title similarity, event type, and date agreement score above a threshold. This avoids false matches but means genuine article-to-official-source links remain absent where the threshold is not met.

`I3.` Article-extracted actors are not resolved to Wikidata URIs.

Wikidata provides background entities for UK politicians, but article-extracted political actors are produced mainly from controlled names and heuristics. An actor mentioned by name in a Guardian article and the corresponding Wikidata politician entity are not linked by any `owl:sameAs` or `skos:exactMatch` assertion.

`I4.` Parliamentary body assignment is incomplete.

Five of the ten `news:ParliamentaryEvent` instances lack `news:occursInParliamentaryBody` because the source text did not name a specific chamber or committee. Events from written statements are sometimes attributed to the body name but this is not consistently extracted across the full Parliament record set.

`I5.` Completion provenance is not recorded at the instance level.

RAG-added `news:involvesActor`, `news:involvesGovernmentBody`, and `news:concernsPolicyTopic` triples carry no associated evidence metadata in the graph. The completion audit JSON captures per-event additions, but this information is not surfaced as RDF statements, so a SPARQL query cannot distinguish a completion-generated topic link from one written during the initial mapping stage.

`I6.` Location extraction does not reliably capture international event venues.

Addressed: `INTERNATIONAL_BODY_LOCATIONS` in `domain_knowledge.py` maps events whose names mention a known international body to the correct city: WTO General Council to Geneva, UN Human Rights Council to Geneva, OSCE to Vienna, and so on. `CANONICAL_LOCATION_NAMES` in `data_extraction.py` was extended to include the venue cities from that dict, so they pass the downstream validity gate and reach the graph. The extraction pipeline also no longer defaults to Westminster when no stronger candidate is available. Events whose names do not match any known body fragment still lack location data.

## Why Completion Matters

Completion improves the query layer without changing the core ontology:

- `news:reportsOn` lets queries start from articles and navigate to events.
- `news:matchedToSourceRecord` makes cross-source alignment explicit for source-integration audits.
- Mirroring existing `representedInOfficialSource` evidence into `matchedToSourceRecord` keeps official-source integration visible even when the graph is inspected outside the CQ query set.
- `news:involvesActor`, `news:involvesGovernmentBody`, and `news:concernsPolicyTopic` links added by the RAG step make events queryable that were previously invisible to CQs requiring actor or topic filtering. The 7 actor links, 6 department links, and 114 topic links were not present in the prototype KG.

The latest run confirms this is enough for all `20/20` competency queries to return at least one row.

## Recommended Backlog

1. Add stronger event canonicalisation so repeated events are reused across articles and official records.
2. Add provenance metadata for completion-generated links, such as match score or match reason.
3. Link article-extracted political actors to Wikidata entities where labels and contextual evidence agree.
4. Extend the RAG enrichment step to cover `occursInParliamentaryBody` for parliamentary events missing a chamber assignment, using the same retrieve-verbalise-validate pattern already implemented for actor and department links.
5. Keep reporting completion results as concrete graph deltas, not as generic claims about AI improvement.

## Final Assessment

The completion stage now combines deterministic graph enrichment with an LLM-assisted RAG step. The defensible claim is that the pipeline adds inverse article-event links, cross-source source-record matches, and context-grounded actor, department, and topic links that collectively improve CQ coverage and provenance without inventing triples that lack evidential support in the retrieved KG context.
