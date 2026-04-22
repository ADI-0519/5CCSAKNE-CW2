# Extraction Evaluation

- Gold standard: `data/evaluation/gold_standard_extraction.json`
- Prediction input: `data/processed/20260422T205841Z_kg_records.json`
- Evaluated samples: `9`
- Missing predictions: `0`

## Overall Metrics

- Metadata accuracy: `0.9298`
- event_name: precision `1.0`, recall `1.0`, f1 `1.0`
- event_type: precision `1.0`, recall `1.0`, f1 `1.0`
- record_topics: precision `0.7895`, recall `0.9375`, f1 `0.8571`
- event_topics: precision `1.0`, recall `1.0`, f1 `1.0`
- institution_links: precision `1.0`, recall `1.0`, f1 `1.0`
- political_actors: precision `0.0`, recall `0.0`, f1 `0.0`
- political_parties: precision `0.0`, recall `0.0`, f1 `0.0`
- record_government_bodies: precision `0.5385`, recall `0.875`, f1 `0.6667`
- record_locations: precision `0.95`, recall `1.0`, f1 `0.9744`

## By Source System

### govuk

- Samples: `3`
- Metadata accuracy: `0.9444`
- event_name: precision `1.0`, recall `1.0`, f1 `1.0`
- event_type: precision `1.0`, recall `1.0`, f1 `1.0`
- record_topics: precision `0.8`, recall `0.8`, f1 `0.8`
- event_topics: precision `1.0`, recall `1.0`, f1 `1.0`
- institution_links: precision `1.0`, recall `1.0`, f1 `1.0`
- political_actors: precision `0.0`, recall `0.0`, f1 `0.0`
- political_parties: precision `0.0`, recall `0.0`, f1 `0.0`
- record_government_bodies: precision `0.5`, recall `1.0`, f1 `0.6667`
- record_locations: precision `1.0`, recall `1.0`, f1 `1.0`

### guardian

- Samples: `3`
- Metadata accuracy: `0.8571`
- event_name: precision `0.0`, recall `0.0`, f1 `0.0`
- event_type: precision `0.0`, recall `0.0`, f1 `0.0`
- record_topics: precision `0.625`, recall `1.0`, f1 `0.7692`
- event_topics: precision `0.0`, recall `0.0`, f1 `0.0`
- institution_links: precision `0.0`, recall `0.0`, f1 `0.0`
- political_actors: precision `0.0`, recall `0.0`, f1 `0.0`
- political_parties: precision `0.0`, recall `0.0`, f1 `0.0`
- record_government_bodies: precision `0.6`, recall `1.0`, f1 `0.75`
- record_locations: precision `0.9412`, recall `1.0`, f1 `0.9697`

### parliament

- Samples: `3`
- Metadata accuracy: `1.0`
- event_name: precision `1.0`, recall `1.0`, f1 `1.0`
- event_type: precision `1.0`, recall `1.0`, f1 `1.0`
- record_topics: precision `1.0`, recall `1.0`, f1 `1.0`
- event_topics: precision `1.0`, recall `1.0`, f1 `1.0`
- institution_links: precision `1.0`, recall `1.0`, f1 `1.0`
- political_actors: precision `0.0`, recall `0.0`, f1 `0.0`
- political_parties: precision `0.0`, recall `0.0`, f1 `0.0`
- record_government_bodies: precision `0.5`, recall `0.5`, f1 `0.5`
- record_locations: precision `0.0`, recall `0.0`, f1 `0.0`
