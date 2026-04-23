# Extraction Evaluation

- Gold standard: `data\evaluation\gold_standard_extraction.json`
- Prediction input: `data\processed\20260422T232808Z_kg_records.json`
- Evaluated samples: `50`
- Missing predictions: `0`

## Overall Metrics

- Metadata accuracy: `0.984`
- event_name: precision `0.1852`, recall `0.1351`, f1 `0.1562`
- event_type: precision `0.1852`, recall `0.1351`, f1 `0.1562`
- record_topics: precision `0.5686`, recall `0.5577`, f1 `0.5631`
- event_topics: precision `0.1154`, recall `0.0476`, f1 `0.0674`
- institution_links: precision `0.25`, recall `0.0833`, f1 `0.125`
- political_actors: precision `0.0`, recall `0.0`, f1 `0.0`
- political_parties: precision `0.0`, recall `0.0`, f1 `0.0`
- record_government_bodies: precision `0.2967`, recall `0.6429`, f1 `0.406`
- record_locations: precision `0.0538`, recall `0.2917`, f1 `0.0909`

## By Source System

### govuk

- Samples: `15`
- Metadata accuracy: `0.9889`
- event_name: precision `1.0`, recall `0.3333`, f1 `0.5`
- event_type: precision `1.0`, recall `0.3333`, f1 `0.5`
- record_topics: precision `0.5385`, recall `0.5185`, f1 `0.5283`
- event_topics: precision `0.5`, recall `0.1111`, f1 `0.1818`
- institution_links: precision `1.0`, recall `0.2778`, f1 `0.4348`
- political_actors: precision `0.0`, recall `0.0`, f1 `0.0`
- political_parties: precision `0.0`, recall `0.0`, f1 `0.0`
- record_government_bodies: precision `0.4848`, recall `0.8889`, f1 `0.6275`
- record_locations: precision `0.0714`, recall `0.25`, f1 `0.1111`

### guardian

- Samples: `15`
- Metadata accuracy: `0.9709`
- event_name: precision `0.0`, recall `0.0`, f1 `0.0`
- event_type: precision `0.0`, recall `0.0`, f1 `0.0`
- record_topics: precision `0.36`, recall `0.75`, f1 `0.4865`
- event_topics: precision `0.0`, recall `0.0`, f1 `0.0`
- institution_links: precision `0.0`, recall `0.0`, f1 `0.0`
- political_actors: precision `0.0`, recall `0.0`, f1 `0.0`
- political_parties: precision `0.0`, recall `0.0`, f1 `0.0`
- record_government_bodies: precision `0.1053`, recall `1.0`, f1 `0.1905`
- record_locations: precision `0.0439`, recall `0.3846`, f1 `0.0787`

### parliament

- Samples: `20`
- Metadata accuracy: `0.9917`
- event_name: precision `0.0`, recall `0.0`, f1 `0.0`
- event_type: precision `0.0`, recall `0.0`, f1 `0.0`
- record_topics: precision `1.0`, recall `0.4906`, f1 `0.6582`
- event_topics: precision `0.0`, recall `0.0`, f1 `0.0`
- institution_links: precision `0.0`, recall `0.0`, f1 `0.0`
- political_actors: precision `0.0`, recall `0.0`, f1 `0.0`
- political_parties: precision `0.0`, recall `0.0`, f1 `0.0`
- record_government_bodies: precision `0.35`, recall `0.35`, f1 `0.35`
- record_locations: precision `0.5`, recall `0.1429`, f1 `0.2222`
