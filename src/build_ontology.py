from pathlib import Path

from rdflib import Graph, Literal, Namespace
from rdflib.namespace import OWL, RDF, RDFS, XSD

NEWS = Namespace("http://example.org/news#")
SCHEMA = Namespace("https://schema.org/")
CORE = Namespace("http://www.bbc.co.uk/ontologies/coreconcepts/")

OUTPUT_PATH = Path(__file__).parent.parent / "ontology" / "news_ontology.ttl"

SCHEMA_EXTENSION_TERMS = {
    "PoliticalActor",
    "PoliticalParty",
    "OfficialBody",
    "GovernmentBody",
    "ParliamentaryBody",
    "PolicyTopic",
    "NewsArticle",
    "NewsOrganisation",
    "Journalist",
    "SourceRecord",
    "OfficialSourceRecord",
    "ParliamentSourceRecord",
    "GovernmentSourceRecord",
    "concernsPolicyTopic",
    "memberOfParty",
    "publishedBy",
    "hasAuthor",
    "publishedDate",
    "articleURL",
    "sourceIdentifier",
    "sourceTitle",
    "sourceSystem",
}

CORE_EXTENSION_TERMS = {
    "PolicyEvent",
    "ParliamentaryEvent",
    "GovernmentPolicyEvent",
    "ParliamentaryDebate",
    "MinisterialStatement",
    "Location",
    "occursOnDate",
    "occursInLocation",
}


def add_extension_comments(path: Path):
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    output_lines = []
    for line in lines:
        if line.startswith("news:"):
            term = line.split()[0].removeprefix("news:")
            if term in SCHEMA_EXTENSION_TERMS:
                output_lines.append("# Schema.org extension\n")
            elif term in CORE_EXTENSION_TERMS:
                output_lines.append("# BBC Core Concepts extension\n")
        output_lines.append(line)
    path.write_text("".join(output_lines), encoding="utf-8")


def normalise_parents(parents):
    if parents is None:
        return []
    if isinstance(parents, (list, tuple, set)):
        return list(parents)
    return [parents]


def add_class(graph: Graph, class_uri, label: str, comment: str, parents=None):
    graph.add((class_uri, RDF.type, OWL.Class))
    for parent in normalise_parents(parents):
        graph.add((class_uri, RDFS.subClassOf, parent))
    graph.add((class_uri, RDFS.label, Literal(label)))
    graph.add((class_uri, RDFS.comment, Literal(comment)))


def add_object_property(
    graph: Graph, property_uri, label: str, comment: str, domain=None, range_=None, parent=None
):
    graph.add((property_uri, RDF.type, OWL.ObjectProperty))
    if parent is not None:
        graph.add((property_uri, RDFS.subPropertyOf, parent))
    if domain is not None:
        graph.add((property_uri, RDFS.domain, domain))
    if range_ is not None:
        graph.add((property_uri, RDFS.range, range_))
    graph.add((property_uri, RDFS.label, Literal(label)))
    graph.add((property_uri, RDFS.comment, Literal(comment)))


def add_datatype_property(
    graph: Graph, property_uri, label: str, comment: str, domain=None, range_=None, parent=None
):
    graph.add((property_uri, RDF.type, OWL.DatatypeProperty))
    if parent is not None:
        graph.add((property_uri, RDFS.subPropertyOf, parent))
    if domain is not None:
        graph.add((property_uri, RDFS.domain, domain))
    if range_ is not None:
        graph.add((property_uri, RDFS.range, range_))
    graph.add((property_uri, RDFS.label, Literal(label)))
    graph.add((property_uri, RDFS.comment, Literal(comment)))


