import os
from urllib.parse import quote_plus

from dotenv import load_dotenv

from src.domain_knowledge import (
    GOVERNMENT_BODY_NAMES as DK_GOVERNMENT_BODY_NAMES,
)
from src.domain_knowledge import (
    GOVERNMENT_DEPARTMENT_KEYWORDS,
    GOVERNMENT_DEPARTMENT_NAMES,
    PARLIAMENTARY_BODY_KEYWORDS,
    PARLIAMENTARY_BODY_NAMES,
)
from src.domain_knowledge import (
    POLITICAL_PARTY_NAMES as DK_POLITICAL_PARTY_NAMES,
)
from src.domain_knowledge import (
    POLITICIAN_NAMES as DK_POLITICIAN_NAMES,
)
from src.domain_knowledge import (
    TOPIC_GROUPS as DK_TOPIC_GROUPS,
)
from src.domain_knowledge import (
    UK_LOCATION_NAMES as DK_UK_LOCATION_NAMES,
)

load_dotenv()

# project scope

DATE_START = "2026-03-06"
DATE_END = "2026-04-06"
DATE_WINDOW = {"start": DATE_START, "end": DATE_END}

PROJECT_SCOPE = (
    "UK parliamentary and government policy events reported in UK news, using "
    "Guardian as the core textual reporting source and Parliament/Hansard plus "
    "GOV.UK as structured or official sources, with OpenAI used critically for "
    "augmentation, extraction support, and evaluation baselines."
)

# API keys and model config

