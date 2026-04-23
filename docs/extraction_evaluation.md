# Extraction Evaluation

- Gold standard: `data/evaluation/gold_standard_extraction.json`
- Prediction input: `data/processed/20260423T110354Z_kg_records.json`
- Evaluated samples: `51`
- Missing predictions: `0`

## Overall Metrics

- Metadata accuracy: `1.0`
- event_name: precision `0.8571`, recall `1.0`, f1 `0.9231`
- event_type: precision `0.8571`, recall `1.0`, f1 `0.9231`
- record_topics: precision `0.5841`, recall `0.6346`, f1 `0.6083`
- event_topics: precision `0.84`, recall `0.84`, f1 `0.84`
- institution_links: precision `0.75`, recall `1.0`, f1 `0.8571`
- political_actors: precision `0.8571`, recall `1.0`, f1 `0.9231`
- political_parties: precision `1.0`, recall `1.0`, f1 `1.0`
- record_government_bodies: precision `0.5306`, recall `0.8966`, f1 `0.6667`
- record_locations: precision `0.3273`, recall `1.0`, f1 `0.4932`

## By Source System

### govuk

- Samples: `17`
- Metadata accuracy: `1.0`
- event_name: precision `1.0`, recall `1.0`, f1 `1.0`
- event_type: precision `1.0`, recall `1.0`, f1 `1.0`
- record_topics: precision `0.4737`, recall `0.5806`, f1 `0.5217`
- event_topics: precision `1.0`, recall `0.9167`, f1 `0.9565`
- institution_links: precision `1.0`, recall `1.0`, f1 `1.0`
- political_actors: precision `0.0`, recall `0.0`, f1 `0.0`
- political_parties: precision `1.0`, recall `1.0`, f1 `1.0`
- record_government_bodies: precision `0.6087`, recall `1.0`, f1 `0.7568`
- record_locations: precision `0.5455`, recall `1.0`, f1 `0.7059`

### guardian

- Samples: `17`
- Metadata accuracy: `1.0`
- event_name: precision `0.6667`, recall `1.0`, f1 `0.8`
- event_type: precision `0.6667`, recall `1.0`, f1 `0.8`
- record_topics: precision `0.617`, recall `0.7838`, f1 `0.6905`
- event_topics: precision `0.6364`, recall `0.7778`, f1 `0.7`
- institution_links: precision `0.0`, recall `0.0`, f1 `0.0`
- political_actors: precision `0.8571`, recall `1.0`, f1 `0.9231`
- political_parties: precision `1.0`, recall `1.0`, f1 `1.0`
- record_government_bodies: precision `0.3636`, recall `0.8`, f1 `0.5`
- record_locations: precision `0.2381`, recall `1.0`, f1 `0.3846`

### parliament

- Samples: `17`
- Metadata accuracy: `1.0`
- event_name: precision `1.0`, recall `1.0`, f1 `1.0`
- event_type: precision `1.0`, recall `1.0`, f1 `1.0`
- record_topics: precision `0.6786`, recall `0.5278`, f1 `0.5937`
- event_topics: precision `1.0`, recall `0.75`, f1 `0.8571`
- institution_links: precision `1.0`, recall `1.0`, f1 `1.0`
- political_actors: precision `0.0`, recall `0.0`, f1 `0.0`
- political_parties: precision `0.0`, recall `0.0`, f1 `0.0`
- record_government_bodies: precision `1.0`, recall `0.8`, f1 `0.8889`
- record_locations: precision `1.0`, recall `1.0`, f1 `1.0`