def build_ontology() -> Graph:
    graph = Graph()
    graph.bind("news", NEWS)
    graph.bind("schema", SCHEMA)
    graph.bind("core", CORE)
    graph.bind("owl", OWL)
    graph.bind("xsd", XSD)

    graph.add((NEWS[""], RDF.type, OWL.Ontology))
    graph.add((NEWS[""], RDFS.label, Literal("UK Parliamentary and Policy Event Ontology")))
    graph.add(
        (
            NEWS[""],
            RDFS.comment,
            Literal(
                "A CQ-driven ontology for UK parliamentary and government policy events "
                "reported in UK news. The ontology models events, actors, institutions, "
                "policy topics, reporting artefacts, and lightweight provenance through "
                "source records."
            ),
        )
    )

    # event layer
    add_class(
        graph,
        NEWS.PolicyEvent,
        "Policy Event",
        "A real-world event concerning UK government policy or parliamentary policy activity.",
        CORE.Event,
    )
    add_class(
        graph,
        NEWS.ParliamentaryEvent,
        "Parliamentary Event",
        "A policy event taking place within a parliamentary setting or linked to a parliamentary body.",
        NEWS.PolicyEvent,
    )
    add_class(
        graph,
        NEWS.GovernmentPolicyEvent,
        "Government Policy Event",
        "A policy event issued by or involving a government body or department.",
        NEWS.PolicyEvent,
    )
    add_class(
        graph,
        NEWS.ParliamentaryDebate,
        "Parliamentary Debate",
        "A parliamentary event in which one or more policy topics are debated.",
        NEWS.ParliamentaryEvent,
    )
    add_class(
        graph,
        NEWS.MinisterialStatement,
        "Ministerial Statement",
        "A government policy event in which a department issues an official ministerial statement.",
        NEWS.GovernmentPolicyEvent,
    )

    # actor and institution layer
    add_class(
        graph,
        NEWS.PoliticalActor,
        "Political Actor",
        "A person participating in a policy event in a political capacity.",
        SCHEMA.Person,
    )
    add_class(
        graph,
        NEWS.PoliticalParty,
        "Political Party",
        "A political party linked to political actors participating in policy events.",
        SCHEMA.Organization,
    )
    add_class(
        graph,
        NEWS.OfficialBody,
        "Official Body",
        "An official public institution relevant to the domain, including executive government bodies and parliamentary institutions.",
        SCHEMA.Organization,
    )
    add_class(
        graph,
        NEWS.GovernmentBody,
        "Government Body",
        "An executive government body involved in a policy event.",
        NEWS.OfficialBody,
    )
    add_class(
        graph,
        NEWS.GovernmentDepartment,
        "Government Department",
        "A government department involved in a government policy event or issuing a ministerial statement.",
        NEWS.GovernmentBody,
    )
    add_class(
        graph,
        NEWS.ParliamentaryBody,
        "Parliamentary Body",
        "A parliamentary chamber, committee, or institution in which a parliamentary event occurs.",
        NEWS.OfficialBody,
    )

    # topic and place layer
    add_class(
        graph,
        NEWS.PolicyTopic,
        "Policy Topic",
        "A policy topic such as immigration, healthcare, taxation, or public spending.",
        SCHEMA.Thing,
    )
    add_class(
        graph,
        NEWS.Location,
        "Location",
        "A location in which a policy event occurs.",
        CORE.Place,
    )

    # reporting and provenance layer
    add_class(
        graph,
        NEWS.NewsArticle,
        "News Article",
        "A news article that reports on a policy event.",
        SCHEMA.NewsArticle,
    )
    add_class(
        graph,
        NEWS.NewsOrganisation,
        "News Organisation",
        "A news publisher reporting on policy events.",
        SCHEMA.Organization,
    )
    add_class(
        graph,
        NEWS.Journalist,
        "Journalist",
        "A journalist who authors a news article reporting on a policy event.",
        SCHEMA.Person,
    )
    add_class(
        graph,
        NEWS.SourceRecord,
        "Source Record",
        "A source-side record used to construct or align the knowledge graph.",
        SCHEMA.CreativeWork,
    )
    add_class(
        graph,
        NEWS.OfficialSourceRecord,
        "Official Source Record",
        "A source record from an official parliamentary or government source.",
        NEWS.SourceRecord,
    )
    add_class(
        graph,
        NEWS.ParliamentSourceRecord,
        "Parliament Source Record",
        "A source record derived from a parliamentary source.",
        NEWS.OfficialSourceRecord,
    )
    add_class(
        graph,
        NEWS.GovernmentSourceRecord,
        "Government Source Record",
        "A source record derived from a government source.",
        NEWS.OfficialSourceRecord,
    )

    # core object properties
    add_object_property(
        graph,
        NEWS.concernsPolicyTopic,
        "concerns policy topic",
        "Links a policy event to the policy topic it concerns.",
        NEWS.PolicyEvent,
        NEWS.PolicyTopic,
        SCHEMA.about,
    )
    add_object_property(
        graph,
        NEWS.involvesActor,
        "involves actor",
        "Links a policy event to a political actor involved in it.",
        NEWS.PolicyEvent,
        NEWS.PoliticalActor,
    )
    add_object_property(
        graph,
        NEWS.involvesGovernmentBody,
        "involves government body",
        "Links a policy event to a government body involved in it.",
        NEWS.PolicyEvent,
        NEWS.GovernmentBody,
    )
    add_object_property(
        graph,
        NEWS.issuedByDepartment,
        "issued by department",
        "Links a ministerial statement to the government department that issued it.",
        NEWS.MinisterialStatement,
        NEWS.GovernmentDepartment,
        NEWS.involvesGovernmentBody,
    )
    add_object_property(
        graph,
        NEWS.occursInParliamentaryBody,
        "occurs in parliamentary body",
        "Links a parliamentary event to the parliamentary body in which it occurs.",
        NEWS.ParliamentaryEvent,
        NEWS.ParliamentaryBody,
    )
    add_object_property(
        graph,
        NEWS.occursInLocation,
        "occurs in location",
        "Links a policy event to the location in which it occurs.",
        NEWS.PolicyEvent,
        NEWS.Location,
        CORE.eventPlace,
    )
    add_object_property(
        graph,
        NEWS.memberOfParty,
        "member of party",
        "Links a political actor to the political party they belong to.",
        NEWS.PoliticalActor,
        NEWS.PoliticalParty,
        SCHEMA.memberOf,
    )
    add_object_property(
        graph,
        NEWS.reportedByArticle,
        "reported by article",
        "Links a policy event to a news article that reports on it.",
        NEWS.PolicyEvent,
        NEWS.NewsArticle,
    )
    add_object_property(
        graph,
        NEWS.publishedBy,
        "published by",
        "Links a news article to the news organisation that published it.",
        NEWS.NewsArticle,
        NEWS.NewsOrganisation,
        SCHEMA.publisher,
    )
    add_object_property(
        graph,
        NEWS.hasAuthor,
        "has author",
        "Links a news article to the journalist who authored it.",
        NEWS.NewsArticle,
        NEWS.Journalist,
        SCHEMA.author,
    )
    add_object_property(
        graph,
        NEWS.representedInOfficialSource,
        "represented in official source",
        "Links a policy event to an official source record that directly describes or evidences that event.",
        NEWS.PolicyEvent,
        NEWS.OfficialSourceRecord,
    )
    add_object_property(
        graph,
        NEWS.matchedToSourceRecord,
        "matched to source record",
        "Links a policy event to a source record aligned to it across datasets for integration purposes, without asserting strict identity between records.",
        NEWS.PolicyEvent,
        NEWS.SourceRecord,
    )

    # datatype properties
    add_datatype_property(
        graph,
        NEWS.occursOnDate,
        "occurs on date",
        "The calendar date on which a policy event occurs.",
        NEWS.PolicyEvent,
        XSD.date,
        CORE.startDate,
    )
    add_datatype_property(
        graph,
        NEWS.publishedDate,
        "published date",
        "The publication timestamp of a news article.",
        NEWS.NewsArticle,
        XSD.dateTime,
        SCHEMA.datePublished,
    )
    add_datatype_property(
        graph,
        NEWS.articleURL,
        "article URL",
        "The canonical URL of a news article.",
        NEWS.NewsArticle,
        XSD.anyURI,
        SCHEMA.url,
    )
    add_datatype_property(
        graph,
        NEWS.sourceIdentifier,
        "source identifier",
        "An identifier assigned to a source record by its source system.",
        NEWS.SourceRecord,
        XSD.string,
    )
    add_datatype_property(
        graph,
        NEWS.sourceTitle,
        "source title",
        "The title or headline held by a source record.",
        NEWS.SourceRecord,
        XSD.string,
    )
    add_datatype_property(
        graph,
        NEWS.sourceSystem,
        "source system",
        "The name of the source system from which a source record was collected.",
        NEWS.SourceRecord,
        XSD.string,
    )

    # property characteristics
    graph.add((NEWS.involvesActor, RDF.type, OWL.IrreflexiveProperty))
    graph.add((NEWS.memberOfParty, RDF.type, OWL.IrreflexiveProperty))
    graph.add((NEWS.publishedBy, RDF.type, OWL.FunctionalProperty))
    graph.add((NEWS.occursOnDate, RDF.type, OWL.FunctionalProperty))
    graph.add((NEWS.reportsOn, RDF.type, OWL.ObjectProperty))
    graph.add((NEWS.reportsOn, OWL.inverseOf, NEWS.reportedByArticle))
    graph.add((NEWS.reportsOn, RDFS.domain, NEWS.NewsArticle))
    graph.add((NEWS.reportsOn, RDFS.range, NEWS.PolicyEvent))
    graph.add((NEWS.reportsOn, RDFS.label, Literal("reports on")))
    graph.add(
        (
            NEWS.reportsOn,
            RDFS.comment,
            Literal("Links a news article to the policy event it reports on."),
        )
    )
    return graph


