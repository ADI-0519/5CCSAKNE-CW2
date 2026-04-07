"""Tests for KG completion/enrichment."""

from rdflib import RDF, Literal
from rdflib.namespace import XSD

from src.build_ontology import NEWS, SCHEMA, build_ontology
from src.complete_kg import enrich_graph


def add_named_entity(graph, entity_uri, label, rdf_types):
    for rdf_type in rdf_types:
        graph.add((entity_uri, RDF.type, rdf_type))
    graph.add((entity_uri, SCHEMA.name, Literal(label)))


def test_enrich_graph_adds_article_completion_metadata():
    graph = build_ontology()
    article_uri = NEWS["article/completion_a"]
    graph.add((article_uri, RDF.type, NEWS.NewsArticle))
    graph.add((article_uri, RDF.type, SCHEMA.NewsArticle))
    graph.add((article_uri, SCHEMA.headline, Literal("Treasury faces pressure over budget plan")))
    graph.add(
        (
            article_uri,
            SCHEMA.description,
            Literal("Ministers defended public spending decisions after the spring budget."),
        )
    )
    graph.add(
        (article_uri, NEWS.publishedDate, Literal("2026-03-12T10:00:00Z", datatype=XSD.dateTime))
    )

    enriched = enrich_graph(graph)
    article_nodes = list(enriched.subjects(RDF.type, NEWS.NewsArticle))

    assert article_nodes
    for article_uri in article_nodes:
        assert (article_uri, NEWS.wordCount, None) in enriched
        assert (article_uri, NEWS.hasSentiment, None) in enriched
        assert (article_uri, NEWS.hasSection, None) in enriched
        assert (article_uri, NEWS.hasUpdateTimestamp, None) in enriched


def test_enrich_graph_infers_additional_topics():
    graph = build_ontology()
    article_uri = NEWS["article/completion_topics"]
    graph.add((article_uri, RDF.type, NEWS.NewsArticle))
    graph.add((article_uri, RDF.type, SCHEMA.NewsArticle))
    graph.add(
        (article_uri, SCHEMA.headline, Literal("Treasury outlines new public spending plans"))
    )
    graph.add(
        (
            article_uri,
            SCHEMA.description,
            Literal("The government defended funding choices in its latest spending review."),
        )
    )
    graph.add(
        (article_uri, NEWS.publishedDate, Literal("2026-03-18T10:00:00Z", datatype=XSD.dateTime))
    )

    enriched = enrich_graph(graph)
    topic_uri = NEWS["topic/Public_Spending"]
    assert (topic_uri, RDF.type, NEWS.Topic) in enriched
    assert (article_uri, NEWS.hasTopic, topic_uri) in enriched


def test_enrich_graph_classifies_articles_and_adds_follow_up():
    graph = build_ontology()
    publisher_uri = NEWS["org/Daily_News"]
    org_uri = NEWS["org/City_Council"]

    add_named_entity(
        graph,
        publisher_uri,
        "Daily News",
        (NEWS.NewsOrganisation, NEWS.Organisation, SCHEMA.Organization),
    )
    add_named_entity(graph, org_uri, "City Council", (NEWS.Organisation, SCHEMA.Organization))

    article_1 = NEWS["article/a1"]
    article_2 = NEWS["article/a2"]

    for article_uri, headline, description, published in (
        (
            article_1,
            "Breaking policy update from city hall",
            "Government officials announced a new policy today.",
            "2024-01-01T10:00:00Z",
        ),
        (
            article_2,
            "Opinion: analysis of the city policy response",
            "Commentary on how the policy may develop next week.",
            "2024-01-03T08:00:00Z",
        ),
    ):
        graph.add((article_uri, RDF.type, NEWS.NewsArticle))
        graph.add((article_uri, RDF.type, SCHEMA.NewsArticle))
        graph.add((article_uri, SCHEMA.headline, Literal(headline)))
        graph.add((article_uri, SCHEMA.description, Literal(description)))
        graph.add((article_uri, NEWS.publishedDate, Literal(published, datatype=XSD.dateTime)))
        graph.add((article_uri, NEWS.publishedBy, publisher_uri))
        graph.add((article_uri, NEWS.mentionsOrganisation, org_uri))

    enriched = enrich_graph(graph)

    assert (article_1, RDF.type, NEWS.BreakingNewsArticle) in enriched
    assert (article_2, RDF.type, NEWS.OpinionArticle) in enriched
    assert (article_1, NEWS.hasFollowUp, article_2) in enriched


