from pathlib import Path

from rdflib import Graph, Literal, Namespace
from rdflib.namespace import OWL, RDF, RDFS, XSD

NEWS = Namespace("http://example.org/news#")
SCHEMA = Namespace("https://schema.org/")
CORE = Namespace("http://www.bbc.co.uk/ontologies/coreconcepts/")

OUTPUT_PATH = Path(__file__).parent.parent / "ontology" / "news_ontology.ttl"


def add_class(graph, class_uri, label, comment, parent=None):
    graph.add((class_uri, RDF.type, RDFS.Class))
    if parent is not None:
        graph.add((class_uri, RDFS.subClassOf, parent))
    graph.add((class_uri, RDFS.label, Literal(label)))
    graph.add((class_uri, RDFS.comment, Literal(comment)))


def add_property(graph, property_uri, label, comment, domain=None, range_=None, parent=None):
    graph.add((property_uri, RDF.type, RDF.Property))
    if parent is not None:
        graph.add((property_uri, RDFS.subPropertyOf, parent))
    if domain is not None:
        graph.add((property_uri, RDFS.domain, domain))
    if range_ is not None:
        graph.add((property_uri, RDFS.range, range_))
    graph.add((property_uri, RDFS.label, Literal(label)))
    graph.add((property_uri, RDFS.comment, Literal(comment)))


