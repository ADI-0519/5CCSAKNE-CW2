# Extraction Evaluation

- Gold standard: `data\evaluation\gold_standard_extraction.json`
- Prediction input: `data\processed\20260422T195330Z_kg_records.json`
- Evaluated samples: `15`
- Missing predictions: `0`

## Overall Metrics

- Metadata accuracy: `1.0`
- event_name: precision `0.375`, recall `0.2727`, f1 `0.3158`
- event_type: precision `0.375`, recall `0.2727`, f1 `0.3158`
- record_topics: precision `0.7188`, recall `0.7419`, f1 `0.7302`
- event_topics: precision `0.1667`, recall `0.0769`, f1 `0.1053`
- institution_links: precision `0.2857`, recall `0.125`, f1 `0.1739`
- political_actors: precision `0.0`, recall `0.0`, f1 `0.0`
- political_parties: precision `0.0`, recall `0.0`, f1 `0.0`
- record_government_bodies: precision `0.4074`, recall `0.7857`, f1 `0.5366`
- record_locations: precision `0.0645`, recall `0.2857`, f1 `0.1053`

## By Source System

### govuk

- Samples: `5`
- Metadata accuracy: `1.0`
- event_name: precision `1.0`, recall `0.6`, f1 `0.75`
- event_type: precision `1.0`, recall `0.6`, f1 `0.75`
- record_topics: precision `0.6`, recall `0.75`, f1 `0.6667`
- event_topics: precision `0.5`, recall `0.2`, f1 `0.2857`
- institution_links: precision `1.0`, recall `0.4`, f1 `0.5714`
- political_actors: precision `0.0`, recall `0.0`, f1 `0.0`
- political_parties: precision `0.0`, recall `0.0`, f1 `0.0`
- record_government_bodies: precision `0.4615`, recall `1.0`, f1 `0.6316`
- record_locations: precision `0.0`, recall `0.0`, f1 `0.0`

### guardian

- Samples: `5`
- Metadata accuracy: `1.0`
- event_name: precision `0.0`, recall `0.0`, f1 `0.0`
- event_type: precision `0.0`, recall `0.0`, f1 `0.0`
- record_topics: precision `0.6667`, recall `1.0`, f1 `0.8`
- event_topics: precision `0.0`, recall `0.0`, f1 `0.0`
- institution_links: precision `0.0`, recall `0.0`, f1 `0.0`
- political_actors: precision `0.0`, recall `0.0`, f1 `0.0`
- political_parties: precision `0.0`, recall `0.0`, f1 `0.0`
- record_government_bodies: precision `0.375`, recall `1.0`, f1 `0.5455`
- record_locations: precision `0.0769`, recall `0.2857`, f1 `0.1212`

### parliament

- Samples: `5`
- Metadata accuracy: `1.0`
- event_name: precision `0.0`, recall `0.0`, f1 `0.0`
- event_type: precision `0.0`, recall `0.0`, f1 `0.0`
- record_topics: precision `1.0`, recall `0.5385`, f1 `0.7`
- event_topics: precision `0.0`, recall `0.0`, f1 `0.0`
- institution_links: precision `0.0`, recall `0.0`, f1 `0.0`
- political_actors: precision `0.0`, recall `0.0`, f1 `0.0`
- political_parties: precision `0.0`, recall `0.0`, f1 `0.0`
- record_government_bodies: precision `0.3333`, recall `0.4`, f1 `0.3636`
- record_locations: precision `0.0`, recall `0.0`, f1 `0.0`