def test_enrich_graph_does_not_add_follow_up_for_cross_publisher_topic_overlap():
    graph = build_ontology()
    publisher_a = NEWS["org/Publisher_A"]
    publisher_b = NEWS["org/Publisher_B"]
    topic_uri = NEWS["topic/Parliament"]

    add_named_entity(
        graph,
        publisher_a,
        "Publisher A",
        (NEWS.NewsOrganisation, NEWS.Organisation, SCHEMA.Organization),
    )
    add_named_entity(
        graph,
        publisher_b,
        "Publisher B",
        (NEWS.NewsOrganisation, NEWS.Organisation, SCHEMA.Organization),
    )

    graph.add((topic_uri, RDF.type, NEWS.Topic))
    graph.add((topic_uri, SCHEMA.name, Literal("Parliament")))

    article_1 = NEWS["article/cross_pub_a"]
    article_2 = NEWS["article/cross_pub_b"]

    for article_uri, publisher_uri, headline, published in (
        (
            article_1,
            publisher_a,
            "Parliament debates welfare proposal",
            "2026-03-10T08:00:00Z",
        ),
        (
            article_2,
            publisher_b,
            "Parliament update on different budget issue",
            "2026-03-11T09:00:00Z",
        ),
    ):
        graph.add((article_uri, RDF.type, NEWS.NewsArticle))
        graph.add((article_uri, RDF.type, SCHEMA.NewsArticle))
        graph.add((article_uri, SCHEMA.headline, Literal(headline)))
        graph.add((article_uri, NEWS.publishedDate, Literal(published, datatype=XSD.dateTime)))
        graph.add((article_uri, NEWS.publishedBy, publisher_uri))
        graph.add((article_uri, NEWS.hasTopic, topic_uri))

    enriched = enrich_graph(graph)

    assert (article_1, NEWS.hasFollowUp, article_2) not in enriched


def test_enrich_graph_requires_strong_same_publisher_signal_for_follow_up():
    graph = build_ontology()
    publisher_uri = NEWS["org/Local_Press"]
    org_uri = NEWS["org/Treasury"]
    topic_uri = NEWS["topic/Government_Policy"]

    add_named_entity(
        graph,
        publisher_uri,
        "Local Press",
        (NEWS.NewsOrganisation, NEWS.Organisation, SCHEMA.Organization),
    )
    add_named_entity(
        graph, org_uri, "Treasury", (NEWS.GovernmentBody, NEWS.Organisation, SCHEMA.Organization)
    )
    graph.add((topic_uri, RDF.type, NEWS.Topic))
    graph.add((topic_uri, SCHEMA.name, Literal("Government Policy")))

    article_1 = NEWS["article/weak_follow_up_a"]
    article_2 = NEWS["article/weak_follow_up_b"]

    for article_uri, headline, description, published in (
        (
            article_1,
            "Treasury outlines fiscal proposal",
            "Officials discussed a policy change.",
            "2026-03-10T10:00:00Z",
        ),
        (
            article_2,
            "Treasury comment on transport funding",
            "A separate government policy debate continues.",
            "2026-03-12T09:00:00Z",
        ),
    ):
        graph.add((article_uri, RDF.type, NEWS.NewsArticle))
        graph.add((article_uri, RDF.type, SCHEMA.NewsArticle))
        graph.add((article_uri, SCHEMA.headline, Literal(headline)))
        graph.add((article_uri, SCHEMA.description, Literal(description)))
        graph.add((article_uri, NEWS.publishedDate, Literal(published, datatype=XSD.dateTime)))
        graph.add((article_uri, NEWS.publishedBy, publisher_uri))
        graph.add((article_uri, NEWS.mentionsOrganisation, org_uri))
        graph.add((article_uri, NEWS.hasTopic, topic_uri))

    enriched = enrich_graph(graph)

    assert (article_1, NEWS.hasFollowUp, article_2) not in enriched


