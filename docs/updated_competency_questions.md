# Competency Questions

This document captures the revised 20 competency questions for the current UK politics and policy news KG.

The questions are written for the following scope:

`Current UK politics and policy news from March 1, 2026 to April 6, 2026, collected from GuardianAPI and NewsAPI, with OpenAI used for extraction, classification, and completion.`

The first 10 questions are the manually developed set. The second 10 were LLM assisted and then reviewed and rewritten so that they better fit the project scope, ontology, and likely pipeline outputs.

Each competency question is intended to have a matching SPARQL query in `queries/news_competency_queries.rq`.

## Manual Competency Questions

`CQ01.` Which journalists wrote articles about UK government policy announcements during the project time window?

`CQ02.` Which news organisations published politics section articles between March 1, 2026 and April 6, 2026?

`CQ03.` Which politicians were mentioned most often across the full article collection?

`CQ04.` Which political parties were mentioned in articles about elections, parliamentary votes, or leadership contests?

`CQ05.` Which government bodies were mentioned in articles about taxation, public spending, or economic policy?

`CQ06.` Which political events took place in London during the project time window, and when did they occur?

`CQ07.` Which political events were covered by more than one news organisation?

`CQ08.` Which opinion articles were classified as negative in sentiment?

`CQ09.` Which topics appeared most often in politics-section reporting during the chosen period?

`CQ10.` Which articles were updated after their original publication time?

## LLM-Augmented Competency Questions

`CQ11.` Which journalists from the same news organisation covered the same political event?

`CQ12.` Which breaking news articles published in the politics section were linked to a political event?

`CQ13.` Which economic events were reported by both The Guardian and at least one other publisher in the dataset?

`CQ14.` Which places were mentioned most often in articles about immigration, taxation, or NHS policy?

`CQ15.` Which journalists wrote both standard news reports and opinion pieces during the chosen period?

`CQ16.` How does the average word count of politics articles compare with the average word count of opinion articles?

`CQ17.` Which politicians and political parties were mentioned together most often in the same articles?

`CQ18.` Which articles have a follow-up article, and do the original and follow-up share at least one topic?

`CQ19.` Which events were described with both positive and negative sentiment across different articles?

`CQ20.` Which politicians were mentioned by more than three different news organisations in the dataset?

## Notes On The Revision

- This version drops the older generic technology-news framing and focuses fully on UK politics and policy news.
- The questions are deliberately varied rather than mechanically following the same template.
- The set is intended to cover the key ontology areas: article types, publishers, journalists, politicians, parties, government bodies, events, event dates, locations, sentiment, follow-up links, dates, sections, and article updates.
