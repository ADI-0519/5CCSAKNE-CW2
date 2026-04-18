"""Central configuration for the CW2 KG construction pipeline.

The final project architecture is now centred on three core sources:
Guardian, Parliament/Hansard, and GOV.UK. A limited amount of NewsAPI
configuration is retained temporarily so the older collection code can still
run while we migrate the rest of the pipeline.
"""

import os
from datetime import datetime, timedelta, timezone
from urllib.parse import quote_plus

from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Project scope
# ---------------------------------------------------------------------------

_today = datetime.now(timezone.utc).date()
DATE_END = _today.strftime("%Y-%m-%d")
DATE_START = (_today - timedelta(days=30)).strftime("%Y-%m-%d")

PROJECT_SCOPE = (
    "UK parliamentary and government policy events reported in UK news, using "
    "Guardian as the core textual reporting source and Parliament/Hansard plus "
    "GOV.UK as structured or official sources, with OpenAI used critically for "
    "augmentation, extraction support, completion, and evaluation baselines."
)

# ---------------------------------------------------------------------------
# API keys and model configuration
# ---------------------------------------------------------------------------

GUARDIAN_API_KEY = os.getenv("GUARDIAN_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
PARLIAMENT_API_KEY = os.getenv("PARLIAMENT_API_KEY")
GOVUK_API_KEY = os.getenv("GOVUK_API_KEY")

# NewsAPI is retained only as a temporary migration path while the collection
# layer is moved over to the final three-source architecture.
NEWS_API_KEY = os.getenv("NEWS_API_KEY")

# ---------------------------------------------------------------------------
# Source endpoints
# ---------------------------------------------------------------------------

GUARDIAN_API_BASE = "https://content.guardianapis.com/search"
GOVUK_CONTENT_API_BASE = os.getenv("GOVUK_CONTENT_API_BASE", "https://www.gov.uk/api/content")
PARLIAMENT_API_BASE = os.getenv("PARLIAMENT_API_BASE", "https://api.parliament.uk")

# GOV.UK Content API is officially public and does not require authentication.
# Parliament endpoints are currently treated as public for this project too, but
# optional keys are exposed here so the pipeline can adapt cleanly if access
# requirements change or a different authenticated endpoint is adopted later.

# Legacy / migration-only endpoint.
NEWS_API_BASE = "https://newsapi.org/v2"

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

# ---------------------------------------------------------------------------
# Directory layout
# ---------------------------------------------------------------------------

RAW_DATA_DIR = "data/raw"
PROCESSED_DATA_DIR = "data/processed"
GENERATED_KG_DIR = "kg/generated"
OPENAI_CACHE_DIR = "data/cache/openai"

# ---------------------------------------------------------------------------
# Guardian configuration
# ---------------------------------------------------------------------------

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

# ---------------------------------------------------------------------------
# Parliament / Hansard configuration
# ---------------------------------------------------------------------------

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
PARLIAMENTARY_BODY_NAMES = [
    "House of Commons",
    "House of Lords",
    "Westminster Hall",
]

# ---------------------------------------------------------------------------
# GOV.UK configuration
# ---------------------------------------------------------------------------

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
    "guidance",
    "news_story",
    "press_release",
    "speech",
    "policy_paper",
    "consultation",
    "statutory_guidance",
]

# ---------------------------------------------------------------------------
# Legacy NewsAPI configuration (temporary migration support only)
# ---------------------------------------------------------------------------

NEWS_API_PAGE_SIZE = 100
NEWS_QUERY_TERMS = GUARDIAN_QUERY_TERMS

NEWSAPI_BLOCKED_SOURCES = {
    "Alltoc.com",
    "Behance.net",
    "Decider",
    "Electrek",
    "Football Italia",
    "Fox News",
    "Louder",
    "MacRumors",
    "OilPrice.com",
    "Page Six",
    "Pitchfork",
    "Radaronline.com",
    "Screen Rant",
    "Slashdot.org",
    "Techdirt",
    "The Next Web",
}

NEWSAPI_ALLOWED_SOURCES = {
    "BBC News",
    "Financial Times",
    "Reuters",
    "Sky News",
    "The Independent",
    "The Irish Times",
}

NEWSAPI_UK_SCOPE_TERMS = {
    "britain",
    "british",
    "england",
    "great britain",
    "house of commons",
    "house of lords",
    "labour",
    "liberal democrats",
    "london",
    "nhs",
    "no 10",
    "northern ireland",
    "parliament",
    "prime minister",
    "reform uk",
    "scotland",
    "scottish",
    "starmer",
    "treasury",
    "uk",
    "united kingdom",
    "wales",
    "westminster",
    "whitehall",
}

# ---------------------------------------------------------------------------
# Extraction dictionaries
# ---------------------------------------------------------------------------

TOPIC_KEYWORDS = [
    "parliament",
    "policy",
    "government",
    "debate",
    "statement",
    "budget",
    "tax",
    "taxation",
    "public spending",
    "economic policy",
    "immigration",
    "healthcare",
    "nhs",
    "education",
    "energy",
    "housing",
    "defence",
    "cost of living",
    "regulation",
]

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
    "Sinn Féin",
]

