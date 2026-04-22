# baseline comparison: KG-backed SPARQL vs direct LLM

| CQ | prototype count | completed count | delta | LLM answer |
|----|-----------------|-----------------|-------|------------|
| CQ04 | 233 | 235 | +2 | During March to April 2026, several key policy events in UK politics were report... |
| CQ11 | 212 | 221 | +9 | From March to April 2026, several key policy events involving UK government depa... |
| CQ12 | 11 | 12 | +1 | During the period from March to April 2026, the most frequently linked policy to... |
| CQ16 | 7 | 7 | +0 | As of March to April 2026, several political actors have been prominent in event... |
| CQ18 | 15 | 15 | +0 | In the UK from March to April 2026, notable policy topics involving both politic... |

**CQ04**: completion added 2 rows for CQ04 that SPARQL can traverse but the LLM cannot ground in the actual dataset
**CQ11**: completion added 9 rows for CQ11 that SPARQL can traverse but the LLM cannot ground in the actual dataset
**CQ12**: completion added 1 row for CQ12 that SPARQL can traverse but the LLM cannot ground in the actual dataset
**CQ16**: completion did not change the row count for CQ16; the relevant triples were already present in the prototype
**CQ18**: completion did not change the row count for CQ18; the relevant triples were already present in the prototype
