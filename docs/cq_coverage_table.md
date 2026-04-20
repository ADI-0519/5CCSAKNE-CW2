# CQ Coverage Table

This table records how each competency question is supported by the current event-centred pipeline. Counts come from running the current query set against the latest validated completed KG from `20260420T202251Z`, where all `20/20` queries returned at least one row.

Classification legend:

- `Answered`: query returns meaningful rows using well-populated ontology terms.
- `Answered (soft)`: query returns rows, but answer quality still depends on residual extraction noise or generic event labels.
- `Diagnostic`: query is intended to expose incompleteness rather than produce only polished answers.

| CQ | Classification | Result count | Notes |
| --- | --- | ---: | --- |
| CQ01 | Answered | 15 | Parliamentary debates are linked to policy topics and dates, mainly through PMQs-style records. |
| CQ02 | Answered | 25 | Ministerial statements are linked to issuing government departments through official-source records. |
| CQ03 | Answered (soft) | 11 | Political-actor extraction is useful but still depends on partial actor disambiguation. |
| CQ04 | Answered | 233 | Confirms events can be both reported by news articles and represented in official source records. |
| CQ05 | Answered | 3 | Shows shared policy topics across parliamentary and government policy events. |
| CQ06 | Answered (soft) | 4 | Parliamentary-body links are populated, but some rows still use generic `Parliamentary Debate` labels. |
| CQ07 | Answered | 8 | Government departments can be ranked by linked policy-event count. |
| CQ08 | Answered (soft) | 4 | Party membership depends on actor-party typing quality and Wikidata enrichment. |
| CQ09 | Diagnostic | 193 | Intentionally identifies reported events still missing a government body, parliamentary body, or topic. |
| CQ10 | Answered | 12 | Policy-topic frequency query over reported parliamentary and government policy events. |
| CQ11 | Answered | 81 | Cross-source question over officially represented events involving government departments. |
| CQ12 | Answered | 11 | Topic aggregation over officially evidenced events. |
| CQ13 | Answered | 48 | Topic co-occurrence query exercises event-topic self-joins. |
| CQ14 | Answered | 12 | Comparative parliamentary-versus-government topic coverage query; now includes government-only topics as well. |
| CQ15 | Answered (soft) | 7 | Location aggregation is supported, though event-location assignment remains conservative. |
| CQ16 | Answered (soft) | 8 | Actor-party-topic aggregation works, but topic breadth still depends on extraction quality. |
| CQ17 | Answered (soft) | 11 | Journalist-to-article-to-event-to-department retrieval works, though it remains a softer, article-facing evaluation query. |
| CQ18 | Answered | 11 | Finds topics on events involving both actors and government bodies. |
| CQ19 | Answered (soft) | 1 | Date-and-topic overlap between parliamentary events and ministerial statements works, but still relies on some generic parliamentary-event labels. |
| CQ20 | Answered | 8 | Ranks departments by distinct policy-topic breadth across linked events. |

## Summary

- Query coverage: `20/20`
- Most robust areas: official source records, event-topic links, event-institution links, article-event reporting links.
- Main residual risk: extraction precision and event canonicalisation, not ontology/query alignment.
- Important correction since earlier versions: `CQ14` now counts both parliamentary and government coverage per topic without dropping government-only topics.
