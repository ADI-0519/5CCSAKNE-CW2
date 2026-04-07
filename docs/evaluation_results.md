# Evaluation Results

This document records a concrete evaluation snapshot for the latest validated pipeline run.

Evaluated run:

- `20260407T010208Z`

Primary artefacts:

- [20260407T010208Z_kg_records.json](/c:/Users/adirj/OneDrive/Documents/GitHub/5CCSAKNE-CW2/data/processed/20260407T010208Z_kg_records.json)
- [20260407T010208Z_completed_kg.ttl](/c:/Users/adirj/OneDrive/Documents/GitHub/5CCSAKNE-CW2/output/20260407T010208Z_completed_kg.ttl)
- [20260407T010208Z_query_results.json](/c:/Users/adirj/OneDrive/Documents/GitHub/5CCSAKNE-CW2/output/20260407T010208Z_query_results.json)

## 1. Structural Results

- Total KG-ready records: `258`
- Source split:
  - `255` Guardian
  - `3` NewsAPI
- Article subtype split:
  - `172` `NewsArticle`
  - `60` `OpinionArticle`
  - `26` `BreakingNewsArticle`
- Sentiment split:
  - `132` Negative
  - `99` Neutral
  - `27` Positive
- Records with event candidates: `228`
- Records with follow-up candidates before RDF completion: `24`

Generated graph counts:

- Prototype KG:
  - `229` `news:coversEvent`
  - `14` `news:hasFollowUp`
  - `124` `news:worksFor`
  - `259` `news:hasSentiment`
- Completed KG:
  - `229` `news:coversEvent`
  - `90` `news:hasFollowUp`
  - `124` `news:worksFor`
  - `259` `news:hasSentiment`

Structural judgment:

- The pipeline completed successfully.
- The ontology, instance graph, prototype KG, completed KG, and query result outputs were all generated.
- The current ontology, RDF output, and SPARQL layer are internally aligned on `news:eventDate` as `xsd:date`.

## 2. Competency Question Results

All `20/20` competency queries returned at least one row in the latest run.

Notable query counts:

- `CQ02`: `3`
- `CQ06`: `9`
- `CQ10`: `297`
- `CQ17`: `30900`
- `CQ18`: `21`
- `CQ19`: `2`

Important judgments:

- `CQ02` is now clean and defensible:
  - `BBC News`
  - `The Guardian`
  - `The Irish Times`
- `CQ19` is now supported and returns:
  - `Election`
  - `Policy Announcement`
- `CQ10` remains heuristic and somewhat noisy.
- `CQ17` is technically answerable but highly combinatorial, so it should be interpreted carefully in the report rather than treated as a neat ranked fact list.

## 3. Manual Audit Snapshot

A stratified audit sample was taken from the latest run across:

- `NewsArticle`
- `OpinionArticle`
- `BreakingNewsArticle`
- all retained NewsAPI articles

Initial qualitative findings from the sample:

### Strengths

- Core metadata is generally preserved correctly from source to KG:
  - title
  - publisher
  - publication date
  - URL
  - section
- Political topics are often sensible for clearly political reporting.
- Event canonicalisation improved cross-publisher event grouping enough to support `CQ19`.
- Source filtering removed many previously off-scope NewsAPI publishers.

### Weaknesses

- Person and organisation extraction still over-generates in some cases.
- Some location extraction is clearly noisy.
- Some event labels remain too generic or synthetic.
- Follow-up links improved substantially but are still heuristic.
- A small amount of off-scope or weakly related NewsAPI material still remains.

Concrete examples from the sample:

1. [20260407T010208Z_kg_records.json](/c:/Users/adirj/OneDrive/Documents/GitHub/5CCSAKNE-CW2/data/processed/20260407T010208Z_kg_records.json)
   `Rachel Reeves rules out universal support on energy bills`
   Good overall topic fit, but extracted people include suspicious names such as `Markets Authority`.

2. [20260407T010208Z_kg_records.json](/c:/Users/adirj/OneDrive/Documents/GitHub/5CCSAKNE-CW2/data/processed/20260407T010208Z_kg_records.json)
   `Senior Labour figures warn government amid fears of ‘political earthquake’ in London`
   Election/event structure is useful, but people and location lists contain noisy labels like `London Exclusive` and `Deltapoll`.

3. [20260407T010208Z_kg_records.json](/c:/Users/adirj/OneDrive/Documents/GitHub/5CCSAKNE-CW2/data/processed/20260407T010208Z_kg_records.json)
   `UK has detained 76 ‘age-disputed’ children under one in, one out scheme`
   Correctly captures immigration focus, but event extraction includes an arguably spurious `Election` event.

4. [20260407T010208Z_kg_records.json](/c:/Users/adirj/OneDrive/Documents/GitHub/5CCSAKNE-CW2/data/processed/20260407T010208Z_kg_records.json)
   `Pressure mounts on UK government to ban Kanye West after Wireless Festival backlash`
   Useful for showing that cross-source policy-event coverage now exists, but it is still only weakly political and should be described honestly as borderline scope.

5. [20260407T010208Z_kg_records.json](/c:/Users/adirj/OneDrive/Documents/GitHub/5CCSAKNE-CW2/data/processed/20260407T010208Z_kg_records.json)
   `Trump endorses ex-UK political aide Steve Hilton for California governor`
   Retains a relevant `Election` event, but the article is still only indirectly about UK politics.

## 4. Evaluation Position For The Report

The strongest defensible evaluation claim is:

- the system works end to end
- the ontology and query layer are aligned
- all competency questions are executable and return results
- the graph is most reliable for metadata, publisher/author information, broad topics, article subtype, sentiment, and major political/economic event groupings
- the graph is less reliable for fine-grained entity precision, weakly grounded events, and follow-up-link semantics

This should be framed as a successful automated KG pipeline with identifiable heuristic limitations, not as a perfect information-extraction system.

## 5. What Still Needs To Be Added

To complete the evaluation section properly, the team should still add:

- a manually annotated audit sheet using the sample in [manual_audit_template.csv](/c:/Users/adirj/OneDrive/Documents/GitHub/5CCSAKNE-CW2/data/evaluation/manual_audit_template.csv)
- a short table comparing prototype KG versus completed KG
- a short table classifying each competency question as:
  - answered
  - answered but noisy
  - partially answered

## 6. Recommended Final Framing

If space is tight, the final report should emphasise:

1. automation and reproducibility
2. ontology-to-pipeline alignment
3. measurable CQ support
4. honest error analysis on sampled articles
5. the fact that OpenAI is used in a constrained, cached, structured way rather than as an opaque one-off assistant
