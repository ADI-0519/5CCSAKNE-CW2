import os
from urllib.parse import quote_plus

from dotenv import load_dotenv

load_dotenv()

# project scope

DATE_START = "2026-03-06"
DATE_END = "2026-04-06"
DATE_WINDOW = {"start": DATE_START, "end": DATE_END}

PROJECT_SCOPE = (
    "UK parliamentary and government policy events reported in UK news, using "
    "Guardian as the core textual reporting source and Parliament/Hansard plus "
    "GOV.UK as structured or official sources, with OpenAI used critically for "
    "augmentation, extraction support, completion, and evaluation baselines."
)

# API keys and model config

GUARDIAN_API_KEY = os.getenv("GUARDIAN_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
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

# Guardian configuration

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

# Parliament / Hansard configuration

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

# GOV.UK configuration

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

# extraction dictionaries

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


CONFIG = {
    "project_scope": PROJECT_SCOPE,
    "date_start": DATE_START,
    "date_end": DATE_END,
    "date_window": DATE_WINDOW,
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
}
