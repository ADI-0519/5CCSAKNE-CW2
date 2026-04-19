from pathlib import Path

import pytest
from rdflib import RDF, RDFS, Graph, Namespace

NEWS = Namespace("http://example.org/news#")
SCHEMA = Namespace("https://schema.org/")

KG_PATH = Path("kg/generated/prototype_kg.ttl")


@pytest.fixture(scope="module")
def kg():
    if not KG_PATH.exists():
        pytest.skip("prototype_kg.ttl not found, run the pipeline first")
    g = Graph()
    g.parse(str(KG_PATH))
    return g


def test_politicians_have_seeAlso(kg):
    political_actors = set(kg.subjects(RDF.type, NEWS.PoliticalActor))
    assert len(political_actors) > 0, "no political actors found in KG"

    with_see_also = {
        s
        for s in political_actors
        if any(str(o).startswith("http://www.wikidata.org/") for o in kg.objects(s, RDFS.seeAlso))
    }
    assert with_see_also, f"no political actors in {KG_PATH} have a wikidata seeAlso link"


def test_politician_party_memberOf(kg):
    politicians = set(kg.subjects(RDF.type, NEWS.PoliticalActor))
    assert any(
        (s, SCHEMA.memberOf, o) in kg and (o, RDF.type, NEWS.PoliticalParty) in kg
        for s in politicians
        for o in kg.objects(s, SCHEMA.memberOf)
    ), "no politician has a schema:memberOf link to a news:PoliticalParty"
