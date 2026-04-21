"""Shared domain lexicons and stable classification rules.

This module holds the small, explicit knowledge resources that we treat as
canonical project lexicons rather than ad hoc extraction heuristics. Keeping
them here makes the rule layer easier to audit and avoids duplicating core
classification logic across the pipeline.
"""

POLITICIAN_NAMES = [
    "Keir Starmer",
    "Rishi Sunak",
    "Kemi Badenoch",
    "Angela Rayner",
    "Rachel Reeves",
    "Wes Streeting",
    "Yvette Cooper",
    "David Lammy",
    "Nigel Farage",
    "Ed Davey",
    "John Swinney",
    "Eluned Morgan",
    "Michelle O'Neill",
]

POLITICAL_PARTY_NAMES = [
    "Labour",
    "Labour Party",
    "Conservative",
    "Conservative Party",
    "Liberal Democrats",
    "Green Party",
    "Reform UK",
    "Scottish National Party",
    "SNP",
    "Plaid Cymru",
    "Democratic Unionist Party",
    "DUP",
    "Sinn Fein",
    "Sinn FÃ©in",
]

POLITICAL_PARTY_ALIASES = {
    "labour": "Labour Party",
    "labour party": "Labour Party",
    "conservative": "Conservative Party",
    "conservative party": "Conservative Party",
    "snp": "Scottish National Party",
    "scottish national party": "Scottish National Party",
    "dup": "Democratic Unionist Party",
    "democratic unionist party": "Democratic Unionist Party",
    "sinn fein": "Sinn Fein",
    "sinn fÃƒÂ©in": "Sinn Fein",
}

PARLIAMENTARY_BODY_NAMES = [
    "House of Commons",
    "House of Lords",
    "Westminster Hall",
]

GOVERNMENT_DEPARTMENT_NAMES = [
    "HM Treasury",
    "Treasury",
    "Home Office",
    "Cabinet Office",
    "Department of Health and Social Care",
    "Department for Education",
    "Department for Work and Pensions",
    "Ministry of Defence",
    "Foreign, Commonwealth and Development Office",
    "Foreign, Commonwealth & Development Office",
    "Foreign Office",
    "FCDO",
    "Department for Business and Trade",
    "DBT",
    "Department for Environment, Food and Rural Affairs",
    "DEFRA",
    "Department for Culture, Media and Sport",
    "DCMS",
    "Ministry of Housing, Communities and Local Government",
]

GOVERNMENT_BODY_NAMES = GOVERNMENT_DEPARTMENT_NAMES + [
    "Downing Street",
    "No 10",
    "NHS England",
    "House of Commons",
    "House of Lords",
    "Parliament",
]

UK_LOCATION_NAMES = [
    "London",
    "Westminster",
    "Manchester",
    "Birmingham",
    "Liverpool",
    "Leeds",
    "Bristol",
    "Edinburgh",
    "Glasgow",
    "Cardiff",
    "Belfast",
    "England",
    "Scotland",
    "Wales",
    "Northern Ireland",
    "United Kingdom",
]

TOPIC_GROUPS = {
    "Taxation": ["tax", "taxation", "fiscal", "levy"],
    "Public Spending": ["public spending", "spending review", "spending cuts", "funding"],
    "Economic Policy": ["economy", "economic policy", "growth", "inflation", "interest rates"],
    "Immigration": ["immigration", "asylum", "migrant", "border"],
    "Healthcare": ["nhs", "healthcare", "hospital", "waiting list"],
    "Education": ["education", "school", "university", "teachers"],
    "Energy": ["energy", "net zero", "oil", "gas", "renewable"],
    "Housing": ["housing", "rent", "homes", "planning"],
    "Defence": ["defence", "defense", "armed forces", "military"],
    "Parliament": ["parliament", "commons", "lords", "mp", "mps", "debate"],
    "Government Policy": ["policy", "bill", "legislation", "proposal", "white paper"],
}

POLITICIAN_NAME_SET = frozenset(POLITICIAN_NAMES)
POLITICAL_PARTY_NAME_SET = frozenset(POLITICAL_PARTY_NAMES)
GOVERNMENT_BODY_NAME_SET = frozenset(GOVERNMENT_BODY_NAMES)
UK_LOCATION_NAME_SET = frozenset(UK_LOCATION_NAMES)
TOPIC_NAME_SET = frozenset(TOPIC_GROUPS)

PARLIAMENTARY_BODY_KEYWORDS = frozenset(
    {
        "commons",
        "lords",
        "parliament",
        "committee",
        "house of commons",
        "house of lords",
    }
)

GOVERNMENT_DEPARTMENT_KEYWORDS = frozenset(
    {
        "department",
        "office",
        "treasury",
        "ministry",
        "cabinet",
        "home office",
        "foreign office",
        "department for",
    }
)

GOVERNMENT_BODY_ALIASES = {
    "treasury": "HM Treasury",
    "dfe": "Department for Education",
    "dhsc": "Department of Health and Social Care",
    "dwp": "Department for Work and Pensions",
    "mod": "Ministry of Defence",
    "moj": "Ministry of Justice",
    "foreign office": "Foreign, Commonwealth and Development Office",
    "foreign, commonwealth & development office": "Foreign, Commonwealth and Development Office",
    "fcdo": "Foreign, Commonwealth and Development Office",
    "department for business, energy & industrial strategy": "Department for Business and Trade",
    "department for business, energy and industrial strategy": "Department for Business and Trade",
    "dit": "Department for Business and Trade",
    "dbt": "Department for Business and Trade",
    "defra": "Department for Environment, Food and Rural Affairs",
    "department for digital, culture, media and sport": "Department for Culture, Media and Sport",
    "dcms": "Department for Culture, Media and Sport",
    "department for housing, communities and local government": "Ministry of Housing, Communities and Local Government",
    "department for levelling up, housing and communities": "Ministry of Housing, Communities and Local Government",
    "dluhc": "Ministry of Housing, Communities and Local Government",
}

