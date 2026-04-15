import pytest
from pathlib import Path
from rdflib import Graph, Namespace, RDF, RDFS

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
    politicians = set(kg.subjects(RDF.type, NEWS.Politician))
    assert len(politicians) > 0, "no politicians found in KG"

    with_see_also = {
        s for s in politicians
        if any(
            str(o).startswith("http://www.wikidata.org/")
            for o in kg.objects(s, RDFS.seeAlso)
        )
    }
    ratio = len(with_see_also) / len(politicians)
    assert ratio >= 0.5, (
        f"only {len(with_see_also)}/{len(politicians)} politicians have a wikidata seeAlso"
    )


def test_politician_party_memberOf(kg):
    politicians = set(kg.subjects(RDF.type, NEWS.Politician))
    assert any(
        (s, SCHEMA.memberOf, o) in kg and (o, RDF.type, NEWS.PoliticalParty) in kg
        for s in politicians
        for o in kg.objects(s, SCHEMA.memberOf)
    ), "no politician has a schema:memberOf link to a news:PoliticalParty"