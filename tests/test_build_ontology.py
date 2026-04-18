from rdflib import RDF, RDFS
from rdflib.namespace import OWL, XSD

from src import build_ontology


class TestBuildOntology:
    def test_returns_non_empty_graph(self):
        graph = build_ontology.build_ontology()
        assert len(graph) > 0

    def test_declares_ontology(self):
        graph = build_ontology.build_ontology()
        assert (build_ontology.NEWS[""], RDF.type, OWL.Ontology) in graph

    def test_ontology_has_expected_label(self):
        graph = build_ontology.build_ontology()
        assert (
            build_ontology.NEWS[""],
            RDFS.label,
            build_ontology.Literal("UK Parliamentary and Policy Event Ontology"),
        ) in graph

    def test_defines_core_event_hierarchy(self):
        graph = build_ontology.build_ontology()
        assert (
            build_ontology.NEWS.PolicyEvent,
            RDFS.subClassOf,
            build_ontology.CORE.Event,
        ) in graph
        assert (
            build_ontology.NEWS.ParliamentaryEvent,
            RDFS.subClassOf,
            build_ontology.NEWS.PolicyEvent,
        ) in graph
        assert (
            build_ontology.NEWS.GovernmentPolicyEvent,
            RDFS.subClassOf,
            build_ontology.NEWS.PolicyEvent,
        ) in graph
        assert (
            build_ontology.NEWS.ParliamentaryDebate,
            RDFS.subClassOf,
            build_ontology.NEWS.ParliamentaryEvent,
        ) in graph
        assert (
            build_ontology.NEWS.MinisterialStatement,
            RDFS.subClassOf,
            build_ontology.NEWS.GovernmentPolicyEvent,
        ) in graph

    def test_extends_schema_org_with_subclasses(self):
        graph = build_ontology.build_ontology()
        assert (
            build_ontology.NEWS.PoliticalActor,
            RDFS.subClassOf,
            build_ontology.SCHEMA.Person,
        ) in graph
        assert (
            build_ontology.NEWS.PoliticalParty,
            RDFS.subClassOf,
            build_ontology.SCHEMA.Organization,
        ) in graph
        assert (
            build_ontology.NEWS.NewsArticle,
            RDFS.subClassOf,
            build_ontology.SCHEMA.NewsArticle,
        ) in graph
        assert (
            build_ontology.NEWS.SourceRecord,
            RDFS.subClassOf,
            build_ontology.SCHEMA.CreativeWork,
        ) in graph

    def test_extends_bbc_core_with_subclasses(self):
        graph = build_ontology.build_ontology()
        assert (
            build_ontology.NEWS.Location,
            RDFS.subClassOf,
            build_ontology.CORE.Place,
        ) in graph

    def test_extends_existing_ontologies_with_subproperties(self):
        graph = build_ontology.build_ontology()
        assert (
            build_ontology.NEWS.concernsPolicyTopic,
            RDFS.subPropertyOf,
            build_ontology.SCHEMA.about,
        ) in graph
        assert (
            build_ontology.NEWS.hasAuthor,
            RDFS.subPropertyOf,
            build_ontology.SCHEMA.author,
        ) in graph
        assert (
            build_ontology.NEWS.publishedBy,
            RDFS.subPropertyOf,
            build_ontology.SCHEMA.publisher,
        ) in graph
        assert (
            build_ontology.NEWS.memberOfParty,
            RDFS.subPropertyOf,
            build_ontology.SCHEMA.memberOf,
        ) in graph
        assert (
            build_ontology.NEWS.occursInLocation,
            RDFS.subPropertyOf,
            build_ontology.CORE.eventPlace,
        ) in graph
        assert (
            build_ontology.NEWS.occursOnDate,
            RDFS.subPropertyOf,
            build_ontology.CORE.startDate,
        ) in graph

    def test_defines_core_object_properties(self):
        graph = build_ontology.build_ontology()
        for property_uri in (
            build_ontology.NEWS.involvesActor,
            build_ontology.NEWS.involvesGovernmentBody,
            build_ontology.NEWS.issuedByDepartment,
            build_ontology.NEWS.occursInParliamentaryBody,
            build_ontology.NEWS.reportedByArticle,
            build_ontology.NEWS.representedInOfficialSource,
            build_ontology.NEWS.matchedToSourceRecord,
        ):
            assert (property_uri, RDF.type, OWL.ObjectProperty) in graph

    def test_defines_core_datatype_properties(self):
        graph = build_ontology.build_ontology()
        assert (
            build_ontology.NEWS.occursOnDate,
            RDFS.range,
            XSD.date,
        ) in graph
        assert (
            build_ontology.NEWS.publishedDate,
            RDFS.range,
            XSD.dateTime,
        ) in graph
        assert (
            build_ontology.NEWS.articleURL,
            RDFS.range,
            XSD.anyURI,
        ) in graph

    def test_no_rdf_property_declarations(self):
        graph = build_ontology.build_ontology()
        assert len(list(graph.subjects(RDF.type, RDF.Property))) == 0

    def test_no_rdfs_class_declarations(self):
        graph = build_ontology.build_ontology()
        assert len(list(graph.subjects(RDF.type, RDFS.Class))) == 0

    def test_reports_on_inverse_if_present(self):
        graph = build_ontology.build_ontology()
        assert (build_ontology.NEWS.reportsOn, RDF.type, OWL.ObjectProperty) in graph
        assert (
            build_ontology.NEWS.reportsOn,
            OWL.inverseOf,
            build_ontology.NEWS.reportedByArticle,
        ) in graph


class TestOntologyMain:
    def test_main_serializes_turtle_to_output_path(self, monkeypatch, tmp_path):
        output_path = tmp_path / "news_ontology.ttl"
        monkeypatch.setattr(build_ontology, "OUTPUT_PATH", output_path)

        build_ontology.main()

        assert output_path.exists()
        content = output_path.read_text(encoding="utf-8")
        assert "@prefix" in content
        assert "UK Parliamentary and Policy Event Ontology" in content
