# CQ Coverage Table

This table records how each competency question maps to the current pipeline and what results it produces. The support assessment reflects the final pipeline state, including Wikidata-based entity typing and OpenAI-assisted triple completion. All 20 queries return results.

Classification legend:

- `Answered`: query returns clean, meaningful results grounded in well-populated data.
- `Answered (noisy)`: query returns results but the underlying data has known quality issues such as over-extraction, heuristic links, or unvalidated classifications.
- `Partial`: query returns results but only for a subset of the intended question due to data gaps.

| CQ | Classification | Result count | Notes |
| --- | --- | --- | --- |
| CQ01 | Answered (noisy) | 132 | journalist-author deduplication is weak |
| CQ02 | Answered | 2 | Guardian and one NewsAPI source pass the politics-section filter |
| CQ03 | Answered (noisy) | 2261 | person entity disambiguation is still heuristic |
| CQ04 | Answered (noisy) | 547 | PoliticalParty typing from Wikidata, not all article mentions resolved |
| CQ05 | Answered (noisy) | 212 | GovernmentBody typing from Wikidata, article-level classification still heuristic |
| CQ06 | Answered (noisy) | 12 | sentiment from OpenAI completion, not validated against ground truth |
| CQ07 | Answered | 14 | topic coverage is flat, no hierarchy |
| CQ08 | Answered | 254 | direct metadata mapping, no extraction needed |
| CQ09 | Answered | 2 | one row per article group, clean comparison |
| CQ10 | Answered (noisy) | 378 | follow-up links are heuristic keyword matches |
| CQ11 | Answered (noisy) | 15 | worksFor derived per-article, not from canonical profiles |
| CQ12 | Answered (noisy) | 26 | BreakingNewsArticle classification is keyword-based |
| CQ13 | Answered (noisy) | 394 | location extraction is regex-based |
| CQ14 | Answered | 246 | metadata-driven, reliable |
| CQ15 | Answered | 259 | both person and organisation triples well-populated |
| CQ16 | Answered (noisy) | 2 | Guardian-dominant dataset limits publisher range |
| CQ17 | Answered (noisy) | 36755 | combinatorial co-mention space, results need careful interpretation |
| CQ18 | Answered (noisy) | 50 | event location matching is string comparison only |
| CQ19 | Answered (noisy) | 5 | event canonicalisation is heuristic |
| CQ20 | Answered (noisy) | 1269 | politician and party typing from Wikidata, article-level co-mention is reliable |
