from pathlib import Path

from rdflib import Graph, Literal, Namespace
from rdflib.namespace import OWL, RDF, RDFS, XSD

NEWS = Namespace("http://example.org/news#")
SCHEMA = Namespace("https://schema.org/")
CORE = Namespace("http://www.bbc.co.uk/ontologies/coreconcepts/")

OUTPUT_PATH = Path(__file__).parent.parent / "ontology" / "news_ontology.ttl"


def build_ontology() -> Graph:
    g = Graph()
    g.bind("news", NEWS)
    g.bind("schema", SCHEMA)
    g.bind("core", CORE)
    g.bind("owl", OWL)
    g.bind("xsd", XSD)

    g.add((NEWS[""], RDF.type, OWL.Ontology))
    g.add((NEWS[""], RDFS.label, Literal("Current News Ontology")))
    g.add(
        (
            NEWS[""],
            RDFS.comment,
            Literal(
                "An ontology for representing current news articles, events, "
                "journalists, organisations, and their relationships. "
                "Extends Schema.org and the BBC Core Concepts Ontology."
            ),
        )
    )

    # ── Classes extending Schema.org ─────────────────────────────────────

    g.add((NEWS.NewsArticle, RDF.type, RDFS.Class))
    g.add((NEWS.NewsArticle, RDFS.subClassOf, SCHEMA.NewsArticle))
    g.add((NEWS.NewsArticle, RDFS.label, Literal("News Article")))
    g.add(
        (
            NEWS.NewsArticle,
            RDFS.comment,
            Literal("A news article from any source in our knowledge graph."),
        )
    )

    g.add((NEWS.BreakingNewsArticle, RDF.type, RDFS.Class))
    g.add((NEWS.BreakingNewsArticle, RDFS.subClassOf, NEWS.NewsArticle))
    g.add((NEWS.BreakingNewsArticle, RDFS.label, Literal("Breaking News Article")))
    g.add(
        (NEWS.BreakingNewsArticle, RDFS.comment, Literal("An article published as breaking news."))
    )

    g.add((NEWS.OpinionArticle, RDF.type, RDFS.Class))
    g.add((NEWS.OpinionArticle, RDFS.subClassOf, NEWS.NewsArticle))
    g.add((NEWS.OpinionArticle, RDFS.label, Literal("Opinion Article")))
    g.add((NEWS.OpinionArticle, RDFS.comment, Literal("An editorial or opinion piece.")))

    g.add((NEWS.Journalist, RDF.type, RDFS.Class))
    g.add((NEWS.Journalist, RDFS.subClassOf, SCHEMA.Person))
    g.add((NEWS.Journalist, RDFS.label, Literal("Journalist")))
    g.add((NEWS.Journalist, RDFS.comment, Literal("A person who writes or reports news articles.")))

    g.add((NEWS.NewsOrganisation, RDF.type, RDFS.Class))
    g.add((NEWS.NewsOrganisation, RDFS.subClassOf, SCHEMA.Organization))
    g.add((NEWS.NewsOrganisation, RDFS.label, Literal("News Organisation")))
    g.add((NEWS.NewsOrganisation, RDFS.comment, Literal("A media company or news publisher.")))

    g.add((NEWS.Topic, RDF.type, RDFS.Class))
    g.add((NEWS.Topic, RDFS.subClassOf, SCHEMA.Thing))
    g.add((NEWS.Topic, RDFS.label, Literal("Topic")))
    g.add((NEWS.Topic, RDFS.comment, Literal("A thematic category or subject area.")))

    # ── Classes extending BBC Core Concepts ──────────────────────────────

    g.add((NEWS.NewsEvent, RDF.type, RDFS.Class))
    g.add((NEWS.NewsEvent, RDFS.subClassOf, CORE.Event))
    g.add((NEWS.NewsEvent, RDFS.label, Literal("News Event")))
    g.add((NEWS.NewsEvent, RDFS.comment, Literal("A real-world event covered by news.")))

    g.add((NEWS.PoliticalEvent, RDF.type, RDFS.Class))
    g.add((NEWS.PoliticalEvent, RDFS.subClassOf, NEWS.NewsEvent))
    g.add((NEWS.PoliticalEvent, RDFS.label, Literal("Political Event")))
    g.add(
        (NEWS.PoliticalEvent, RDFS.comment, Literal("An election, debate, or policy announcement."))
    )

    g.add((NEWS.NaturalDisasterEvent, RDF.type, RDFS.Class))
    g.add((NEWS.NaturalDisasterEvent, RDFS.subClassOf, NEWS.NewsEvent))
    g.add((NEWS.NaturalDisasterEvent, RDFS.label, Literal("Natural Disaster Event")))
    g.add(
        (NEWS.NaturalDisasterEvent, RDFS.comment, Literal("An earthquake, flood, wildfire, etc."))
    )

    g.add((NEWS.Location, RDF.type, RDFS.Class))
    g.add((NEWS.Location, RDFS.subClassOf, CORE.Place))
    g.add((NEWS.Location, RDFS.label, Literal("Location")))
    g.add((NEWS.Location, RDFS.comment, Literal("A geographic location mentioned in news.")))

    # ── New classes ────────────────────────────────────────────────────

    g.add((NEWS.Sentiment, RDF.type, RDFS.Class))
    g.add((NEWS.Sentiment, RDFS.label, Literal("Sentiment")))
    g.add((NEWS.Sentiment, RDFS.comment, Literal("Positive, negative, or neutral sentiment.")))

    for label in ["Positive", "Negative", "Neutral"]:
        g.add((NEWS[label], RDF.type, NEWS.Sentiment))
        g.add((NEWS[label], RDFS.label, Literal(label)))

    # ── Properties extending Schema.org ──────────────────────────────────

    g.add((NEWS.hasAuthor, RDF.type, RDF.Property))
    g.add((NEWS.hasAuthor, RDFS.subPropertyOf, SCHEMA.author))
    g.add((NEWS.hasAuthor, RDFS.domain, NEWS.NewsArticle))
    g.add((NEWS.hasAuthor, RDFS.range, NEWS.Journalist))
    g.add((NEWS.hasAuthor, RDFS.label, Literal("has author")))

    g.add((NEWS.publishedBy, RDF.type, RDF.Property))
    g.add((NEWS.publishedBy, RDFS.subPropertyOf, SCHEMA.publisher))
    g.add((NEWS.publishedBy, RDFS.domain, NEWS.NewsArticle))
    g.add((NEWS.publishedBy, RDFS.range, NEWS.NewsOrganisation))
    g.add((NEWS.publishedBy, RDFS.label, Literal("published by")))

    g.add((NEWS.hasTopic, RDF.type, RDF.Property))
    g.add((NEWS.hasTopic, RDFS.subPropertyOf, SCHEMA.about))
    g.add((NEWS.hasTopic, RDFS.domain, NEWS.NewsArticle))
    g.add((NEWS.hasTopic, RDFS.range, NEWS.Topic))
    g.add((NEWS.hasTopic, RDFS.label, Literal("has topic")))

    g.add((NEWS.mentionsPerson, RDF.type, RDF.Property))
    g.add((NEWS.mentionsPerson, RDFS.subPropertyOf, SCHEMA.mentions))
    g.add((NEWS.mentionsPerson, RDFS.domain, NEWS.NewsArticle))
    g.add((NEWS.mentionsPerson, RDFS.range, SCHEMA.Person))
    g.add((NEWS.mentionsPerson, RDFS.label, Literal("mentions person")))

    g.add((NEWS.mentionsOrganisation, RDF.type, RDF.Property))
    g.add((NEWS.mentionsOrganisation, RDFS.subPropertyOf, SCHEMA.mentions))
    g.add((NEWS.mentionsOrganisation, RDFS.domain, NEWS.NewsArticle))
    g.add((NEWS.mentionsOrganisation, RDFS.range, SCHEMA.Organization))
    g.add((NEWS.mentionsOrganisation, RDFS.label, Literal("mentions organisation")))

    g.add((NEWS.mentionsLocation, RDF.type, RDF.Property))
    g.add((NEWS.mentionsLocation, RDFS.subPropertyOf, SCHEMA.mentions))
    g.add((NEWS.mentionsLocation, RDFS.domain, NEWS.NewsArticle))
    g.add((NEWS.mentionsLocation, RDFS.range, NEWS.Location))
    g.add((NEWS.mentionsLocation, RDFS.label, Literal("mentions location")))

    g.add((NEWS.publishedDate, RDF.type, RDF.Property))
    g.add((NEWS.publishedDate, RDFS.subPropertyOf, SCHEMA.datePublished))
    g.add((NEWS.publishedDate, RDFS.domain, NEWS.NewsArticle))
    g.add((NEWS.publishedDate, RDFS.range, XSD.dateTime))
    g.add((NEWS.publishedDate, RDFS.label, Literal("published date")))

    g.add((NEWS.hasUpdateTimestamp, RDF.type, RDF.Property))
    g.add((NEWS.hasUpdateTimestamp, RDFS.subPropertyOf, SCHEMA.dateModified))
    g.add((NEWS.hasUpdateTimestamp, RDFS.domain, NEWS.NewsArticle))
    g.add((NEWS.hasUpdateTimestamp, RDFS.range, XSD.dateTime))
    g.add((NEWS.hasUpdateTimestamp, RDFS.label, Literal("update timestamp")))

    g.add((NEWS.hasSection, RDF.type, RDF.Property))
    g.add((NEWS.hasSection, RDFS.subPropertyOf, SCHEMA.articleSection))
    g.add((NEWS.hasSection, RDFS.domain, NEWS.NewsArticle))
    g.add((NEWS.hasSection, RDFS.range, XSD.string))
    g.add((NEWS.hasSection, RDFS.label, Literal("has section")))

    g.add((NEWS.articleURL, RDF.type, RDF.Property))
    g.add((NEWS.articleURL, RDFS.subPropertyOf, SCHEMA.url))
    g.add((NEWS.articleURL, RDFS.domain, NEWS.NewsArticle))
    g.add((NEWS.articleURL, RDFS.range, XSD.anyURI))
    g.add((NEWS.articleURL, RDFS.label, Literal("article URL")))

    g.add((NEWS.worksFor, RDF.type, RDF.Property))
    g.add((NEWS.worksFor, RDFS.subPropertyOf, SCHEMA.worksFor))
    g.add((NEWS.worksFor, RDFS.domain, NEWS.Journalist))
    g.add((NEWS.worksFor, RDFS.range, NEWS.NewsOrganisation))
    g.add((NEWS.worksFor, RDFS.label, Literal("works for")))

    # ── Properties extending BBC Core Concepts ───────────────────────────

    g.add((NEWS.eventLocation, RDF.type, RDF.Property))
    g.add((NEWS.eventLocation, RDFS.subPropertyOf, CORE.eventPlace))
    g.add((NEWS.eventLocation, RDFS.domain, NEWS.NewsEvent))
    g.add((NEWS.eventLocation, RDFS.range, NEWS.Location))
    g.add((NEWS.eventLocation, RDFS.label, Literal("event location")))

    g.add((NEWS.eventDate, RDF.type, RDF.Property))
    g.add((NEWS.eventDate, RDFS.subPropertyOf, CORE.startDate))
    g.add((NEWS.eventDate, RDFS.domain, NEWS.NewsEvent))
    g.add((NEWS.eventDate, RDFS.range, XSD.dateTime))
    g.add((NEWS.eventDate, RDFS.label, Literal("event date")))

    g.add((NEWS.coversEvent, RDF.type, RDF.Property))
    g.add((NEWS.coversEvent, RDFS.subPropertyOf, CORE.notablyAssociatedWith))
    g.add((NEWS.coversEvent, RDFS.domain, NEWS.NewsArticle))
    g.add((NEWS.coversEvent, RDFS.range, NEWS.NewsEvent))
    g.add((NEWS.coversEvent, RDFS.label, Literal("covers event")))

    # ── New properties ─────────────────────────────────────────────────

    g.add((NEWS.hasSentiment, RDF.type, RDF.Property))
    g.add((NEWS.hasSentiment, RDFS.domain, NEWS.NewsArticle))
    g.add((NEWS.hasSentiment, RDFS.range, NEWS.Sentiment))
    g.add((NEWS.hasSentiment, RDFS.label, Literal("has sentiment")))

    g.add((NEWS.wordCount, RDF.type, RDF.Property))
    g.add((NEWS.wordCount, RDFS.domain, NEWS.NewsArticle))
    g.add((NEWS.wordCount, RDFS.range, XSD.integer))
    g.add((NEWS.wordCount, RDFS.label, Literal("word count")))

    g.add((NEWS.hasFollowUp, RDF.type, RDF.Property))
    g.add((NEWS.hasFollowUp, RDFS.domain, NEWS.NewsArticle))
    g.add((NEWS.hasFollowUp, RDFS.range, NEWS.NewsArticle))
    g.add((NEWS.hasFollowUp, RDFS.label, Literal("has follow-up")))

    return g


def main():
    print("Building Current News Ontology (TBox)...\n")
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
