# CQ Coverage Table

This table records how each competency question maps to the current pipeline and what results it produces. The support assessment reflects the final pipeline state, including Wikidata-based entity typing and OpenAI-assisted triple completion. All 20 queries return results.

Classification legend:

- `Answered`: query returns clean, meaningful results grounded in well-populated data.
- `Answered (noisy)`: query returns results but the underlying data has known quality issues such as over-extraction, heuristic links, or unvalidated classifications.
- `Partial`: query returns results but only for a subset of the intended question due to data gaps.

| CQ | Classification | Result count | Notes |
| --- | --- | --- | --- |
| CQ01 | Answered (noisy) | 128 | journalist-author deduplication is weak; Guardian bylines include appended job titles |
| CQ02 | Answered | 2 | Guardian and one NewsAPI source pass the politics-section filter |
| CQ03 | Answered (noisy) | 1860 | person entity list is now cleaner after extraction fixes; count reduction from 2261 reflects removal of spurious nav-phrase entries |
| CQ04 | Answered (noisy) | 534 | PoliticalParty typing from Wikidata; not all article-extracted mentions resolved |
| CQ05 | Answered (noisy) | 200 | GovernmentBody typing from Wikidata; article-level classification still heuristic |
| CQ06 | Answered (noisy) | 11 | sentiment from combined heuristic and OpenAI completion; not validated against ground truth |
| CQ07 | Answered | 14 | topic coverage is flat with no hierarchy |
| CQ08 | Answered | 246 | direct metadata mapping, no extraction needed |
| CQ09 | Answered | 2 | one row per article group, clean comparison |
| CQ10 | Answered (noisy) | 314 | follow-up links are heuristic; count reduction from 378 reflects removal of links grounded in spurious events |
| CQ11 | Answered (noisy) | 15 | worksFor derived per-article, not from canonical journalist profiles |
| CQ12 | Answered (noisy) | 25 | live-blog classification now locked by structural title/URL signals; body-keyword-only cases remain heuristic |
| CQ13 | Answered (noisy) | 383 | location extraction is regex-based and still noisy in long-form live blog articles |
| CQ14 | Answered | 239 | metadata-driven, reliable |
| CQ15 | Answered | 251 | both person and organisation triples well-populated; slight reduction reflects articles that had only spurious person mentions |
| CQ16 | Answered (noisy) | 2 | Guardian-dominant dataset limits publisher range |
| CQ17 | Answered (noisy) | 30500 | combinatorial co-mention space; count reduction from 36755 reflects removal of spurious person nodes, not loss of real data |
| CQ18 | Answered (noisy) | 52 | event location matching is string comparison only; slight increase reflects more policy events correctly assigned London location |
| CQ19 | Answered (noisy) | 5 | event canonicalisation is heuristic |
| CQ20 | Answered (noisy) | 1249 | politician and party typing from Wikidata; article-level co-mention is reliable |
