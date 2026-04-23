# CQ Coverage Table

This table records which sources and pipeline steps support each competency question.

## Source and completion coverage

| CQ | Title (brief) | Primary property tested | Guardian | Parliament | GOV.UK | Wikidata | Completion step |
|---|---|---|---|---|---|---|---|
| CQ01 | Debates by topic | `news:concernsPolicyTopic` | partial | yes | - | - | concernsPolicyTopic (RAG) |
| CQ02 | Statements by department | `news:issuedByDepartment` | partial | yes | yes | partial | |
| CQ03 | Actors in multiple events | `news:involvesActor` | yes | partial | partial | yes | involvesActor (RAG) |
| CQ04 | Events in official sources | `news:representedInOfficialSource` | yes | yes | yes | - | matchedToSourceRecord |
| CQ05 | Topics shared across event types | `news:concernsPolicyTopic` | partial | yes | yes | - | concernsPolicyTopic (RAG) |
| CQ06 | Parliamentary bodies by topic | `news:occursInParliamentaryBody` | partial | yes | - | - | concernsPolicyTopic (RAG) |
| CQ07 | Departments by event count | `news:involvesGovernmentBody` | partial | partial | yes | yes | involvesGovernmentBody (RAG) |
| CQ08 | Parties spanning multiple topics | `news:memberOfParty` | partial | partial | partial | yes | involvesActor (RAG) |
| CQ09 | Events lacking institution or topic | `news:reportedByArticle` | yes | partial | partial | - | |
| CQ10 | Topics by reported event frequency | `news:concernsPolicyTopic` | yes | yes | yes | - | concernsPolicyTopic (RAG) |
| CQ11 | Official events with department | `news:representedInOfficialSource` | partial | yes | yes | - | involvesGovernmentBody (RAG) |
| CQ12 | Topics on officially sourced events | `news:concernsPolicyTopic` | partial | yes | yes | - | concernsPolicyTopic (RAG) |
| CQ13 | Co-occurring topic pairs | `news:concernsPolicyTopic` | partial | partial | partial | - | concernsPolicyTopic (RAG) |
| CQ14 | Topics by event type count | `news:concernsPolicyTopic` | partial | yes | yes | - | concernsPolicyTopic (RAG) |
| CQ15 | Locations with multiple events | `news:occursInLocation` | yes | partial | partial | - | |
| CQ16 | Actors spanning two or more topics | `news:involvesActor` | partial | partial | partial | yes | involvesActor (RAG) |
| CQ17 | Journalists covering department events | `news:hasAuthor` | yes | - | - | - | involvesGovernmentBody (RAG) |
| CQ18 | Topics with both actor and body | `news:involvesActor` | partial | partial | partial | partial | involvesActor (RAG) |
| CQ19 | Topics shared by debates and statements | `news:concernsPolicyTopic` | partial | yes | partial | - | concernsPolicyTopic (RAG) |
| CQ20 | Departments by topic breadth | `news:involvesGovernmentBody` | partial | partial | yes | yes | involvesGovernmentBody (RAG) |

## Query results

Counts come from running the current query set against the latest validated completed KG from `20260423T022716Z`, where all `20/20` queries returned at least one row and `16` of `17` validation rules passed. The single failing rule (V15) has warning severity only and `0` errors.

Classification legend:

- `Answered`: query returns meaningful rows using well-populated ontology terms.
- `Answered (soft)`: query returns rows, but answer quality still depends on residual extraction noise or generic event labels.
- `Diagnostic`: query is intended to expose incompleteness rather than produce only polished answers.

| CQ | Classification | Result count | Notes |
| --- | --- | ---: | --- |
| CQ01 | Answered | 10 | Parliamentary debates are linked to policy topics and dates, mainly through PMQs-style records. |
| CQ02 | Answered | 52 | Ministerial statements are linked to issuing government departments through official-source records. |
| CQ03 | Answered (soft) | 7 | Political-actor extraction is useful but still depends on partial actor disambiguation. |
| CQ04 | Answered | 147 | Confirms events can be both reported by news articles and represented in official source records. |
| CQ05 | Answered | 6 | Shows shared policy topics across parliamentary and government policy events. |
| CQ06 | Answered | 10 | Parliamentary-body links are populated consistently; the explicit parent-type assertion fix ensures ParliamentaryDebate instances satisfy the ParliamentaryEvent type check in the query. |
| CQ07 | Answered | 18 | Government departments can be ranked by linked policy-event count. |
| CQ08 | Answered (soft) | 4 | Party membership depends on actor-party typing quality and Wikidata enrichment. |
| CQ09 | Diagnostic | 17 | Intentionally identifies reported events still missing a government body, parliamentary body, or topic; the count reflects events without complete institution grounding. |
| CQ10 | Answered | 16 | Policy-topic frequency query over reported parliamentary and government policy events. |
| CQ11 | Answered | 142 | Cross-source question requiring both official-source representation and a department link; the completed graph supports this with 7 additional rows over the prototype. |
| CQ12 | Answered | 11 | Topic aggregation over officially evidenced events; concernsPolicyTopic links from the RAG step extend the result set. |
| CQ13 | Answered | 35 | Topic co-occurrence query exercises event-topic self-joins. |
| CQ14 | Answered | 16 | Comparative parliamentary-versus-government topic coverage query. |
| CQ15 | Answered | 6 | Location aggregation over events with populated occursInLocation links. |
| CQ16 | Answered | 7 | Actor-party-topic aggregation benefits from RAG-added actor links. |
| CQ17 | Answered | 5 | Journalist-to-article-to-event-to-department retrieval over source-grounded government policy events. |
| CQ18 | Answered | 18 | Finds topics on events involving both actors and government bodies; both involvesActor and involvesGovernmentBody are partly completion-supported. |
| CQ19 | Answered (soft) | 4 | Date-and-topic overlap between parliamentary events and ministerial statements works, but still relies on some generic parliamentary-event labels. |
| CQ20 | Answered | 16 | Ranks departments by distinct policy-topic breadth across linked events. |

## Summary

- Query coverage: `20/20`
- Validation status: `16/17` rules passed, `1` failure (V15, warning severity), `0` errors, `8` warnings
- Most populated areas: official source records, event-topic links, event-institution links, article-event reporting links.
- Main residual risk: extraction precision and event canonicalisation, not ontology/query alignment.
- CQ06 now requires the explicit intermediate type assertion fix in `json_to_rdf.py`: `ParliamentaryDebate` instances must also be asserted as `ParliamentaryEvent` for the SPARQL type check to match.
- CQ11 shows the strongest completion benefit with 6 additional rows over the prototype.
