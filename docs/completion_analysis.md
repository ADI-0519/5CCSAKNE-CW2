# Completion Analysis

This document records the remaining incompleteness in the fixed-scope UK politics and policy KG and defines a practical completion strategy.

Project scope:

`A knowledge graph for current UK politics and policy news, using articles published between March 6, 2026 and April 6, 2026 from GuardianAPI and NewsAPI, with OpenAI used for extraction, classification, and completion.`

Current state:

- the base pipeline already populates articles, authors, publishers, topics, people, organisations, locations, sections, publication dates, update timestamps, URLs, and word counts
- the current completion script adds heuristic sentiment, article subtype, and follow-up links
- the remaining gaps are mainly political-actor typing, event modelling, journalist affiliation, and confidence-grounded completion

## Remaining Incomplete Ontology Elements

`O1.` `news:worksFor` is modelled but not populated.

`O2.` `news:NewsEvent`, `news:PoliticalEvent`, and `news:EconomicEvent` are modelled but not instantiated.

`O3.` `news:coversEvent`, `news:eventDate`, and `news:eventLocation` are modelled but not populated.

`O4.` `news:Politician`, `news:PoliticalParty`, and `news:GovernmentBody` exist in the ontology but current entity mentions are not typed into those subclasses.

`O5.` The ontology still contains a legacy technology mention path that is not part of the final politics-focused CQ scope, so the implemented ontology is broader than the final scored domain.

## Remaining Incomplete Instance Elements

`I1.` The fixed-window dataset is currently Guardian-heavy because NewsAPI can reject historical fixed-window access on the present plan, which weakens cross-source coverage.

`I2.` Person mentions are stored generically and are not yet disambiguated into politicians versus non-political people.

`I3.` Organisation mentions are not yet resolved into political parties, government bodies, and other organisation types.

`I4.` No event instances, event dates, or event locations are currently generated from article text.

`I5.` Completion outputs such as sentiment, subtype, and follow-up are heuristic and are not yet stored with confidence scores or evidence spans.

## Why These Gaps Matter

These gaps block or weaken the hardest CQs:

- `CQ04` and `CQ20` depend on party and politician typing.
- `CQ05` depends on government-body typing.
- `CQ11` depends on `news:worksFor`.
- `CQ18` and `CQ19` depend on event extraction.
- `CQ06`, `CQ09`, `CQ10`, and `CQ12` are currently only partially supported because completion is heuristic.

## Practical RAG-Style Completion Strategy

The completion workflow does not need a heavy framework. A constrained retrieve-generate-validate loop is enough.

### 1. Retrieve

For each target article or entity, retrieve:

- article headline, summary, and content
- section, tags, publisher, author, and publication metadata
- nearby KG context such as existing people, organisations, locations, and topics
- optionally, official external context for political actors or institutions if time allows

### 2. Generate

Use OpenAI to propose only ontology-allowed outputs in strict JSON.

Priority generation tasks:

- classify mentioned people as `news:Politician` or generic `schema:Person`
- classify organisations as `news:PoliticalParty`, `news:GovernmentBody`, or generic `news:Organisation`
- extract `news:PoliticalEvent` and `news:EconomicEvent` candidates
- propose `news:eventDate`, `news:eventLocation`, and `news:coversEvent`
- propose `news:worksFor` only when evidence is explicit
- replace heuristic sentiment and subtype outputs with evidence-backed outputs

### 3. Validate

Before converting to RDF:

- reject any class or property outside the ontology
- validate domain and range compatibility
- canonicalise names and dates
- reject low-confidence completions
- keep evidence text and confidence score alongside accepted outputs

### 4. Store

Store accepted completions in a separate completion graph or as a clearly marked enrichment layer, then merge only validated triples into the final KG.

## Recommended Completion Backlog

1. Add political-actor classification for people and organisations.
2. Add event extraction with date and location.
3. Materialise `news:worksFor` where author-publisher evidence is strong.
4. Replace heuristic sentiment and subtype labelling with constrained LLM outputs.
5. Add confidence and provenance tracking for all completion-generated triples.
