"""Shared domain lexicons and stable classification rules.

This module holds the small, explicit knowledge resources that we treat as
canonical project lexicons rather than ad hoc extraction heuristics. Keeping
them here makes the rule layer easier to audit and avoids duplicating core
classification logic across the pipeline.
"""

import re

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
    "Department for Transport",
    "DfT",
    "Department for Environment, Food and Rural Affairs",
    "DEFRA",
    "Department for Culture, Media and Sport",
    "DCMS",
    "Ministry of Housing, Communities and Local Government",
    "Ministry of Justice",
    "MoJ",
    "Department for Science, Innovation and Technology",
    "DSIT",
    "Department for Energy Security and Net Zero",
    "DESNZ",
]

GOVERNMENT_BODY_NAMES = GOVERNMENT_DEPARTMENT_NAMES + [
    "Downing Street",
    "No 10",
    "Prime Minister's Office",
    "NHS England",
    "HM Revenue and Customs",
    "HMRC",
    "Driver and Vehicle Licensing Agency",
    "DVLA",
    "Intellectual Property Office",
    "IPO",
    "Office for National Statistics",
    "ONS",
    "Charity Commission",
    "Attorney General's Office",
    "Welsh Government",
    "Scottish Government",
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
        "government",
        "home office",
        "foreign office",
        "department for",
    }
)

GOVERNMENT_BODY_ALIASES = {
    "treasury": "HM Treasury",
    "the treasury": "HM Treasury",
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
    "department for international trade": "Department for Business and Trade",
    "dit": "Department for Business and Trade",
    "dbt": "Department for Business and Trade",
    "department for transport": "Department for Transport",
    "dft": "Department for Transport",
    "defra": "Department for Environment, Food and Rural Affairs",
    "department for digital, culture, media and sport": "Department for Culture, Media and Sport",
    "dcms": "Department for Culture, Media and Sport",
    "department for housing, communities and local government": "Ministry of Housing, Communities and Local Government",
    "department for levelling up, housing and communities": "Ministry of Housing, Communities and Local Government",
    "dluhc": "Ministry of Housing, Communities and Local Government",
    "ministry of justice": "Ministry of Justice",
    "department for science, innovation and technology": "Department for Science, Innovation and Technology",
    "department for science, innovation & technology": "Department for Science, Innovation and Technology",
    "dsit": "Department for Science, Innovation and Technology",
    "department for energy security and net zero": "Department for Energy Security and Net Zero",
    "department for energy security & net zero": "Department for Energy Security and Net Zero",
    "desnz": "Department for Energy Security and Net Zero",
    "hm revenue and customs": "HM Revenue and Customs",
    "hmrc": "HM Revenue and Customs",
    "driver and vehicle licensing agency": "Driver and Vehicle Licensing Agency",
    "dvla": "Driver and Vehicle Licensing Agency",
    "intellectual property office": "Intellectual Property Office",
    "ipo": "Intellectual Property Office",
    "office for national statistics": "Office for National Statistics",
    "ons": "Office for National Statistics",
    "charity commission": "Charity Commission",
    "attorney general's office": "Attorney General's Office",
    "prime minister's office": "Prime Minister's Office",
    "scottish government": "Scottish Government",
    "welsh government": "Welsh Government",
}

OFFICIAL_BODY_KIND_OVERRIDES = {
    "nhs england": "government_body",
    "driver and vehicle licensing agency": "government_body",
    "intellectual property office": "government_body",
    "office for national statistics": "government_body",
    "charity commission": "government_body",
    "attorney general's office": "government_body",
    "prime minister's office": "government_body",
    "welsh government": "government_body",
    "scottish government": "government_body",
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
    "exchequer": "HM Treasury",
    "levy": "HM Treasury",
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


def _contains_phrase(haystack, phrase):
    if not haystack or not phrase:
        return False
    escaped = re.escape(_normalise_label(phrase))
    return re.search(rf"(?<![a-z0-9]){escaped}(?![a-z0-9])", haystack) is not None


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


def is_known_political_party_name(name):
    canonical = canonicalise_political_party_name(name)
    return bool(canonical) and canonical in POLITICAL_PARTY_NAME_SET


def looks_like_official_body_name(name):
    lowered = _normalise_label(canonicalise_government_body_name(name))
    if not lowered:
        return False
    if lowered in PARLIAMENTARY_BODY_NAME_SET:
        return True
    if lowered in GOVERNMENT_DEPARTMENT_NAME_SET:
        return True
    if lowered in GOVERNMENT_BODY_MATCH_SET:
        return True
    if any(keyword in lowered for keyword in PARLIAMENTARY_BODY_KEYWORDS):
        return True
    if any(keyword in lowered for keyword in GOVERNMENT_DEPARTMENT_KEYWORDS):
        return True
    return False


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
    override = OFFICIAL_BODY_KIND_OVERRIDES.get(lowered)
    if override:
        return override
    if lowered in PARLIAMENTARY_BODY_NAME_SET:
        return "parliamentary_body"
    if lowered in GOVERNMENT_DEPARTMENT_NAME_SET:
        return "government_department"
    if any(keyword in lowered for keyword in PARLIAMENTARY_BODY_KEYWORDS):
        return "parliamentary_body"
    if any(keyword in lowered for keyword in GOVERNMENT_DEPARTMENT_KEYWORDS):
        return "government_department"
    return "government_body"


def official_body_alias_terms(name):
    canonical = canonicalise_government_body_name(name)
    lowered = _normalise_label(canonical)
    if not lowered:
        return set()

    aliases = {lowered}
    for alias, canonical_name in GOVERNMENT_BODY_ALIASES.items():
        if _normalise_label(canonical_name) == lowered:
            aliases.add(_normalise_label(alias))

    if lowered.startswith("department for "):
        aliases.add(lowered.replace("department for ", "", 1))
    elif lowered.startswith("department of "):
        aliases.add(lowered.replace("department of ", "", 1))
    elif lowered.startswith("ministry of "):
        aliases.add(lowered.replace("ministry of ", "", 1))

    return {alias for alias in aliases if alias}


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
        if _contains_phrase(haystack, name):
            matches.add(canonicalise_government_body_name(name))

    for alias, canonical in GOVERNMENT_BODY_ALIASES.items():
        if _contains_phrase(haystack, alias):
            matches.add(canonical)

    for role_phrase, department_name in MINISTER_ROLE_DEPARTMENT_MAP.items():
        if _contains_phrase(haystack, role_phrase):
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
