# baseline comparison: KG-backed SPARQL vs direct LLM

| CQ | prototype count | completed count | delta | LLM answer |
|----|-----------------|-----------------|-------|------------|
| CQ04 | 233 | 237 | +4 | During March to April 2026, several key policy events reported by news articles ... |
| CQ11 | 212 | 224 | +12 | To identify specific policy events in the UK from March to April 2026, one typic... |
| CQ12 | 11 | 12 | +1 | During March to April 2026, the most frequently linked policy topics in UK polit... |
| CQ16 | 5 | 5 | +0 | In March to April 2026, several political actors in the UK were involved in key ... |
| CQ18 | 11 | 12 | +1 | In March to April 2026 UK politics, key policy topics involving both political a... |

**CQ04**: completion added 4 rows for CQ04 that SPARQL can traverse but the LLM cannot ground in the actual dataset
**CQ11**: completion added 12 rows for CQ11 that SPARQL can traverse but the LLM cannot ground in the actual dataset
**CQ12**: completion added 1 row for CQ12 that SPARQL can traverse but the LLM cannot ground in the actual dataset
**CQ16**: completion did not change the row count for CQ16; the relevant triples were already present in the prototype
**CQ18**: completion added 1 row for CQ18 that SPARQL can traverse but the LLM cannot ground in the actual dataset
