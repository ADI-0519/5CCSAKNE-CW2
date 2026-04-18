# Final Competency Questions

This document contains the current competency-question design for the coursework.

Project scope:

`A knowledge graph for UK parliamentary and government policy events reported in UK news during a fixed time window, using automated mappings from textual and structured sources, with OpenAI used critically for augmentation, extraction support, completion, and evaluation baselines.`

The first 10 questions below are the revised manually authored set. They are intentionally event-centred and are designed to drive the ontology redesign before the SPARQL layer is rewritten. The LLM-assisted 10 should be generated later so they complement this set rather than duplicating it.

Implementation difficulty and runtime support should be tracked separately in [cq_coverage_table.md](docs/cq_coverage_table.md).

## Manual Competency Questions

`CQ01.` Which parliamentary debates in the selected time window concern which policy topics?

`CQ02.` Which ministerial statements in the selected time window are issued by which government departments?

`CQ03.` Which political actors are involved in more than one policy event during the selected time window?

`CQ04.` Which policy events are reported by news articles and are also represented in official parliamentary or government sources?

`CQ05.` Which policy topics are common to both parliamentary events and government policy events during the selected time window?

`CQ06.` Which parliamentary bodies are linked to events concerning a given policy topic during the selected time window?

`CQ07.` Which government departments are involved in the highest number of policy events during the selected time window?

`CQ08.` Which political parties have members involved in events concerning more than one policy topic?

`CQ09.` Which reported policy events lack a linked government body, parliamentary body, or policy topic in the knowledge graph?

`CQ10.` Which policy topics are most frequently linked to parliamentary and government policy events reported during the selected time window?

## CQ-To-Ontology Mapping

This table records the minimum ontology support each manual CQ requires. It should drive the redesign of [news_ontology.ttl](5CCSAKNE-CW2/ontology/news_ontology.ttl) and [build_ontology.py](5CCSAKNE-CW2/src/build_ontology.py).

| CQ | Main classes justified | Main properties justified | Query shape / strict-marker rationale |
| --- | --- | --- | --- |
| CQ01 | `ParliamentaryDebate`, `PolicyTopic` | `concernsPolicyTopic`, `occursOnDate` | Event-topic retrieval; not article lookup; supports temporal filtering. |
| CQ02 | `MinisterialStatement`, `GovernmentDepartment` | `issuedByDepartment`, `occursOnDate` | Official-source event-to-institution linkage; justifies department modelling. |
| CQ03 | `PoliticalActor`, `PolicyEvent` | `involvesActor`, `occursOnDate` | Aggregation with `COUNT` / `HAVING`; easy to construct boundary cases. |
| CQ04 | `PolicyEvent`, `NewsArticle`, `ParliamentaryEvent`, `GovernmentPolicyEvent` | `reportedByArticle`, `representedInOfficialSource`, `matchedToSourceRecord` | Cross-source integration question; validates multi-source KG design without overclaiming identity. |
| CQ05 | `PolicyTopic`, `ParliamentaryEvent`, `GovernmentPolicyEvent` | `concernsPolicyTopic` | Tests whether event subclasses are meaningfully distinguished but still connected by shared topics. |
| CQ06 | `ParliamentaryBody`, `PolicyEvent`, `PolicyTopic` | `occursInParliamentaryBody`, `concernsPolicyTopic`, `occursOnDate` | Institution-event-topic linkage; supports non-trivial joins. |
| CQ07 | `GovernmentDepartment`, `PolicyEvent` | `involvesGovernmentBody`, `occursOnDate` | Ranking / `ORDER BY` / `LIMIT`; requires true aggregation cases. |
| CQ08 | `PoliticalParty`, `PoliticalActor`, `PolicyEvent`, `PolicyTopic` | `memberOfParty`, `involvesActor`, `concernsPolicyTopic` | Multi-hop party-actor-event-topic query; stronger than simple party mention lookup. |
| CQ09 | `PolicyEvent`, `GovernmentBody`, `ParliamentaryBody`, `PolicyTopic` | missing-link detection over `involvesGovernmentBody`, `occursInParliamentaryBody`, `concernsPolicyTopic` | Completion-oriented CQ; explicitly supports incompleteness analysis. |
| CQ10 | `PolicyTopic`, `ParliamentaryEvent`, `GovernmentPolicyEvent`, `NewsArticle` | `concernsPolicyTopic`, `reportedByArticle` | Frequency / topic ranking query; supports counterexamples and meaningful limits. |

## LLM-Assisted Competency Questions

The LLM-assisted 10 should be designed after the ontology redesign and should complement the manual set across question types:

- boolean questions
- comparative questions
- additional aggregation questions
- completion/incompleteness questions
- cross-source validation questions
- reasoning-aware questions that test inferred class or relation membership

They should not simply paraphrase the manual 10 or fall back to article-mention lookup.

## Notes

- This revised manual set is intentionally more TBox-aware and less ABox-retrieval-heavy than the earlier article-centric version.
- The wording has been tightened to avoid vague relations such as `associated with` where more explicit ontology links are intended.
- The set is designed to be safer against the CW1 feedback pattern: weak class-role distinctions, shallow retrieval CQs, and SPARQL that lacks meaningful aggregation or boundary cases.
