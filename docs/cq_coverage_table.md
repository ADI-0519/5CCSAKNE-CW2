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

Counts come from running the current query set against the latest validated completed KG from `20260422T172612Z`, where all `20/20` queries returned at least one row and all `17` validation rules passed with `0` failures.

Classification legend:

- `Answered`: query returns meaningful rows using well-populated ontology terms.
- `Answered (soft)`: query returns rows, but answer quality still depends on residual extraction noise or generic event labels.
- `Diagnostic`: query is intended to expose incompleteness rather than produce only polished answers.

| CQ | Classification | Result count | Notes |
| --- | --- | ---: | --- |
| CQ01 | Answered | 14 | Parliamentary debates are linked to policy topics and dates, mainly through PMQs-style records. |
| CQ02 | Answered | 66 | Ministerial statements are linked to issuing government departments through official-source records. |
| CQ03 | Answered (soft) | 11 | Political-actor extraction is useful but still depends on partial actor disambiguation. |
| CQ04 | Answered | 235 | Confirms events can be both reported by news articles and represented in official source records. |
| CQ05 | Answered | 3 | Shows shared policy topics across parliamentary and government policy events. |
| CQ06 | Answered | 6 | Parliamentary-body links are now populated consistently enough for this topic-based aggregation query. |
| CQ07 | Answered | 16 | Government departments can be ranked by linked policy-event count. |
| CQ08 | Answered (soft) | 4 | Party membership depends on actor-party typing quality and Wikidata enrichment. |
| CQ09 | Diagnostic | 8 | Intentionally identifies reported events still missing a government body, parliamentary body, or topic; the low remaining count now reflects residual incompleteness rather than broad structural gaps. |
| CQ10 | Answered | 16 | Policy-topic frequency query over reported parliamentary and government policy events. |
| CQ11 | Answered | 222 | Cross-source question requiring both official-source representation and a department link; the completed graph now supports this strongly. |
| CQ12 | Answered | 12 | Topic aggregation over officially evidenced events; concernsPolicyTopic links from the RAG step significantly extend the result set. |
| CQ13 | Answered | 41 | Topic co-occurrence query exercises event-topic self-joins. |
| CQ14 | Answered | 16 | Comparative parliamentary-versus-government topic coverage query; now includes government-only topics as well. |
| CQ15 | Answered | 9 | Location aggregation is now clean and no longer shows earlier junk-location artefacts. |
| CQ16 | Answered | 8 | Actor-party-topic aggregation benefits from RAG-added actor links improving coverage over the prototype. |
| CQ17 | Answered | 1 | Journalist-to-article-to-event-to-department retrieval was tightened to source-grounded government policy events, sacrificing recall for much better precision. |
| CQ18 | Answered | 15 | Finds topics on events involving both actors and government bodies; both involvesActor and involvesGovernmentBody are partly completion-supported. |
| CQ19 | Answered (soft) | 2 | Date-and-topic overlap between parliamentary events and ministerial statements works, but still relies on some generic parliamentary-event labels. |
| CQ20 | Answered | 16 | Ranks departments by distinct policy-topic breadth across linked events with much cleaner department canonicalisation than earlier runs. |

## Summary

- Query coverage: `20/20`
- Validation status: `17/17` rules passed, `0` failures, `0` violations
- Most robust areas: official source records, event-topic links, event-institution links, article-event reporting links.
- Main residual risk: extraction precision and event canonicalisation, not ontology/query alignment.
- Important correction since earlier versions: `CQ14` now counts both parliamentary and government coverage per topic without dropping government-only topics.
- CQ11 and CQ12 now depend on RAG-added triples; their row counts reflect completion enrichment, not just extraction output.