def build_ontology() -> Graph:
    g = Graph()
    g.bind("news", NEWS)
    g.bind("schema", SCHEMA)
    g.bind("core", CORE)
    g.bind("owl", OWL)
    g.bind("xsd", XSD)

    g.add((NEWS[""], RDF.type, OWL.Ontology))
    g.add((NEWS[""], RDFS.label, Literal("UK Politics and Policy News Ontology")))
    g.add(
        (
            NEWS[""],
            RDFS.comment,
            Literal(
                "An ontology for representing current UK politics and policy news, "
                "including articles, journalists, organisations, events, topics, "
                "places, and analytical metadata. Extends Schema.org and the BBC "
                "Core Concepts Ontology."
            ),
        )
    )

    # Classes extending Schema.org

    add_class(
        g,
        NEWS.NewsArticle,
        "News Article",
        "A news article from any source in our knowledge graph.",
        SCHEMA.NewsArticle,
    )
    add_class(
        g,
        NEWS.BreakingNewsArticle,
        "Breaking News Article",
        "An article published as breaking news.",
        NEWS.NewsArticle,
    )
    add_class(
        g,
        NEWS.OpinionArticle,
        "Opinion Article",
        "An editorial or opinion piece.",
        NEWS.NewsArticle,
    )
    add_class(
        g,
        NEWS.Journalist,
        "Journalist",
        "A person who writes or reports news articles.",
        SCHEMA.Person,
    )
    add_class(
        g,
        NEWS.Politician,
        "Politician",
        "A political actor such as an MP, minister, mayor, or party leader.",
        SCHEMA.Person,
    )
    add_class(
        g,
        NEWS.Organisation,
        "Organisation",
        "An organisation mentioned in current UK politics and policy reporting.",
        SCHEMA.Organization,
    )
    add_class(
        g,
        NEWS.NewsOrganisation,
        "News Organisation",
        "A media company or news publisher.",
        NEWS.Organisation,
    )
    add_class(
        g,
        NEWS.Topic,
        "Topic",
        "A policy or public-affairs theme discussed in reporting.",
        SCHEMA.Thing,
    )
    add_class(
        g,
        NEWS.PoliticalParty,
        "Political Party",
        "A political party or party grouping active in UK politics.",
        NEWS.Organisation,
    )
    add_class(
        g,
        NEWS.GovernmentBody,
        "Government Body",
        "A department, regulator, parliamentary body, or public institution.",
        NEWS.Organisation,
    )

    # Classes extending BBC Core Concepts

    add_class(
        g,
        NEWS.NewsEvent,
        "News Event",
        "A real-world event covered by news.",
        CORE.Event,
    )
    add_class(
        g,
        NEWS.PoliticalEvent,
        "Political Event",
        "An election, debate, or policy announcement.",
        NEWS.NewsEvent,
    )
    add_class(
        g,
        NEWS.EconomicEvent,
        "Economic Event",
        "A budget statement, fiscal announcement, spending review, or similar economic event.",
        NEWS.NewsEvent,
    )
    add_class(
        g,
        NEWS.Location,
        "Location",
        "A geographic location mentioned in news.",
        CORE.Place,
    )

    # New classes

    add_class(
        g,
        NEWS.Sentiment,
        "Sentiment",
        "Positive, negative, or neutral sentiment associated with a news article.",
    )

    for label in ["Positive", "Negative", "Neutral"]:
        g.add((NEWS[label], RDF.type, NEWS.Sentiment))
        g.add((NEWS[label], RDFS.label, Literal(label)))

    # Properties extending Schema.org

    add_property(
        g,
        NEWS.hasAuthor,
        "has author",
        "Links an article to the journalist credited with writing it.",
        NEWS.NewsArticle,
        NEWS.Journalist,
        SCHEMA.author,
    )
    add_property(
        g,
        NEWS.publishedBy,
        "published by",
        "Links an article to the news organisation that published it.",
        NEWS.NewsArticle,
        NEWS.NewsOrganisation,
        SCHEMA.publisher,
    )
    add_property(
        g,
        NEWS.hasTopic,
        "has topic",
        "Links an article to a thematic topic discussed in it.",
        NEWS.NewsArticle,
        NEWS.Topic,
        SCHEMA.about,
    )
    add_property(
        g,
        NEWS.mentionsPerson,
        "mentions person",
        "Links an article to a person mentioned in its content.",
        NEWS.NewsArticle,
        SCHEMA.Person,
        SCHEMA.mentions,
    )
    add_property(
        g,
        NEWS.mentionsOrganisation,
        "mentions organisation",
        "Links an article to an organisation mentioned in its content.",
        NEWS.NewsArticle,
        NEWS.Organisation,
        SCHEMA.mentions,
    )
    add_property(
        g,
        NEWS.mentionsLocation,
        "mentions location",
        "Links an article to a location mentioned in its content.",
        NEWS.NewsArticle,
        NEWS.Location,
        SCHEMA.mentions,
    )
    add_property(
        g,
        NEWS.publishedDate,
        "published date",
        "The publication date of a news article.",
        NEWS.NewsArticle,
        XSD.dateTime,
        SCHEMA.datePublished,
    )
    add_property(
        g,
        NEWS.hasUpdateTimestamp,
        "update timestamp",
        "The timestamp of the latest update known for an article.",
        NEWS.NewsArticle,
        XSD.dateTime,
        SCHEMA.dateModified,
    )
    add_property(
        g,
        NEWS.hasSection,
        "has section",
        "The editorial section assigned to an article.",
        NEWS.NewsArticle,
        XSD.string,
        SCHEMA.articleSection,
    )
    add_property(
        g,
        NEWS.articleURL,
        "article URL",
        "The canonical URL of a news article.",
        NEWS.NewsArticle,
        XSD.anyURI,
        SCHEMA.url,
    )
    add_property(
        g,
        NEWS.worksFor,
        "works for",
        "Links a journalist to the news organisation they work for.",
        NEWS.Journalist,
        NEWS.NewsOrganisation,
        SCHEMA.worksFor,
    )

    # Properties extending BBC Core Concepts

    add_property(
        g,
        NEWS.eventLocation,
        "event location",
        "Links a news event to the place where it happened.",
        NEWS.NewsEvent,
        NEWS.Location,
        CORE.eventPlace,
    )
    add_property(
        g,
        NEWS.eventDate,
        "event date",
        "The date on which a news event occurred.",
        NEWS.NewsEvent,
        XSD.date,
        CORE.startDate,
    )
    add_property(
        g,
        NEWS.coversEvent,
        "covers event",
        "Links a news article to the event it covers.",
        NEWS.NewsArticle,
        NEWS.NewsEvent,
        CORE.notablyAssociatedWith,
    )

    # New properties

    add_property(
        g,
        NEWS.hasSentiment,
        "has sentiment",
        "Links an article to its sentiment classification.",
        NEWS.NewsArticle,
        NEWS.Sentiment,
    )
    add_property(
        g,
        NEWS.wordCount,
        "word count",
        "The number of words available for an article representation.",
        NEWS.NewsArticle,
        XSD.integer,
    )
    add_property(
        g,
        NEWS.hasFollowUp,
        "has follow-up",
        "Links an article to a subsequent follow-up article.",
        NEWS.NewsArticle,
        NEWS.NewsArticle,
    )

    return g


def main():
    print("Building UK Politics and Policy News Ontology (TBox)...\n")
    g = build_ontology()

    classes = set(g.subjects(RDF.type, RDFS.Class))
    properties = set(g.subjects(RDF.type, RDF.Property))
    subclass_triples = list(g.triples((None, RDFS.subClassOf, None)))
    subprop_triples = list(g.triples((None, RDFS.subPropertyOf, None)))

    schema_subclasses = [s for s, _, o in subclass_triples if "schema.org" in str(o)]
    schema_subprops = [s for s, _, o in subprop_triples if "schema.org" in str(o)]
    bbc_subclasses = [s for s, _, o in subclass_triples if "bbc.co.uk" in str(o)]
    bbc_subprops = [s for s, _, o in subprop_triples if "bbc.co.uk" in str(o)]

    print(f"  Classes:          {len(classes)}")
    print(f"  Properties:       {len(properties)}")
    print(f"  Total triples:    {len(g)}")
    print(
        f"\n  Schema.org — {len(schema_subclasses)} subclasses, {len(schema_subprops)} subproperties"
    )
    print(f"  BBC Core   — {len(bbc_subclasses)} subclasses, {len(bbc_subprops)} subproperties")

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    g.serialize(str(OUTPUT_PATH), format="turtle")
    print(f"\n  Saved to: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
