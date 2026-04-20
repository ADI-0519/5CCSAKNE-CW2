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

`CQ06.` Which parliamentary bodies are linked to events concerning a given policy topic during the selected time window?

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
| CQ09 | `PolicyEvent`, `GovernmentBody`, `ParliamentaryBody`, `PolicyTopic` | missing-link detection over `involvesGovernmentBody`, `occursInParliamentaryBody`, `concernsPolicyTopic` | Completion-oriented CQ; explicitly supports incompleteness analysis. |
| CQ10 | `PolicyTopic`, `ParliamentaryEvent`, `GovernmentPolicyEvent`, `NewsArticle` | `concernsPolicyTopic`, `reportedByArticle` | Frequency / topic ranking query; supports counterexamples and meaningful limits. |
| CQ11 | `PolicyEvent`, `OfficialSourceRecord` | `representedInOfficialSource` | Counting with `NOT EXISTS`; interlinking completeness metric (Week 10). |
| CQ12 | `SourceRecord`, `PolicyEvent` | `matchedToSourceRecord`, `sourceSystem` | Provenance aggregation; validates three-source integration story. |
| CQ13 | `PolicyEvent`, `PolicyTopic` | `concernsPolicyTopic`, `occursOnDate` | Topic co-occurrence via self-join with `HAVING`; non-trivial join pattern. |
| CQ14 | `NewsOrganisation`, `NewsArticle`, `ParliamentaryEvent`, `GovernmentPolicyEvent` | `publishedBy`, `reportedByArticle` | Comparative coverage counts for parliamentary versus government policy events; exercises subtype distinction without assuming a non-empty winner set. |
| CQ15 | `Location`, `PolicyEvent` | `occursInLocation`, `occursOnDate` | Location aggregation; exercises the geographic dimension of the event model. |
| CQ16 | `PoliticalActor`, `PoliticalParty`, `PolicyEvent`, `PolicyTopic` | `memberOfParty`, `involvesActor`, `concernsPolicyTopic`, `occursOnDate` | Per-actor multi-topic aggregation; distinct from CQ08 which aggregates at party level. |
| CQ17 | `Journalist`, `NewsArticle`, `PolicyEvent`, `GovernmentDepartment` | `hasAuthor`, `reportedByArticle`, `involvesGovernmentBody` | Four-hop retrieval linking reporters to institutional involvement. |
| CQ18 | `PolicyTopic`, `PolicyEvent`, `PoliticalActor`, `GovernmentBody` | `involvesActor`, `involvesGovernmentBody`, `concernsPolicyTopic` | Multi-constraint intersection query; tests joint actor-institution-topic linkage on the same event. |
| CQ19 | `ParliamentaryEvent`, `MinisterialStatement` | `occursOnDate` | Temporal co-occurrence across disjoint event subclasses; tests date-based reasoning. |
| CQ20 | `NewsOrganisation`, `NewsArticle`, `PolicyEvent`, `GovernmentDepartment` | `publishedBy`, `reportedByArticle`, `involvesGovernmentBody` | Ranking query over 3-hop chain; measures institutional breadth of news coverage per publisher. |

## LLM-Assisted Competency Questions

`CQ11.` How many policy events in the knowledge graph have no linked official source record?

`CQ12.` Which source systems contributed records matched to policy events in the knowledge graph, and how many matched events does each system account for?

`CQ13.` Which pairs of policy topics co-occur across more than one policy event during the selected time window?

`CQ14.` How many articles did each news organisation publish reporting on parliamentary events versus government policy events during the selected time window?

`CQ15.` Which locations are linked to more than one distinct policy event during the selected time window?

`CQ16.` Which political actors are individually involved in events spanning at least two distinct policy topics, and which party do they belong to?

`CQ17.` Which journalists authored articles that report on events involving a government department?

`CQ18.` Which policy topics appear in events that involve both a political actor and a government body?

`CQ19.` Which parliamentary events share an occurrence date with at least one ministerial statement?

`CQ20.` Which news organisations published the most articles reporting on events that involved government departments, ranked by number of distinct departments covered?

## Notes

- This revised manual set is intentionally more TBox-aware and less ABox-retrieval-heavy than the earlier article-centric version.
- The wording has been tightened to avoid vague relations such as `associated with` where more explicit ontology links are intended.
- The set is designed to be safer against the CW1 feedback pattern: weak class-role distinctions, shallow retrieval CQs, and SPARQL that lacks meaningful aggregation or boundary cases.
