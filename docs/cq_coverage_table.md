# CQ Coverage Table

This table records how each competency question is supported by the current event-centred pipeline. Counts come from the validated `20260420T130554Z` run, where all 20 queries returned at least one row.

Classification legend:

- `Answered`: query returns meaningful rows using well-populated ontology terms.
- `Answered (noisy)`: query returns rows, but the underlying extraction or matching still has known quality limits.
- `Diagnostic`: query is intended to expose incompleteness rather than produce only polished answers.

| CQ | Classification | Result count | Notes |
| --- | --- | ---: | --- |
| CQ01 | Answered | 21 | Parliamentary debates are linked to policy topics and dates. |
| CQ02 | Answered | 4 | Ministerial statements are linked to issuing government departments. |
| CQ03 | Answered (noisy) | 11 | Political-actor extraction is useful but not fully disambiguated against Wikidata. |
| CQ04 | Answered | 22 | Confirms events can be both reported by articles and represented in official source records. |
| CQ05 | Answered | 6 | Shows shared policy topics across parliamentary and government policy events. |
| CQ06 | Answered | 7 | Parliamentary-body links are populated for parliamentary event records. |
| CQ07 | Answered | 7 | Government departments can be ranked by linked policy-event count. |
| CQ08 | Answered (noisy) | 4 | Party membership depends on extracted and enriched actor-party links. |
| CQ09 | Diagnostic | 50 | Intentionally identifies reported events missing a government body, parliamentary body, or topic. |
| CQ10 | Answered | 12 | Policy-topic frequency query over reported parliamentary and government policy events. |
| CQ11 | Diagnostic | 1 | Counts events without official source records; useful for integration-gap analysis. |
| CQ12 | Answered | 2 | Uses `matchedToSourceRecord`; confirms completion-stage provenance matching works. |
| CQ13 | Answered | 39 | Topic co-occurrence query exercises event-topic self-joins. |
| CQ14 | Answered | 1 | Compares news-organisation coverage of parliamentary versus government policy events. |
| CQ15 | Answered | 2 | Location aggregation is supported, though location extraction remains conservative. |
| CQ16 | Answered (noisy) | 8 | Actor-party-topic aggregation depends on actor and party typing quality. |
| CQ17 | Answered | 5 | Four-hop journalist-to-article-to-event-to-department chain works. |
| CQ18 | Answered | 11 | Finds topics on events involving both actors and government bodies. |
| CQ19 | Answered | 3 | Date-based co-occurrence between parliamentary events and ministerial statements. |
| CQ20 | Answered | 3 | Ranks publishers by distinct government departments covered through reported events. |

## Summary

- Query coverage: `20/20`
- Most robust areas: official source records, event-topic links, event-institution links, article-event reporting links.
- Main residual risk: extraction quality and event canonicalisation, not ontology/query alignment.
