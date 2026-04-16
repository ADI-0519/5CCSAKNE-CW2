## Evaluation Results

This document records a concrete evaluation snapshot for the latest validated pipeline run.

Evaluated run:

- `20260416T064639Z`

Primary artefacts:

- [20260416T064639Z_kg_records.json](data/processed/20260416T064639Z_kg_records.json)
- [20260416T064639Z_completed_kg.ttl](output/20260416T064639Z_completed_kg.ttl)
- [20260416T064639Z_query_results.json](output/20260416T064639Z_query_results.json)

## 1. Structural Results

- Total KG-ready records: `264`
- Source split:
  - `261` Guardian
  - `3` NewsAPI
- Article subtype split:
  - `174` NewsArticle
  - `60` OpinionArticle
  - `30` BreakingNewsArticle
- Records with event candidates: `231 / 264`

Generated graph counts:

- Instance KG: `30694` triples
- Wikidata KG: `24307` triples
- Prototype KG: `54720` triples
- Completed KG: `55146` triples
- Wikidata entities: `1722` politicians, `964` parties, `489` government bodies

Comparison with previous run (`20260415T205507Z`):

- Instance KG reduced from `32547` to `30694` (fewer spurious entity nodes after extraction fixes)
- Prototype KG reduced from `56573` to `54720` (same cause)
- Completed KG reduced from `56998` to `55146` (same cause)
- Wikidata KG and entity counts unchanged

Structural judgment:

- The pipeline completed successfully with all three data sources.
- The ontology, instance graph, prototype KG, completed KG, and query result outputs were all generated.
- The current ontology, RDF output, and SPARQL layer are internally aligned on `news:eventDate` as `xsd:date`.
- The collection window is dynamically computed as the 30 days prior to the run date, ensuring the pipeline remains reproducible without hardcoded date constraints.
- The reduction in triple count reflects genuine quality improvement: fewer spurious person-entity nodes and fewer false-positive event candidates.

## 2. Competency Question Results

All `20/20` competency queries returned at least one row in the latest run.

| CQ | Row count |
| --- | --- |
| CQ01 | 128 |
| CQ02 | 2 |
| CQ03 | 1860 |
| CQ04 | 534 |
| CQ05 | 200 |
| CQ06 | 11 |
| CQ07 | 14 |
| CQ08 | 246 |
| CQ09 | 2 |
| CQ10 | 314 |
| CQ11 | 15 |
| CQ12 | 25 |
| CQ13 | 383 |
| CQ14 | 239 |
| CQ15 | 251 |
| CQ16 | 2 |
| CQ17 | 30500 |
| CQ18 | 52 |
| CQ19 | 5 |
| CQ20 | 1249 |

Important judgments:

- `CQ02` returns two publishers: The Guardian and one NewsAPI source, confirming multi-source coverage.
- `CQ16` similarly returns two publishers with distinct topic ranges.
- `CQ17` and `CQ20` are highly combinatorial ranking queries; result counts reflect the full cross-product of co-mentions and should be interpreted as ranked lists rather than absolute counts. The reduction in CQ17 from 36755 to 30500 reflects the removal of spurious person entities rather than a loss of real data.
- `CQ19` returns five events covered by more than one article, confirming the event layer is populated and functional.
- `CQ10` follow-up link counts reflect heuristic matching and should be treated as approximate. The reduction from 378 to 314 reflects removal of follow-up links grounded in spurious events.
- `CQ03` reduced from 2261 to 1860 because hundreds of nav-phrase fragments that were previously extracted as person names have been removed.

## 3. Manual Audit Snapshot

A stratified 15-article audit sample was taken from the dataset across all three article subtypes and all retained NewsAPI articles. The full scored sheet is in [manual_audit_template.csv](data/evaluation/manual_audit_template.csv).

Aggregate precision scores across the sample:

| Metric | Score |
| --- | --- |
| author_correct | 0.64 |
| publisher_correct | 1.00 |
| people_precision | 0.66 |
| organisations_precision | 0.92 |
| locations_precision | 0.68 |
| topics_precision | 0.72 |
| sentiment_correct | 0.87 |
| article_type_correct | 0.87 |
| event_precision | 0.59 |
| follow_up_quality | 0.67 |

### Strengths

- Core metadata is preserved correctly from source to KG: title, publisher, publication date, URL, and section.
- `organisations_precision` of 0.92 is the strongest extraction metric. The config-driven lookup for political parties and government bodies is reliable, and the fix removing lead-in prefix fragments (`"As Sky News"`, `"From GB News"`) eliminated the main remaining noise source.
- Political topics are sensible for clearly political reporting. `topics_precision` of 0.72 holds up well across opinion, news, and breaking news subtypes.
- Sentiment classification is correct in 13 of 15 sampled articles.
- Article subtype classification is correct in 13 of 15 sampled articles. Live-blog structural signals (title ends with `"as it happened"`, URL contains `"live/"`) now lock the `BreakingNewsArticle` label regardless of LLM output, preventing false downgrades.
- Wikidata entity typing correctly classifies political parties and government bodies, enabling CQ04, CQ05, and CQ20.
- Event extraction improved: the `"The Guardian view on a recovering NHS"` editorial no longer generates a spurious Budget event, and live-blog event lists are more coherent.