GOVERNMENT_BODY_NAMES = [
    "HM Treasury",
    "Treasury",
    "Home Office",
    "Cabinet Office",
    "Department of Health and Social Care",
    "Department for Education",
    "Department for Work and Pensions",
    "Ministry of Defence",
    "Foreign Office",
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


def build_query_string(terms):
    return " OR ".join(terms)


def build_guardian_url(page=None):
    section_filter = "|".join(GUARDIAN_SECTIONS)
    fields = ",".join(GUARDIAN_FIELDS)
    tag_filter = "|".join(GUARDIAN_TAGS)
    show_tags = ",".join(GUARDIAN_SHOW_TAGS)
    query = quote_plus(build_query_string(GUARDIAN_QUERY_TERMS))
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


def build_newsapi_everything_url(page=None):
    query = quote_plus(build_query_string(NEWS_QUERY_TERMS))
    base = (
        f"{NEWS_API_BASE}/everything?"
        f"q={query}&"
        f"language=en&"
        f"sortBy=publishedAt&"
        f"pageSize={NEWS_API_PAGE_SIZE}&"
        f"from={DATE_START}&"
        f"to={DATE_END}&"
    )
    if page is not None:
        base += f"page={page}&"
    return f"{base}apiKey={NEWS_API_KEY}"


def build_newsapi_page_url(page):
    return build_newsapi_everything_url(page=page)


CONFIG = {
    "project_scope": PROJECT_SCOPE,
    "date_start": DATE_START,
    "date_end": DATE_END,
    "GUARDIAN_API_KEY": GUARDIAN_API_KEY,
    "OPENAI_API_KEY": OPENAI_API_KEY,
    "OPENAI_MODEL": OPENAI_MODEL,
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
    "GUARDIAN_PAGE_SIZE": GUARDIAN_PAGE_SIZE,
    "GUARDIAN_SHOW_TAGS": GUARDIAN_SHOW_TAGS,
    "GUARDIAN_FIELDS": GUARDIAN_FIELDS,
    "GUARDIAN_SECTIONS": GUARDIAN_SECTIONS,
    "GUARDIAN_TAGS": GUARDIAN_TAGS,
    "GUARDIAN_QUERY_TERMS": GUARDIAN_QUERY_TERMS,
    "PARLIAMENT_QUERY_TERMS": PARLIAMENT_QUERY_TERMS,
    "PARLIAMENT_EVENT_KEYWORDS": PARLIAMENT_EVENT_KEYWORDS,
    "PARLIAMENTARY_BODY_NAMES": PARLIAMENTARY_BODY_NAMES,
    "GOVUK_QUERY_TERMS": GOVUK_QUERY_TERMS,
    "GOVUK_DOCUMENT_FORMATS": GOVUK_DOCUMENT_FORMATS,
    "NEWS_API_KEY": NEWS_API_KEY,
    "NEWS_API_BASE": NEWS_API_BASE,
    "NEWS_API_PAGE_SIZE": NEWS_API_PAGE_SIZE,
    "NEWS_QUERY_TERMS": NEWS_QUERY_TERMS,
    "NEWSAPI_BLOCKED_SOURCES": NEWSAPI_BLOCKED_SOURCES,
    "NEWSAPI_ALLOWED_SOURCES": NEWSAPI_ALLOWED_SOURCES,
    "NEWSAPI_UK_SCOPE_TERMS": NEWSAPI_UK_SCOPE_TERMS,
    "TOPIC_KEYWORDS": TOPIC_KEYWORDS,
    "POLITICIAN_NAMES": POLITICIAN_NAMES,
    "POLITICAL_PARTY_NAMES": POLITICAL_PARTY_NAMES,
    "GOVERNMENT_BODY_NAMES": GOVERNMENT_BODY_NAMES,
    "UK_LOCATION_NAMES": UK_LOCATION_NAMES,
    "TOPIC_GROUPS": TOPIC_GROUPS,
    "POLITICAL_EVENT_HINTS": POLITICAL_EVENT_HINTS,
    "ECONOMIC_EVENT_HINTS": ECONOMIC_EVENT_HINTS,
    "OPINION_SECTION_NAMES": OPINION_SECTION_NAMES,
    "BREAKING_NEWS_HINTS": BREAKING_NEWS_HINTS,
    "POSITIVE_SENTIMENT_TERMS": POSITIVE_SENTIMENT_TERMS,
    "NEGATIVE_SENTIMENT_TERMS": NEGATIVE_SENTIMENT_TERMS,
    "CONTROLLED_PREDICATES": CONTROLLED_PREDICATES,
    "ENTITY_STOPLIST": ENTITY_STOPLIST,
    "PERSON_STOPLIST": PERSON_STOPLIST,
    "url_guardian": build_guardian_url(),
    "url_newsapi_everything": build_newsapi_everything_url(),
}

# Backwards-compatible alias used by the current prototype pipeline.
CONFIG["url_headlines"] = CONFIG["url_newsapi_everything"]