def main():
    print("Building UK Parliamentary and Policy Event Ontology (TBox)...\n")
    graph = build_ontology()

    classes = set(graph.subjects(RDF.type, OWL.Class))
    object_properties = set(graph.subjects(RDF.type, OWL.ObjectProperty))
    datatype_properties = set(graph.subjects(RDF.type, OWL.DatatypeProperty))
    subclass_triples = list(graph.triples((None, RDFS.subClassOf, None)))
    subproperty_triples = list(graph.triples((None, RDFS.subPropertyOf, None)))

    schema_subclasses = [s for s, _, o in subclass_triples if "schema.org" in str(o)]
    schema_subproperties = [s for s, _, o in subproperty_triples if "schema.org" in str(o)]
    core_subclasses = [s for s, _, o in subclass_triples if "bbc.co.uk" in str(o)]
    core_subproperties = [s for s, _, o in subproperty_triples if "bbc.co.uk" in str(o)]

    print(f"Classes: {len(classes)}")
    print(f"Object properties: {len(object_properties)}")
    print(f"Datatype properties: {len(datatype_properties)}")
    print(f"Total triples: {len(graph)}")
    print(
        f"\nSchema.org: {len(schema_subclasses)} subclasses, {len(schema_subproperties)} subproperties"
    )
    print(
        f"BBC Core Concepts: {len(core_subclasses)} subclasses, {len(core_subproperties)} subproperties"
    )

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    graph.serialize(str(OUTPUT_PATH), format="turtle")
    add_extension_comments(OUTPUT_PATH)
    print(f"\nSaved to: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