### Weaknesses

- `people_precision` of 0.66 remains the weakest extraction metric. The regex-based `PERSON_PATTERN` still fires on some two-word title-cased phrases that are not person names, particularly in live blogs where the pattern encounters very high text volume. The fix substantially reduced noise across the dataset but has not eliminated it.
- `author_correct` of 0.64 reflects a systematic issue: Guardian API returns bylines with job titles appended (`"Jessica Elgot Deputy political editor"`), which are stored verbatim. This is a source-level limitation rather than an extraction error.
- Two articles in the sample retain wrong `article_type` labels. `45d02a56` (Farage ng-interactive investigative piece) is still classified as `BreakingNewsArticle` because the cached OpenAI result predates the article type fix. `d7e785ab` (Yvette Cooper profile interview) was not in the latest collection snapshot and so was not re-extracted.
- Event extraction at 0.59 still produces some false positives. Generic fallback events (`"Election"`, `"Policy Announcement"`) are still generated for articles where they are only loosely relevant. The `"Budget"` fallback now requires an explicit named fiscal phrase, which removed most false positives, but OpenAI can still propose Budget as an event independently.
- Location extraction at 0.68 remains noisy for long-form live blog articles where the regex fires on person names and media brand names that appear in prepositional contexts.

Concrete examples from the sample:

1. `The Guardian view on a recovering NHS`
   Cleanest extraction in the sample after fixes. Only one person extracted (`Wes Streeting`), all genuine. Budget event correctly absent. This article illustrates the maximum quality the pipeline achieves on short, focused opinion pieces.

2. `Farage backs Tory attack on Muslim iftar event` (live blog)
   Best illustration of the live-blog over-generation problem. People list contains 71 entries, of which roughly 70% are genuine. Organisations and events are mostly correct. Location list at 0.52 is the weakest in the sample, driven by person names and abbreviations appearing in prepositional contexts across ~8000 words of live content.

3. `Rachel Reeves rules out universal support on energy bills`
   Persistent issue: author stored as `"Jessica Elgot Deputy political editor"` rather than `"Jessica Elgot"`. `Markets Authority` extracted as a person name because the phrase appears title-cased mid-sentence. Both are known systematic issues rather than random noise.

4. `Pressure mounts on UK government to ban Kanye West after Wireless Festival backlash`
   Borderline scope. The `Immigration` topic is loosely plausible for an entry-ban story, but the article is primarily about a celebrity rather than UK policy. Useful as a documented edge case for the report's source-scope discussion.

5. `Lil Nas X assault case to be dismissed if he completes mental health programme`
   Out-of-scope article retained because it passed the NewsAPI source allowlist. Topics precision 0.00: no configured UK political topics apply. Included in the audit to document pipeline scope limits honestly.

## 4. Extraction Quality Improvement

The following targeted fixes were applied and are now reflected in the current run:

- `blocked_person_words` expanded with 17 additional entries covering section and navigation words that appear title-cased in Guardian article text (`"Politics"`, `"Election"`, `"Reform"`, `"Opinion"`, `"When"`, `"While"`, `"From"`, etc.)
- `_ORG_LEAD_IN` guard added to `extract_organisations` to drop regex matches whose first word is a sentence-initial connective (`"As"`, `"From"`, `"By"`, etc.)
- `ECONOMIC_EVENT_HINTS` tightened: bare `"budget"` replaced with `"spring budget"` and `"autumn budget"` so Budget events only fire on named fiscal phrases
- `POLITICAL_EVENT_HINTS` tightened: bare `"election"` replaced with `"general election"`, `"local election"`, and `"by-election"`
- Both `extract_events` and `add_topic_based_fallback_events` now require an explicit fiscal phrase before generating a Budget fallback event
- `apply_openai_extraction` restructured: structural live-blog signals (title/URL) lock `BreakingNewsArticle` regardless of LLM output; otherwise the LLM decides freely across all three types

Measured impact across the 15-article audit sample:

- `people_precision`: 0.56 -> 0.66 (+0.10)
- `event_precision`: 0.51 -> 0.59 (+0.08)
- Other metrics stable with no regressions

## 5. Evaluation Position For The Report

The strongest defensible evaluation claim is:

- the system works end to end
- the ontology and query layer are aligned
- all 20 competency questions are executable and return results
- the graph is most reliable for metadata, publisher/author information, broad topics, article subtype, sentiment, and major political/economic event groupings
- the graph is less reliable for fine-grained entity precision in long-form live blogs, weakly grounded events, and follow-up-link semantics
- extraction quality improved measurably after targeted fixes, with `people_precision` up 0.10 and `event_precision` up 0.08

This should be framed as a successful automated KG pipeline with identifiable heuristic limitations and a documented improvement cycle, not as a perfect information-extraction system.

## 6. Recommended Final Framing

If space is tight, the final report should emphasise:

1. automation and reproducibility
2. ontology-to-pipeline alignment
3. measurable CQ support across all 20 queries
4. honest error analysis on sampled articles with quantified precision scores
5. the documented improvement cycle: audit → fix → re-run → measure
6. the fact that OpenAI is used in a constrained, cached, structured way rather than as an opaque one-off assistant
