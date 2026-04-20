from src.wikidata_collection import has_minimum_wikidata_coverage, merge_with_cached_entities


def test_merge_with_cached_entities_prefers_live_records():
    live_records = [{"name": "Keir Starmer"}]
    cached_payload = {"politicians": [{"name": "Rishi Sunak"}]}

    result = merge_with_cached_entities(live_records, cached_payload, "politicians")

    assert result == live_records


def test_merge_with_cached_entities_falls_back_to_cached_records():
    live_records = []
    cached_payload = {"politicians": [{"name": "Keir Starmer"}]}

    result = merge_with_cached_entities(live_records, cached_payload, "politicians")

    assert result == cached_payload["politicians"]


def test_has_minimum_wikidata_coverage_requires_all_three_entity_sets():
    assert has_minimum_wikidata_coverage(
        {
            "politicians": [{"name": "Keir Starmer"}],
            "political_parties": [{"name": "Labour Party"}],
            "government_bodies": [{"name": "HM Treasury"}],
        }
    )
    assert not has_minimum_wikidata_coverage(
        {
            "politicians": [],
            "political_parties": [{"name": "Labour Party"}],
            "government_bodies": [{"name": "HM Treasury"}],
        }
    )
