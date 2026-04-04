"""Contract and smoke tests for the full pipeline."""

import json
import os

import pytest

from src.data_extraction import extract_relevant_information
from src.data_normalisation import normalise_data
from src.json_to_rdf import convert_json_to_rdf

FIXTURE_PATH = os.path.join(os.path.dirname(__file__), "fixtures", "sample_response.json")


@pytest.fixture
def sample_raw_data():
    with open(FIXTURE_PATH) as f:
        return json.load(f)


@pytest.fixture
def extracted(sample_raw_data):
    return extract_relevant_information(sample_raw_data)


@pytest.fixture
def normalised(extracted):
    return normalise_data(extracted)


@pytest.fixture
def rdf_graph(normalised):
    return convert_json_to_rdf(normalised)


# ---------------------------------------------------------------------------
# Contract: extract -> normalise
# ---------------------------------------------------------------------------


class TestExtractToNormaliseContract:
    def test_extracted_records_pass_normalisation(self, extracted):
        """Every record output by extraction must be accepted by normalisation."""
        result = normalise_data(extracted)
        assert len(result) == len(extracted)

    def test_normalised_ids_are_stable(self, extracted):
        """Running normalisation twice on the same extracted data yields identical IDs."""
        r1 = normalise_data(extracted)
        r2 = normalise_data(extracted)
        assert [r["id"] for r in r1] == [r["id"] for r in r2]

    def test_normalised_dates_are_utc_iso(self, normalised):
        for record in normalised:
            dt = record["published_at"]
            assert dt.endswith("Z"), f"Date not UTC: {dt}"
            assert "T" in dt

    def test_all_normalised_entities_have_required_keys(self, normalised):
        for record in normalised:
            entities = record["entities"]
            for key in ("organizations", "people", "locations", "technologies", "topics"):
                assert key in entities

    def test_all_normalised_relations_use_controlled_predicates(self, normalised):
        from src.config import CONFIG

        allowed = CONFIG["CONTROLLED_PREDICATES"]
        for record in normalised:
            for rel in record["relations"]:
                assert rel["predicate"] in allowed, f"Unexpected predicate: {rel['predicate']!r}"


# ---------------------------------------------------------------------------
# Contract: normalise -> rdf
# ---------------------------------------------------------------------------


class TestNormaliseToRdfContract:
    def test_every_normalised_record_produces_triples(self, normalised):
        for record in normalised:
            g = convert_json_to_rdf([record])
            assert len(g) > 0, f"No triples produced for record {record['id']}"

    def test_rdf_graph_has_article_nodes(self, normalised, rdf_graph):
        from rdflib import RDF
        from rdflib.namespace import Namespace

        SCHEMA_NS = Namespace("http://schema.org/")
        article_types = list(rdf_graph.subjects(RDF.type, SCHEMA_NS.NewsArticle))
        assert len(article_types) == len(normalised)


# ---------------------------------------------------------------------------
# Smoke test: offline end-to-end with fixture
# ---------------------------------------------------------------------------


class TestEndToEndSmoke:
    def test_pipeline_produces_valid_nonempty_turtle(self, rdf_graph, tmp_path):
        out_file = tmp_path / "output.ttl"
        rdf_graph.serialize(destination=str(out_file), format="turtle")

        assert out_file.exists()
        content = out_file.read_text()
        assert len(content) > 0
        assert "@prefix" in content

    def test_fixture_produces_expected_article_count(self, normalised):
        assert len(normalised) == 2

    def test_fixture_detects_ai_technology(self, normalised):
        all_techs = [t for r in normalised for t in r["entities"]["technologies"]]
        assert "AI" in all_techs or "Artificial Intelligence" in all_techs

    def test_fixture_detects_robotics(self, normalised):
        all_techs = [t for r in normalised for t in r["entities"]["technologies"]]
        assert "Robotics" in all_techs
