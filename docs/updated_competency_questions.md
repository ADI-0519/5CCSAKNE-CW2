# Final Competency Questions

This document contains the final wording for the 20 competency questions used in the coursework.

Project scope:

`A knowledge graph for current UK politics and policy news, using articles published between March 1, 2026 and April 6, 2026 from GuardianAPI and NewsAPI, with OpenAI used for extraction, classification, and completion.`

The first 10 questions are the manually authored set. The second 10 were LLM-assisted and then revised so they align with the fixed time window, the current ontology, and the planned pipeline outputs.

Implementation difficulty and current pipeline support are tracked separately in [cq_coverage_table.md](/home/kasim/5CCSAKNE-CW2/docs/cq_coverage_table.md).

## Manual Competency Questions

`CQ01.` Which journalists wrote politics-section articles about government or policy issues during the project time window?

`CQ02.` Which news organisations published politics-section articles between March 1, 2026 and April 6, 2026?

`CQ03.` Which people were mentioned most often across the fixed article collection?

`CQ04.` Which political parties were mentioned in articles about elections or parliamentary politics?

`CQ05.` Which government bodies were mentioned in articles about tax, public services, or healthcare policy?

`CQ06.` Which opinion articles were classified as negative in sentiment?

`CQ07.` Which topics appeared most often in politics-section reporting during the project time window?

`CQ08.` Which articles were updated after their original publication time, and what are their canonical URLs?

`CQ09.` How does the average word count of politics-section articles compare with the average word count of opinion articles?

`CQ10.` Which articles have a follow-up article, and do the original and follow-up share at least one topic?

## LLM-Assisted Competency Questions

`CQ11.` Which journalists from the same news organisation wrote about the same topic during the project time window?

`CQ12.` Which breaking news articles were published in the politics section?

`CQ13.` Which locations were mentioned most often in articles about migration, tax, or healthcare policy?

`CQ14.` Which journalists wrote articles that were later updated?

`CQ15.` Which articles mention both a person and an organisation?

`CQ16.` Which news organisations published the widest range of topics during the project time window?

`CQ17.` Which people and organisations were co-mentioned most often in the same articles?

`CQ18.` Which political events took place in London during the project time window, and when did they occur?

`CQ19.` Which political or economic events were covered by more than one news organisation?

`CQ20.` Which politicians and political parties were mentioned together most often in the same articles?

## Notes

- This set is now fully aligned to the fixed March 1, 2026 to April 6, 2026 dataset window.
- The wording avoids the earlier generic news and technology framing.
- The blocked questions were kept deliberately where they exercise ontology areas that still need modelling work, especially `news:worksFor`, event modelling, and political-actor classification.