def test_enrich_graph_does_not_link_opinion_articles_as_follow_up_seeds():
    graph = build_ontology()
    publisher_uri = NEWS["org/Guardian"]
    org_uri = NEWS["org/Reform_UK"]
    topic_one = NEWS["topic/Parliament"]
    topic_two = NEWS["topic/Government_Policy"]

    add_named_entity(
        graph,
        publisher_uri,
        "The Guardian",
        (NEWS.NewsOrganisation, NEWS.Organisation, SCHEMA.Organization),
    )
    add_named_entity(
        graph,
        org_uri,
        "Reform UK",
        (NEWS.PoliticalParty, NEWS.Organisation, SCHEMA.Organization),
    )
    for topic_uri, label in ((topic_one, "Parliament"), (topic_two, "Government Policy")):
        graph.add((topic_uri, RDF.type, NEWS.Topic))
        graph.add((topic_uri, SCHEMA.name, Literal(label)))

    opinion_article = NEWS["article/opinion_seed"]
    live_article = NEWS["article/live_target"]

    graph.add((opinion_article, RDF.type, NEWS.NewsArticle))
    graph.add((opinion_article, RDF.type, NEWS.OpinionArticle))
    graph.add((opinion_article, RDF.type, SCHEMA.NewsArticle))
    graph.add(
        (
            opinion_article,
            SCHEMA.headline,
            Literal("Opinion: Nigel Farage and Reform UK are warping British politics"),
        )
    )
    graph.add(
        (
            opinion_article,
            SCHEMA.description,
            Literal("A comment piece about Parliament and government policy."),
        )
    )
    graph.add(
        (
            opinion_article,
            NEWS.publishedDate,
            Literal("2026-03-22T10:00:00Z", datatype=XSD.dateTime),
        )
    )
    graph.add((opinion_article, NEWS.publishedBy, publisher_uri))
    graph.add((opinion_article, NEWS.mentionsOrganisation, org_uri))
    graph.add((opinion_article, NEWS.hasTopic, topic_one))
    graph.add((opinion_article, NEWS.hasTopic, topic_two))

    graph.add((live_article, RDF.type, NEWS.NewsArticle))
    graph.add((live_article, RDF.type, NEWS.BreakingNewsArticle))
    graph.add((live_article, RDF.type, SCHEMA.NewsArticle))
    graph.add(
        (
            live_article,
            SCHEMA.headline,
            Literal("UK politics live: Starmer faces Reform UK attacks in Parliament"),
        )
    )
    graph.add(
        (
            live_article,
            SCHEMA.description,
            Literal("Rolling coverage of Parliament and government policy updates."),
        )
    )
    graph.add(
        (live_article, NEWS.publishedDate, Literal("2026-03-23T10:00:00Z", datatype=XSD.dateTime))
    )
    graph.add((live_article, NEWS.publishedBy, publisher_uri))
    graph.add((live_article, NEWS.mentionsOrganisation, org_uri))
    graph.add((live_article, NEWS.hasTopic, topic_one))
    graph.add((live_article, NEWS.hasTopic, topic_two))

    enriched = enrich_graph(graph)

    assert (opinion_article, NEWS.hasFollowUp, live_article) not in enriched


def test_enrich_graph_uses_openai_completion_when_available(monkeypatch):
    monkeypatch.setattr(
        "src.complete_kg.maybe_complete_article_with_openai",
        lambda article_key, article_payload, heuristic_result: {
            "sentiment": "Positive",
            "section": "Politics",
            "article_types": ["OpinionArticle"],
            "additional_topics": ["Healthcare"],
        },
    )

    graph = build_ontology()
    article_uri = NEWS["article/llm_completion"]
    graph.add((article_uri, RDF.type, NEWS.NewsArticle))
    graph.add((article_uri, RDF.type, SCHEMA.NewsArticle))
    graph.add((article_uri, SCHEMA.headline, Literal("Health secretary defends NHS plan")))
    graph.add(
        (
            article_uri,
            SCHEMA.description,
            Literal("Ministers said the NHS proposal would improve services."),
        )
    )
    graph.add(
        (article_uri, NEWS.publishedDate, Literal("2026-03-22T10:00:00Z", datatype=XSD.dateTime))
    )

    enriched = enrich_graph(graph)

    assert (article_uri, NEWS.hasSentiment, NEWS.Positive) in enriched
    assert (article_uri, NEWS.hasSection, Literal("Politics")) in enriched
    assert (article_uri, RDF.type, NEWS.OpinionArticle) in enriched
    assert (article_uri, NEWS.hasTopic, NEWS["topic/Healthcare"]) in enriched
