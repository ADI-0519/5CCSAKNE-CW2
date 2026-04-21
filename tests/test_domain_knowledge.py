from src.config import CONFIG
from src.domain_knowledge import (
    canonicalise_government_body_name,
    canonicalise_political_party_name,
    classify_known_government_bodies,
    classify_known_political_parties,
    classify_known_politicians,
    classify_official_body_kind,
    has_ministerial_statement_signal,
    infer_government_bodies_from_text,
)


def test_classify_official_body_kind_uses_exact_and_keyword_rules():
    assert classify_official_body_kind("House of Commons") == "parliamentary_body"
    assert classify_official_body_kind("Department for Education") == "government_department"
    assert classify_official_body_kind("NHS England") == "government_body"


def test_config_exposes_structured_rule_groups():
    assert "RETRIEVAL_CONFIG" in CONFIG
    assert "CANONICAL_LEXICONS" in CONFIG
    assert "BODY_CLASSIFICATION_RULES" in CONFIG
    assert "FILTER_RULES" in CONFIG
    assert (
        "Department for Education"
        in CONFIG["BODY_CLASSIFICATION_RULES"]["government_department_names"]
    )


def test_shared_exact_match_classifiers_are_stable():
    assert classify_known_politicians(["Keir Starmer", "Someone Else"]) == ["Keir Starmer"]
    assert classify_known_political_parties(["Labour", "BBC News"]) == ["Labour Party"]
    assert classify_known_government_bodies(["Treasury", "BBC News"]) == ["HM Treasury"]


def test_government_body_aliases_are_canonicalised():
    assert (
        canonicalise_government_body_name("FCDO") == "Foreign, Commonwealth and Development Office"
    )
    assert canonicalise_government_body_name("DCMS") == "Department for Culture, Media and Sport"
    assert classify_known_government_bodies(["FCDO", "BBC News"]) == [
        "Foreign, Commonwealth and Development Office"
    ]


def test_political_party_aliases_are_canonicalised():
    assert canonicalise_political_party_name("Labour") == "Labour Party"
    assert classify_known_political_parties(["Labour", "Labour Party", "BBC News"]) == [
        "Labour Party"
    ]


def test_ministerial_signal_and_department_inference_are_conservative():
    assert has_ministerial_statement_signal("FCDO statement on Iran") is True
    assert has_ministerial_statement_signal("UK statement at the UN Security Council") is False
    assert (
        has_ministerial_statement_signal(
            "Ministers met this afternoon to discuss the latest developments"
        )
        is False
    )
    assert infer_government_bodies_from_text("Trade Minister speech at Chatham House") == [
        "Department for Business and Trade"
    ]
    assert infer_government_bodies_from_text(
        "My Honourable Friend the Minister of State for Housing and Planning has made the following statement."
    ) == ["Ministry of Housing, Communities and Local Government"]