MINISTER_ROLE_DEPARTMENT_MAP = {
    "foreign secretary": "Foreign, Commonwealth and Development Office",
    "trade minister": "Department for Business and Trade",
    "trade secretary": "Department for Business and Trade",
    "business and trade secretary": "Department for Business and Trade",
    "minister for industry": "Department for Business and Trade",
    "chancellor": "HM Treasury",
    "treasury minister": "HM Treasury",
    "chief secretary to the treasury": "HM Treasury",
    "home secretary": "Home Office",
    "health secretary": "Department of Health and Social Care",
    "education secretary": "Department for Education",
    "work and pensions secretary": "Department for Work and Pensions",
    "defence secretary": "Ministry of Defence",
    "environment secretary": "Department for Environment, Food and Rural Affairs",
    "minister of state for housing and planning": "Ministry of Housing, Communities and Local Government",
    "housing and planning": "Ministry of Housing, Communities and Local Government",
    "secretary of state for culture, media and sport": "Department for Culture, Media and Sport",
    "minister for the cabinet office": "Cabinet Office",
    "paymaster general": "Cabinet Office",
}

MINISTERIAL_STATEMENT_SIGNAL_TERMS = frozenset(
    {
        "ministerial statement",
        "minister of state",
        "minister for",
        "secretary of state",
        "secretary",
        "chancellor",
        "paymaster general",
        "fcdo",
        "foreign office",
        "foreign, commonwealth and development office",
        "home office",
        "cabinet office",
        "treasury",
        "department for",
        "department of",
    }
)


def _normalise_label(value):
    return " ".join(str(value or "").strip().lower().split())


def canonicalise_government_body_name(name):
    cleaned = " ".join(str(name or "").strip().split())
    if not cleaned:
        return ""
    return GOVERNMENT_BODY_ALIASES.get(_normalise_label(cleaned), cleaned)


def canonicalise_political_party_name(name):
    cleaned = " ".join(str(name or "").strip().split())
    if not cleaned:
        return ""
    return POLITICAL_PARTY_ALIASES.get(_normalise_label(cleaned), cleaned)


PARLIAMENTARY_BODY_NAME_SET = frozenset(_normalise_label(name) for name in PARLIAMENTARY_BODY_NAMES)
GOVERNMENT_DEPARTMENT_NAME_SET = frozenset(
    _normalise_label(canonicalise_government_body_name(name))
    for name in GOVERNMENT_DEPARTMENT_NAMES
)
GOVERNMENT_BODY_MATCH_SET = frozenset(_normalise_label(name) for name in GOVERNMENT_BODY_NAMES)


def classify_official_body_kind(name):
    """Return the stable body kind label used by ontology mapping.

    The ordering is deliberate:
    1. exact parliamentary bodies
    2. exact government departments
    3. high-precision keyword fallbacks
    4. generic government body
    """

    lowered = _normalise_label(canonicalise_government_body_name(name))
    if lowered in PARLIAMENTARY_BODY_NAME_SET:
        return "parliamentary_body"
    if lowered in GOVERNMENT_DEPARTMENT_NAME_SET:
        return "government_department"
    if any(keyword in lowered for keyword in PARLIAMENTARY_BODY_KEYWORDS):
        return "parliamentary_body"
    if any(keyword in lowered for keyword in GOVERNMENT_DEPARTMENT_KEYWORDS):
        return "government_department"
    return "government_body"


def classify_known_politicians(people):
    return sorted(person for person in people if person in POLITICIAN_NAME_SET)


def classify_known_political_parties(organisations):
    canonicalised = []
    for organisation in organisations:
        cleaned = " ".join(str(organisation or "").strip().split())
        if not cleaned:
            continue
        canonical = canonicalise_political_party_name(cleaned)
        if (
            cleaned in POLITICAL_PARTY_NAME_SET
            or canonical in POLITICAL_PARTY_NAME_SET
            or _normalise_label(cleaned) in POLITICAL_PARTY_ALIASES
        ):
            canonicalised.append(canonical)
    return sorted(set(canonicalised))


def classify_known_government_bodies(organisations):
    canonicalised = []
    for organisation in organisations:
        cleaned = " ".join(str(organisation or "").strip().split())
        if not cleaned:
            continue
        canonical = canonicalise_government_body_name(cleaned)
        lowered_cleaned = _normalise_label(cleaned)
        lowered_canonical = _normalise_label(canonical)
        if (
            lowered_cleaned in GOVERNMENT_BODY_MATCH_SET
            or lowered_canonical in GOVERNMENT_BODY_MATCH_SET
        ):
            canonicalised.append(canonical)
    return sorted(set(canonicalised))


def infer_government_bodies_from_text(text):
    haystack = _normalise_label(text)
    if not haystack:
        return []

    matches = set()
    for name in GOVERNMENT_BODY_NAMES:
        lowered_name = _normalise_label(name)
        if lowered_name and lowered_name in haystack:
            matches.add(canonicalise_government_body_name(name))

    for role_phrase, department_name in MINISTER_ROLE_DEPARTMENT_MAP.items():
        if role_phrase in haystack:
            matches.add(department_name)

    return sorted(matches)


def has_ministerial_statement_signal(*texts):
    haystack = " ".join(_normalise_label(text) for text in texts if text)
    if not haystack:
        return False
    if "ministerial statement" in haystack:
        return True
    if "statement" not in haystack:
        return False
    return any(term in haystack for term in MINISTERIAL_STATEMENT_SIGNAL_TERMS)