GUARDIAN_API_KEY = os.getenv("GUARDIAN_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_REQUEST_TIMEOUT_SECONDS = int(os.getenv("OPENAI_REQUEST_TIMEOUT_SECONDS", "30"))
ENABLE_SPACY_NER = os.getenv("ENABLE_SPACY_NER", "1") == "1"
SPACY_MODEL_NAME = os.getenv("SPACY_MODEL_NAME", "en_core_web_sm")
PARLIAMENT_API_KEY = os.getenv("PARLIAMENT_API_KEY")
GOVUK_API_KEY = os.getenv("GOVUK_API_KEY")

# source endpoints

GUARDIAN_API_BASE = "https://content.guardianapis.com/search"
GOVUK_CONTENT_API_BASE = os.getenv("GOVUK_CONTENT_API_BASE", "https://www.gov.uk/api/content")
PARLIAMENT_API_BASE = os.getenv(
    "PARLIAMENT_API_BASE", "https://questions-statements-api.parliament.uk"
)

SOURCE_CONFIG = {
    "guardian": {
        "kind": "textual",
        "role": "news reporting source",
        "base_url": GUARDIAN_API_BASE,
        "requires_api_key": True,
        "api_key_env": "GUARDIAN_API_KEY",
    },
    "parliament": {
        "kind": "structured",
        "role": "parliamentary backbone source",
        "base_url": PARLIAMENT_API_BASE,
        "requires_api_key": False,
        "api_key_env": None,
    },
    "govuk": {
        "kind": "structured",
        "role": "official government policy source",
        "base_url": GOVUK_CONTENT_API_BASE,
        "requires_api_key": False,
        "api_key_env": None,
    },
}

CORE_SOURCE_ORDER = ["guardian", "parliament", "govuk"]
TEXTUAL_SOURCE_SYSTEMS = {"guardian"}
STRUCTURED_SOURCE_SYSTEMS = {"parliament", "govuk"}
OFFICIAL_SOURCE_SYSTEMS = {"parliament", "hansard", "govuk", "gov.uk"}

# directory layout

RAW_DATA_DIR = "data/raw"
PROCESSED_DATA_DIR = "data/processed"
GENERATED_KG_DIR = "kg/generated"
OPENAI_CACHE_DIR = "data/cache/openai"
EXTRACTION_PROGRESS_EVERY = 25

NLP_CONFIG = {
    "enable_spacy_ner": ENABLE_SPACY_NER,
    "spacy_model_name": SPACY_MODEL_NAME,
}

# Guardian retrieval

GUARDIAN_PAGE_SIZE = 200
GUARDIAN_SHOW_TAGS = ["keyword", "tone", "contributor"]
GUARDIAN_FIELDS = [
    "headline",
    "trailText",
    "bodyText",
    "byline",
    "lastModified",
    "wordcount",
]
GUARDIAN_SECTIONS = ["politics", "uk-news", "commentisfree"]
GUARDIAN_TAGS = [
    "politics/politics",
    "politics/uk",
    "politics/conservatives",
    "politics/labour",
    "business/economics",
    "society/health",
]
GUARDIAN_QUERY_TERMS = [
    "UK parliament",
    "House of Commons",
    "House of Lords",
    "ministerial statement",
    "government policy",
    "policy reform",
    "Treasury",
    "Home Office",
    "budget",
    "taxation",
    "public spending",
    "immigration",
    "NHS",
]

# Parliament / Hansard retrieval

PARLIAMENT_QUERY_TERMS = [
    "debate",
    "statement",
    "bill",
    "ministerial",
    "committee",
    "budget",
    "tax",
    "spending",
    "immigration",
    "health",
]
PARLIAMENT_EVENT_KEYWORDS = [
    "debate",
    "question",
    "statement",
    "committee",
    "bill",
    "reading",
]

# GOV.UK retrieval and filtering

GOVUK_QUERY_TERMS = [
    "policy",
    "statement",
    "guidance",
    "announcement",
    "consultation",
    "budget",
    "tax",
    "public spending",
    "immigration",
    "healthcare",
]
GOVUK_DOCUMENT_FORMATS = [
    "press_release",
    "speech",
    "policy_paper",
    "consultation",
]
GOVUK_ALWAYS_INCLUDE_FORMATS = {
    "consultation",
}
GOVUK_SCOPE_SIGNAL_TERMS = {
    "budget",
    "defence",
    "education",
    "energy",
    "health",
    "healthcare",
    "home office",
    "housing",
    "immigration",
    "ministerial",
    "nhs",
    "parliament",
    "public spending",
    "reform",
    "statement",
    "tax",
    "treasury",
    "transport",
    "welfare",
}
GOVUK_EXCLUDED_TEXT_TERMS = {
    "annual report",
    "appointments to",
    "code of practice",
    "data strategy",
    "extension notice",
    "form ",
    "helpsheet",
    "manual",
    "minutes",
    "privacy policy",
    "rates and allowances",
    "report:",
    "self assessment",
    "small and medium-sized enterprise",
    "terms of reference",
}

# canonical domain lexicons

POLITICIAN_NAMES = list(DK_POLITICIAN_NAMES)
POLITICAL_PARTY_NAMES = list(DK_POLITICAL_PARTY_NAMES)
GOVERNMENT_BODY_NAMES = list(DK_GOVERNMENT_BODY_NAMES)
UK_LOCATION_NAMES = list(DK_UK_LOCATION_NAMES)
TOPIC_GROUPS = dict(DK_TOPIC_GROUPS)
TOPIC_KEYWORDS = sorted({hint for hints in TOPIC_GROUPS.values() for hint in hints})

# extraction heuristics

POLITICAL_EVENT_HINTS = [
    "ministerial statement",
    "parliamentary debate",
    "commons debate",
    "lords debate",
    "policy announcement",
    "committee session",
    "bill debate",
    "general election",
    "local election",
    "by-election",
]

ECONOMIC_EVENT_HINTS = [
    "spring budget",
    "autumn budget",
    "spring statement",
    "autumn statement",
    "spending review",
    "fiscal statement",
]

OPINION_SECTION_NAMES = {
    "comment is free",
    "opinion",
}

BREAKING_NEWS_HINTS = {
    "live",
    "breaking",
    "as it happened",
    "rolling coverage",
    "updates",
}

GOVUK_EVENT_FALLBACK_SECTIONS = {
    "press_release",
    "speech",
}

GOVUK_EXPLICIT_EVENT_SIGNAL_TERMS = {
    "agreement",
    "announcement",
    "consultation",
    "crackdown",
    "declaration",
    "funding",
    "investment",
    "launch",
    "policy",
    "reform",
    "response",
    "rules",
    "speech",
    "statement",
    "summit",
    "vision",
}

GOVUK_NON_EVENT_SECTIONS = {
    "person",
    "form",
    "employment_tribunal_decision",
    "travel_advice",
    "complaints_procedure",
    "mainstream_browse_page",
    "hmrc_manual_section",
    "armed_forces_covenant_business",
    "policy_group",
}

POSITIVE_SENTIMENT_TERMS = {
    "boost",
    "progress",
    "welcomed",
    "welcome",
    "improvement",
    "improved",
    "success",
    "positive",
    "support",
}

NEGATIVE_SENTIMENT_TERMS = {
    "backlash",
    "criticism",
    "criticised",
    "criticized",
    "concern",
    "concerns",
    "pressure",
    "row",
    "crisis",
    "negative",
}

CONTROLLED_PREDICATES = {
    "mentions",
    "located_in",
    "authored_by",
    "published_by",
    "involved_in",
}

ENTITY_STOPLIST = {
    "April",
    "Britain",
    "February",
    "It",
    "Its",
    "January",
    "June",
    "Last",
    "Monday",
    "More",
    "Most",
    "First",
    "Next",
    "Other",
    "Some",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
    "March",
    "May",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
    "United Kingdom",
    "Great Britain",
}

PERSON_STOPLIST = {
    "United Kingdom",
    "Prime Minister",
    "Labour Party",
    "Conservative Party",
    "House Commons",
    "House Lords",
    "Downing Street",
    "Cabinet Office",
    "New Labour",
    "Northern Ireland",
    "Westminster Abbey",
}

EXTRACTION_ORG_BLOCKED_PREFIXES = {
    "Analysis",
    "Comment",
    "Commentary",
    "Opinion",
    "Politics",
    "Reports",
}

EXTRACTION_ORG_NOISE_TERMS = {
    "Letters",
    "News",
    "Opinion",
    "Politics",
    "Review",
}

EXTRACTION_LOCATION_BLOCKLIST = {
    "Badenoch",
    "British",
    "Britons",
    "Cameo",
    "CenTax",
    "Common",
    "Conservatives",
    "Farage",
    "Kemi",
    "Labour MPs",
    "Muslims",
    "Nige",
    "Offord",
    "PMQs",
    "Rayner",
    "Reform",
    "Tories",
    "UK The",
}

EXTRACTION_LOCATION_STOPWORDS = {
    "A",
    "My",
    "An",
    "The",
}

EXTRACTION_LOCATION_ROLE_TERMS = {
    "Budget",
    "Minister",
    "Ministers",
    "MP",
    "MPs",
    "MSP",
    "MSPs",
    "Party",
    "Parties",
    "Policy",
    "Policies",
    "Questions",
}

EXTRACTION_PERSON_BLOCKED_PREFIXES = {
    "House",
    "Last",
    "Lords",
    "Middle",
    "News",
    "Reports",
}

EXTRACTION_BROAD_EVENT_LOCATIONS = {
    "England",
    "Europe",
    "Iran",
    "Northern Ireland",
    "Scotland",
    "UK",
    "United Kingdom",
    "Wales",
}

EXTRACTION_ELECTION_SIGNAL_PHRASES = {
    "byelection",
    "by-election",
    "election campaign",
    "election candidate",
    "elections",
    "general election",
    "local election",
    "may elections",
    "mayoral election",
}

EXTRACTION_POLICY_ANNOUNCEMENT_SIGNAL_PHRASES = {
    "announcement",
    "announced",
    "consultation",
    "guidance",
    "ministerial statement",
    "plan",
    "plans",
    "policy paper",
    "proposal",
    "proposed",
    "set out",
    "speech",
    "statement",
    "unveiled",
}

# grouped config interfaces

RETRIEVAL_CONFIG = {
    "guardian_query_terms": GUARDIAN_QUERY_TERMS,
    "parliament_query_terms": PARLIAMENT_QUERY_TERMS,
    "govuk_query_terms": GOVUK_QUERY_TERMS,
    "govuk_document_formats": GOVUK_DOCUMENT_FORMATS,
}

CANONICAL_LEXICONS = {
    "politician_names": POLITICIAN_NAMES,
    "political_party_names": POLITICAL_PARTY_NAMES,
    "government_body_names": GOVERNMENT_BODY_NAMES,
    "parliamentary_body_names": list(PARLIAMENTARY_BODY_NAMES),
    "uk_location_names": UK_LOCATION_NAMES,
    "topic_groups": TOPIC_GROUPS,
}

BODY_CLASSIFICATION_RULES = {
    "government_department_names": list(GOVERNMENT_DEPARTMENT_NAMES),
    "government_department_keywords": sorted(GOVERNMENT_DEPARTMENT_KEYWORDS),
    "parliamentary_body_keywords": sorted(PARLIAMENTARY_BODY_KEYWORDS),
}

FILTER_RULES = {
    "govuk_scope_signal_terms": GOVUK_SCOPE_SIGNAL_TERMS,
    "govuk_excluded_text_terms": GOVUK_EXCLUDED_TEXT_TERMS,
    "opinion_section_names": OPINION_SECTION_NAMES,
    "breaking_news_hints": BREAKING_NEWS_HINTS,
    "govuk_non_event_sections": GOVUK_NON_EVENT_SECTIONS,
}


def build_query_string(terms):
    return " OR ".join(terms)


def build_guardian_url(page=None):
    section_filter = "|".join(GUARDIAN_SECTIONS)
    fields = ",".join(GUARDIAN_FIELDS)
    tag_filter = "|".join(GUARDIAN_TAGS)
    show_tags = ",".join(GUARDIAN_SHOW_TAGS)
    query = quote_plus(build_query_string(RETRIEVAL_CONFIG["guardian_query_terms"]))
    base = (
        f"{GUARDIAN_API_BASE}?"
        f"q={query}&"
        f"from-date={DATE_START}&"
        f"to-date={DATE_END}&"
        f"section={section_filter}&"
        f"tag={tag_filter}&"
        f"show-fields={fields}&"
        f"show-tags={show_tags}&"
        f"page-size={GUARDIAN_PAGE_SIZE}&"
    )
    if page is not None:
        base += f"page={page}&"
    return f"{base}api-key={GUARDIAN_API_KEY}"


def build_guardian_page_url(page):
    return build_guardian_url(page=page)


CONFIG = {
    "project_scope": PROJECT_SCOPE,
    "date_start": DATE_START,
    "date_end": DATE_END,
    "date_window": DATE_WINDOW,
    "GUARDIAN_API_KEY": GUARDIAN_API_KEY,
    "OPENAI_API_KEY": OPENAI_API_KEY,
    "OPENAI_MODEL": OPENAI_MODEL,
    "OPENAI_REQUEST_TIMEOUT_SECONDS": OPENAI_REQUEST_TIMEOUT_SECONDS,
    "ENABLE_SPACY_NER": ENABLE_SPACY_NER,
    "SPACY_MODEL_NAME": SPACY_MODEL_NAME,
    "PARLIAMENT_API_KEY": PARLIAMENT_API_KEY,
    "GOVUK_API_KEY": GOVUK_API_KEY,
    "SOURCE_CONFIG": SOURCE_CONFIG,
    "CORE_SOURCE_ORDER": CORE_SOURCE_ORDER,
    "TEXTUAL_SOURCE_SYSTEMS": TEXTUAL_SOURCE_SYSTEMS,
    "STRUCTURED_SOURCE_SYSTEMS": STRUCTURED_SOURCE_SYSTEMS,
    "OFFICIAL_SOURCE_SYSTEMS": OFFICIAL_SOURCE_SYSTEMS,
    "GUARDIAN_API_BASE": GUARDIAN_API_BASE,
    "GOVUK_CONTENT_API_BASE": GOVUK_CONTENT_API_BASE,
    "PARLIAMENT_API_BASE": PARLIAMENT_API_BASE,
    "RAW_DATA_DIR": RAW_DATA_DIR,
    "PROCESSED_DATA_DIR": PROCESSED_DATA_DIR,
    "GENERATED_KG_DIR": GENERATED_KG_DIR,
    "OPENAI_CACHE_DIR": OPENAI_CACHE_DIR,
    "EXTRACTION_PROGRESS_EVERY": EXTRACTION_PROGRESS_EVERY,
    "NLP_CONFIG": NLP_CONFIG,
    "GUARDIAN_PAGE_SIZE": GUARDIAN_PAGE_SIZE,
    "GUARDIAN_SHOW_TAGS": GUARDIAN_SHOW_TAGS,
    "GUARDIAN_FIELDS": GUARDIAN_FIELDS,
    "GUARDIAN_SECTIONS": GUARDIAN_SECTIONS,
    "GUARDIAN_TAGS": GUARDIAN_TAGS,
    "GUARDIAN_QUERY_TERMS": RETRIEVAL_CONFIG["guardian_query_terms"],
    "PARLIAMENT_QUERY_TERMS": RETRIEVAL_CONFIG["parliament_query_terms"],
    "PARLIAMENT_EVENT_KEYWORDS": PARLIAMENT_EVENT_KEYWORDS,
    "PARLIAMENTARY_BODY_NAMES": CANONICAL_LEXICONS["parliamentary_body_names"],
    "GOVUK_QUERY_TERMS": RETRIEVAL_CONFIG["govuk_query_terms"],
    "GOVUK_DOCUMENT_FORMATS": RETRIEVAL_CONFIG["govuk_document_formats"],
    "GOVUK_ALWAYS_INCLUDE_FORMATS": GOVUK_ALWAYS_INCLUDE_FORMATS,
    "GOVUK_SCOPE_SIGNAL_TERMS": FILTER_RULES["govuk_scope_signal_terms"],
    "GOVUK_EXCLUDED_TEXT_TERMS": FILTER_RULES["govuk_excluded_text_terms"],
    "RETRIEVAL_CONFIG": RETRIEVAL_CONFIG,
    "CANONICAL_LEXICONS": CANONICAL_LEXICONS,
    "BODY_CLASSIFICATION_RULES": BODY_CLASSIFICATION_RULES,
    "FILTER_RULES": FILTER_RULES,
    "TOPIC_KEYWORDS": TOPIC_KEYWORDS,
    "POLITICIAN_NAMES": CANONICAL_LEXICONS["politician_names"],
    "POLITICAL_PARTY_NAMES": CANONICAL_LEXICONS["political_party_names"],
    "GOVERNMENT_BODY_NAMES": CANONICAL_LEXICONS["government_body_names"],
    "UK_LOCATION_NAMES": CANONICAL_LEXICONS["uk_location_names"],
    "TOPIC_GROUPS": CANONICAL_LEXICONS["topic_groups"],
    "POLITICAL_EVENT_HINTS": POLITICAL_EVENT_HINTS,
    "ECONOMIC_EVENT_HINTS": ECONOMIC_EVENT_HINTS,
    "OPINION_SECTION_NAMES": FILTER_RULES["opinion_section_names"],
    "BREAKING_NEWS_HINTS": FILTER_RULES["breaking_news_hints"],
    "GOVUK_EVENT_FALLBACK_SECTIONS": GOVUK_EVENT_FALLBACK_SECTIONS,
    "GOVUK_EXPLICIT_EVENT_SIGNAL_TERMS": GOVUK_EXPLICIT_EVENT_SIGNAL_TERMS,
    "GOVUK_NON_EVENT_SECTIONS": FILTER_RULES["govuk_non_event_sections"],
    "POSITIVE_SENTIMENT_TERMS": POSITIVE_SENTIMENT_TERMS,
    "NEGATIVE_SENTIMENT_TERMS": NEGATIVE_SENTIMENT_TERMS,
    "CONTROLLED_PREDICATES": CONTROLLED_PREDICATES,
    "ENTITY_STOPLIST": ENTITY_STOPLIST,
    "PERSON_STOPLIST": PERSON_STOPLIST,
    "EXTRACTION_ORG_BLOCKED_PREFIXES": EXTRACTION_ORG_BLOCKED_PREFIXES,
    "EXTRACTION_ORG_NOISE_TERMS": EXTRACTION_ORG_NOISE_TERMS,
    "EXTRACTION_LOCATION_BLOCKLIST": EXTRACTION_LOCATION_BLOCKLIST,
    "EXTRACTION_LOCATION_STOPWORDS": EXTRACTION_LOCATION_STOPWORDS,
    "EXTRACTION_LOCATION_ROLE_TERMS": EXTRACTION_LOCATION_ROLE_TERMS,
    "EXTRACTION_PERSON_BLOCKED_PREFIXES": EXTRACTION_PERSON_BLOCKED_PREFIXES,
    "EXTRACTION_BROAD_EVENT_LOCATIONS": EXTRACTION_BROAD_EVENT_LOCATIONS,
    "EXTRACTION_ELECTION_SIGNAL_PHRASES": EXTRACTION_ELECTION_SIGNAL_PHRASES,
    "EXTRACTION_POLICY_ANNOUNCEMENT_SIGNAL_PHRASES": EXTRACTION_POLICY_ANNOUNCEMENT_SIGNAL_PHRASES,
    "url_guardian": build_guardian_url(),
}
