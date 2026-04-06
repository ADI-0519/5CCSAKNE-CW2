from rdflib import RDF, RDFS
from rdflib.namespace import OWL

from src import build_ontology


class TestBuildOntology:
    def test_returns_non_empty_graph(self):
        graph = build_ontology.build_ontology()
        assert len(graph) > 0

    def test_declares_ontology(self):
        graph = build_ontology.build_ontology()
        assert (build_ontology.NEWS[""], RDF.type, OWL.Ontology) in graph

    def test_extends_schema_org_with_subclasses(self):
        graph = build_ontology.build_ontology()
        assert (
            build_ontology.NEWS.NewsArticle,
            RDFS.subClassOf,
            build_ontology.SCHEMA.NewsArticle,
        ) in graph
        assert (
            build_ontology.NEWS.Journalist,
            RDFS.subClassOf,
            build_ontology.SCHEMA.Person,
        ) in graph

    def test_extends_bbc_core_with_subclasses(self):
        graph = build_ontology.build_ontology()
        assert (
            build_ontology.NEWS.NewsEvent,
            RDFS.subClassOf,
            build_ontology.CORE.Event,
        ) in graph
        assert (
            build_ontology.NEWS.Location,
            RDFS.subClassOf,
            build_ontology.CORE.Place,
        ) in graph

    def test_extends_existing_ontologies_with_subproperties(self):
        graph = build_ontology.build_ontology()
        assert (
            build_ontology.NEWS.hasAuthor,
            RDFS.subPropertyOf,
            build_ontology.SCHEMA.author,
        ) in graph
        assert (
            build_ontology.NEWS.eventLocation,
            RDFS.subPropertyOf,
            build_ontology.CORE.eventPlace,
        ) in graph

    def test_creates_sentiment_class_and_instances(self):
        graph = build_ontology.build_ontology()
        assert (build_ontology.NEWS.Sentiment, RDF.type, RDFS.Class) in graph
        for label in ("Positive", "Negative", "Neutral"):
            assert (build_ontology.NEWS[label], RDF.type, build_ontology.NEWS.Sentiment) in graph


class TestOntologyMain:
    def test_main_serializes_turtle_to_output_path(self, monkeypatch, tmp_path):
        output_path = tmp_path / "news_ontology.ttl"
        monkeypatch.setattr(build_ontology, "OUTPUT_PATH", output_path)

        build_ontology.main()

        assert output_path.exists()
        content = output_path.read_text()
        assert "@prefix" in content
        assert "UK Politics and Policy News Ontology" in content
