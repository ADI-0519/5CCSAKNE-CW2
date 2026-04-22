# baseline comparison: KG-backed SPARQL vs direct LLM

| CQ | prototype count | completed count | delta | LLM answer |
|----|-----------------|-----------------|-------|------------|
| CQ04 | 134 | 134 | +0 | During March to April 2026, several key policy events reported in news articles ... |
| CQ11 | 117 | 123 | +6 | In March to April 2026, several key policy events involved UK government departm... |
| CQ12 | 11 | 11 | +0 | During March to April 2026, the most frequently linked policy topics in UK polit... |
| CQ16 | 7 | 7 | +0 | In the UK political landscape from March to April 2026, several political actors... |
| CQ18 | 11 | 12 | +1 | In the period from March to April 2026, key policy topics involving both politic... |

**CQ04**: completion did not change the row count for CQ04; the relevant triples were already present in the prototype
**CQ11**: completion added 6 rows for CQ11 that SPARQL can traverse but the LLM cannot ground in the actual dataset
**CQ12**: completion did not change the row count for CQ12; the relevant triples were already present in the prototype
**CQ16**: completion did not change the row count for CQ16; the relevant triples were already present in the prototype
**CQ18**: completion added 1 row for CQ18 that SPARQL can traverse but the LLM cannot ground in the actual dataset
