# Final Competency Questions

This document contains the current competency-question design for the coursework.

Project scope:

`A knowledge graph for UK parliamentary and government policy events reported in UK news during a fixed time window, using automated mappings from textual and structured sources, with OpenAI used critically for augmentation, extraction support, and evaluation baselines.`

The first 10 questions below are the revised manually authored set. The second 10 are LLM-assisted questions that were reviewed and edited manually so they complement the manual set rather than duplicating it.

Implementation difficulty and runtime support should be tracked separately in [cq_coverage_table.md](cq_coverage_table.md).

## Manual Competency Questions

`CQ01.` Which parliamentary debates in the selected time window concern which policy topics?

`CQ02.` Which ministerial statements in the selected time window are issued by which government departments?

`CQ03.` Which political actors are involved in more than one policy event during the selected time window?

`CQ04.` Which policy events are reported by news articles and are also represented in official parliamentary or government sources?

`CQ05.` Which policy topics are common to both parliamentary events and government policy events during the selected time window?

`CQ06.` Which parliamentary bodies do events concerning a given policy topic occur in during the selected time window?

`CQ07.` Which government departments are involved in the highest number of policy events during the selected time window?

`CQ08.` Which political parties have members involved in events concerning more than one policy topic?

`CQ09.` Which reported policy events lack a linked government body, parliamentary body, or policy topic in the knowledge graph?

`CQ10.` Which policy topics are most frequently linked to parliamentary and government policy events reported during the selected time window?

## CQ-To-Ontology Mapping

This table records the minimum ontology support each CQ requires. It is aligned with [news_ontology.ttl](../ontology/news_ontology.ttl), [build_ontology.py](../src/build_ontology.py), and [news_competency_queries.rq](../queries/news_competency_queries.rq).

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
| CQ09 | `PolicyEvent`, `OfficialBody`, `GovernmentBody`, `ParliamentaryBody`, `PolicyTopic` | missing-link detection over `involvesGovernmentBody`, `occursInParliamentaryBody`, `concernsPolicyTopic` | Completion-oriented CQ over the relevant subclasses of `OfficialBody`; explicitly supports incompleteness analysis. |
| CQ10 | `PolicyTopic`, `ParliamentaryEvent`, `GovernmentPolicyEvent`, `NewsArticle` | `concernsPolicyTopic`, `reportedByArticle` | Frequency / topic ranking query; supports counterexamples and meaningful limits. |
| CQ11 | `PolicyEvent`, `OfficialSourceRecord`, `GovernmentDepartment` | `representedInOfficialSource`, `involvesGovernmentBody`, `occursOnDate` | Cross-source institutional linkage; extends CQ04 toward department-level analysis without duplicating ministerial statements. |
| CQ12 | `PolicyTopic`, `PolicyEvent`, `OfficialSourceRecord` | `concernsPolicyTopic`, `representedInOfficialSource`, `occursOnDate` | Topic aggregation over officially evidenced events; complements CQ10 with an official-source perspective. |
| CQ13 | `PolicyEvent`, `PolicyTopic` | `concernsPolicyTopic`, `occursOnDate` | Topic co-occurrence via self-join with `HAVING`; non-trivial join pattern. |
| CQ14 | `PolicyTopic`, `ParliamentaryEvent`, `GovernmentPolicyEvent` | `concernsPolicyTopic`, `occursOnDate` | Comparative topic coverage counts across event subclasses; domain-centred counterpart to CQ05 and CQ10 without assuming one side dominates. |
| CQ15 | `Location`, `PolicyEvent` | `occursInLocation`, `occursOnDate` | Location aggregation; exercises the geographic dimension of the event model. |
| CQ16 | `PoliticalActor`, `PoliticalParty`, `PolicyEvent`, `PolicyTopic` | `memberOfParty`, `involvesActor`, `concernsPolicyTopic`, `occursOnDate` | Per-actor multi-topic aggregation; distinct from CQ08 which aggregates at party level. |
| CQ17 | `Journalist`, `NewsArticle`, `PolicyEvent`, `GovernmentDepartment` | `hasAuthor`, `reportedByArticle`, `involvesGovernmentBody` | Journalist-level aggregation over department-linked coverage; source-dependent because byline metadata is only available where article authors are captured reliably. |
| CQ18 | `PolicyTopic`, `PolicyEvent`, `PoliticalActor`, `GovernmentBody` | `involvesActor`, `involvesGovernmentBody`, `concernsPolicyTopic` | Multi-constraint intersection query; tests joint actor-institution-topic linkage on the same event. |
| CQ19 | `ParliamentaryEvent`, `MinisterialStatement`, `PolicyTopic` | `occursOnDate`, `concernsPolicyTopic` | Temporal-topic overlap across disjoint event subclasses; stronger than weak date-only co-occurrence and better aligned to what the KG can support reliably. |
| CQ20 | `GovernmentDepartment`, `PolicyEvent`, `PolicyTopic` | `involvesGovernmentBody`, `concernsPolicyTopic`, `occursOnDate` | Department-topic breadth ranking; domain-facing aggregation over institutional policy scope. |

## LLM-Assisted Competency Questions

`CQ11.` Which policy events in the selected time window are represented in official source records and also involve a government department?

`CQ12.` Which policy topics are most frequently linked to policy events represented in official source records during the selected time window?

`CQ13.` Which pairs of policy topics co-occur across more than one policy event during the selected time window?

`CQ14.` How many parliamentary events and government policy events are linked to each policy topic during the selected time window?

`CQ15.` Which locations are linked to more than one distinct policy event during the selected time window?

`CQ16.` Which political actors are individually involved in events spanning at least two distinct policy topics, and which party do they belong to?

`CQ17.` Which journalists authored more than one article reporting on policy events that involve a government department?

`CQ18.` Which policy topics appear in events that involve both a political actor and a government body?

`CQ19.` Which policy topics are shared by parliamentary events and ministerial statements occurring on the same date?

`CQ20.` Which government departments are involved in policy events spanning the widest range of policy topics during the selected time window?

## Notes

- This revised manual set is intentionally more TBox-aware and less ABox-retrieval-heavy than the earlier article-centric version.
- The wording has been tightened to avoid vague relations such as `associated with` where more explicit ontology links are intended.
- `OfficialBody` is the superclass for official institutions in scope, with `GovernmentBody` and `ParliamentaryBody` used where the CQs need subclass-level distinctions.
