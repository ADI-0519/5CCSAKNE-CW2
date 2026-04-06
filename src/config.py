import os
from urllib.parse import quote_plus

from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Project scope
# ---------------------------------------------------------------------------

PROJECT_SCOPE = (
    "Current UK politics and policy news from March 6, 2026 to April 6, 2026, "
    "collected from GuardianAPI and NewsAPI, with OpenAI used for extraction, "
    "classification, and completion."
)

DATE_START = "2026-03-06"
DATE_END = "2026-04-06"

# ---------------------------------------------------------------------------
# Source configuration
# ---------------------------------------------------------------------------

NEWS_API_KEY = os.getenv("NEWS_API_KEY")
GUARDIAN_API_KEY = os.getenv("GUARDIAN_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

NEWS_API_BASE = "https://newsapi.org/v2"
GUARDIAN_API_BASE = "https://content.guardianapis.com/search"
NEWS_API_PAGE_SIZE = 100
GUARDIAN_PAGE_SIZE = 200
GUARDIAN_SHOW_TAGS = ["keyword", "tone", "contributor"]

RAW_DATA_DIR = "data/raw"
PROCESSED_DATA_DIR = "data/processed"
GENERATED_KG_DIR = "kg/generated"

NEWS_QUERY_TERMS = [
    "UK politics",
    "UK government",
    "Parliament",
    "Labour",
    "Conservative",
    "Liberal Democrats",
    "Home Office",
    "Treasury",
    "budget",
    "tax",
    "public spending",
    "immigration",
    "NHS",
    "policy",
]

GUARDIAN_SECTIONS = ["politics", "uk-news", "commentisfree"]
GUARDIAN_TAGS = [
    "politics/politics",
    "politics/uk",
    "business/economics",
    "society/health",
]

GUARDIAN_FIELDS = [
    "headline",
    "trailText",
    "bodyText",
    "byline",
    "lastModified",
    "wordcount",
]

# ---------------------------------------------------------------------------
# Extraction dictionaries
# ---------------------------------------------------------------------------

# Kept for backwards compatibility with the current prototype extraction code.
# The current branch still uses a technology-oriented extractor in places, even
# though the final project focus is UK politics and policy news.
TECHNOLOGY_KEYWORDS = [
    "AI",
    "Artificial Intelligence",
    "Machine Learning",
    "Deep Learning",
    "Automation",
    "Large Language Model",
    "LLM",
    "Generative AI",
    "GPT",
]

TOPIC_KEYWORDS = [
    "politics",
    "policy",
    "government",
    "parliament",
    "election",
    "leadership",
    "budget",
    "tax",
    "taxation",
    "public spending",
    "economy",
    "economic policy",
    "immigration",
    "healthcare",
    "nhs",
    "education",
    "energy",
    "defense",
    "housing",
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
    "Election": ["election", "ballot", "campaign", "polling"],
    "Parliament": ["parliament", "commons", "lords", "mp", "mps"],
    "Leadership": ["leadership", "cabinet reshuffle", "party leader"],
    "Government Policy": ["policy", "bill", "legislation", "proposal", "white paper"],
}

POLITICAL_EVENT_HINTS = [
    "election",
    "leadership contest",
    "parliamentary vote",
    "commons vote",
    "lords vote",
    "policy announcement",
    "cabinet reshuffle",
    "bill debate",
    "spring statement",
]

ECONOMIC_EVENT_HINTS = [
    "budget",
    "spring statement",
    "autumn statement",
    "spending review",
    "fiscal statement",
    "interest rate decision",
]

POSITIVE_SENTIMENT_TERMS = [
    "boost",
    "success",
    "welcome",
    "improve",
    "growth",
    "progress",
    "confidence",
    "backing",
]

NEGATIVE_SENTIMENT_TERMS = [
    "crisis",
    "criticised",
    "criticized",
    "concern",
    "failure",
    "backlash",
    "warning",
    "decline",
    "pressure",
    "row",
]

OPINION_SECTION_NAMES = {"comment is free", "opinion", "comment"}
BREAKING_NEWS_HINTS = ["breaking", "live", "updates", "developing", "just in"]

CONTROLLED_PREDICATES = {
    "mentions",
    "located_in",
    "authored_by",
    "published_by",
    "involved_in",
}

ENTITY_STOPLIST = {
    "The",
    "This",
    "That",
    "These",
    "Those",
    "It",
    "Its",
    "He",
    "She",
    "They",
    "We",
    "You",
    "I",
    "Me",
    "Us",
    "Them",
    "New",
    "More",
    "Most",
    "First",
    "Last",
    "Next",
    "Other",
    "Some",
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
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


def build_news_query_string():
    return " OR ".join(NEWS_QUERY_TERMS)


def build_newsapi_everything_url():
    query = quote_plus(build_news_query_string())
    return (
        f"{NEWS_API_BASE}/everything?"
        f"q={query}&"
        f"language=en&"
        f"sortBy=publishedAt&"
        f"pageSize={NEWS_API_PAGE_SIZE}&"
        f"from={DATE_START}&"
        f"to={DATE_END}&"
        f"apiKey={NEWS_API_KEY}"
    )


def build_newsapi_page_url(page):
    query = quote_plus(build_news_query_string())
    return (
        f"{NEWS_API_BASE}/everything?"
        f"q={query}&"
        f"language=en&"
        f"sortBy=publishedAt&"
        f"pageSize={NEWS_API_PAGE_SIZE}&"
        f"page={page}&"
        f"from={DATE_START}&"
        f"to={DATE_END}&"
        f"apiKey={NEWS_API_KEY}"
    )


def build_guardian_url():
    section_filter = "|".join(GUARDIAN_SECTIONS)
    fields = ",".join(GUARDIAN_FIELDS)
    tag_filter = "|".join(GUARDIAN_TAGS)
    show_tags = ",".join(GUARDIAN_SHOW_TAGS)
    query = quote_plus(build_news_query_string())
    return (
        f"{GUARDIAN_API_BASE}?"
        f"q={query}&"
        f"from-date={DATE_START}&"
        f"to-date={DATE_END}&"
        f"section={section_filter}&"
        f"tag={tag_filter}&"
        f"show-fields={fields}&"
        f"show-tags={show_tags}&"
        f"page-size={GUARDIAN_PAGE_SIZE}&"
        f"api-key={GUARDIAN_API_KEY}"
    )


def build_guardian_page_url(page):
    section_filter = "|".join(GUARDIAN_SECTIONS)
    fields = ",".join(GUARDIAN_FIELDS)
    tag_filter = "|".join(GUARDIAN_TAGS)
    show_tags = ",".join(GUARDIAN_SHOW_TAGS)
    query = quote_plus(build_news_query_string())
    return (
        f"{GUARDIAN_API_BASE}?"
        f"q={query}&"
        f"from-date={DATE_START}&"
        f"to-date={DATE_END}&"
        f"section={section_filter}&"
        f"tag={tag_filter}&"
        f"show-fields={fields}&"
        f"show-tags={show_tags}&"
        f"page-size={GUARDIAN_PAGE_SIZE}&"
        f"page={page}&"
        f"api-key={GUARDIAN_API_KEY}"
    )


CONFIG = {
    "project_scope": PROJECT_SCOPE,
    "date_start": DATE_START,
    "date_end": DATE_END,
    "NEWS_API_KEY": NEWS_API_KEY,
    "GUARDIAN_API_KEY": GUARDIAN_API_KEY,
    "OPENAI_API_KEY": OPENAI_API_KEY,
    "NEWS_API_BASE": NEWS_API_BASE,
    "GUARDIAN_API_BASE": GUARDIAN_API_BASE,
    "NEWS_API_PAGE_SIZE": NEWS_API_PAGE_SIZE,
    "GUARDIAN_PAGE_SIZE": GUARDIAN_PAGE_SIZE,
    "GUARDIAN_SHOW_TAGS": GUARDIAN_SHOW_TAGS,
    "RAW_DATA_DIR": RAW_DATA_DIR,
    "PROCESSED_DATA_DIR": PROCESSED_DATA_DIR,
    "GENERATED_KG_DIR": GENERATED_KG_DIR,
    "NEWS_QUERY_TERMS": NEWS_QUERY_TERMS,
    "GUARDIAN_SECTIONS": GUARDIAN_SECTIONS,
    "GUARDIAN_TAGS": GUARDIAN_TAGS,
    "GUARDIAN_FIELDS": GUARDIAN_FIELDS,
    "TECHNOLOGY_KEYWORDS": TECHNOLOGY_KEYWORDS,
    "TOPIC_KEYWORDS": TOPIC_KEYWORDS,
    "POLITICIAN_NAMES": POLITICIAN_NAMES,
    "POLITICAL_PARTY_NAMES": POLITICAL_PARTY_NAMES,
    "GOVERNMENT_BODY_NAMES": GOVERNMENT_BODY_NAMES,
    "UK_LOCATION_NAMES": UK_LOCATION_NAMES,
    "TOPIC_GROUPS": TOPIC_GROUPS,
    "POLITICAL_EVENT_HINTS": POLITICAL_EVENT_HINTS,
    "ECONOMIC_EVENT_HINTS": ECONOMIC_EVENT_HINTS,
    "POSITIVE_SENTIMENT_TERMS": POSITIVE_SENTIMENT_TERMS,
    "NEGATIVE_SENTIMENT_TERMS": NEGATIVE_SENTIMENT_TERMS,
    "OPINION_SECTION_NAMES": OPINION_SECTION_NAMES,
    "BREAKING_NEWS_HINTS": BREAKING_NEWS_HINTS,
    "CONTROLLED_PREDICATES": CONTROLLED_PREDICATES,
    "ENTITY_STOPLIST": ENTITY_STOPLIST,
    "PERSON_STOPLIST": PERSON_STOPLIST,
    "url_newsapi_everything": build_newsapi_everything_url(),
    "url_guardian": build_guardian_url(),
}

# Backwards-compatible alias used by the current prototype pipeline.
CONFIG["url_headlines"] = CONFIG["url_newsapi_everything"]
