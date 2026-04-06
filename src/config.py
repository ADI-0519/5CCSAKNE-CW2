import os

from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Fixed coursework scope
# ---------------------------------------------------------------------------

FIXED_SCOPE = (
    "A knowledge graph for current UK politics and policy news, using articles "
    "published between March 1, 2026 and April 6, 2026 from GuardianAPI and "
    "NewsAPI, with OpenAI used for extraction, classification, and completion."
)

DATE_WINDOW_START = "2026-03-01"
DATE_WINDOW_END = "2026-04-06"

UK_POLITICS_QUERY = (
    '"UK government" OR Westminster OR Parliament OR Labour OR Conservative '
    'OR budget OR regulation OR policy OR minister OR "public affairs"'
)

POLITICAL_PERSON_TITLES = {
    "chancellor",
    "councillor",
    "deputy prime minister",
    "foreign secretary",
    "home secretary",
    "lord",
    "mayor",
    "minister",
    "mp",
    "prime minister",
    "secretary",
    "shadow chancellor",
    "shadow minister",
    "sir",
}

POLITICAL_PARTIES = {
    "Conservative Party",
    "Green Party",
    "Labour Party",
    "Liberal Democrats",
    "Plaid Cymru",
    "Reform UK",
    "Scottish National Party",
}

GOVERNMENT_BODIES = {
    "Cabinet Office",
    "Department for Education",
    "Department for Transport",
    "HM Treasury",
    "House of Commons",
    "House of Lords",
    "No 10",
    "Parliament",
    "UK Government",
    "Westminster",
}

TECHNOLOGY_KEYWORDS = [
    "AI",
    "Artificial Intelligence",
    "Machine Learning",
    "Deep Learning",
    "Neural Network",
    "Natural Language Processing",
    "NLP",
    "Computer Vision",
    "Robotics",
    "Automation",
    "Cloud Computing",
    "Blockchain",
    "Cryptocurrency",
    "Bitcoin",
    "Ethereum",
    "Quantum Computing",
    "Cybersecurity",
    "Data Science",
    "Big Data",
    "Internet of Things",
    "IoT",
    "5G",
    "Augmented Reality",
    "Virtual Reality",
    "Mixed Reality",
    "Edge Computing",
    "Kubernetes",
    "Docker",
    "Microservices",
    "Large Language Model",
    "LLM",
    "Generative AI",
    "GPT",
    "ChatGPT",
    "Transformer",
    "BERT",
    "Diffusion Model",
    "Autonomous Vehicle",
    "Self-Driving",
    "Semiconductor",
    "GPU",
    "TPU",
]

TOPIC_KEYWORDS = [
    "budget",
    "climate",
    "economy",
    "education",
    "election",
    "energy",
    "finance",
    "funding",
    "government",
    "healthcare",
    "housing",
    "innovation",
    "investment",
    "migration",
    "parliament",
    "policy",
    "politics",
    "public services",
    "regulation",
    "research",
    "security",
    "tax",
    "transport",
    "welfare",
]

CONTROLLED_PREDICATES = {
    "mentions",
    "developed_by",
    "announced",
    "located_in",
    "authored_by",
    "published_by",
    "uses_technology",
    "involved_in",
    "part_of",
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
    "New",
    "North America",
    "Other",
    "Prime Minister",
    "Saturday",
    "September",
    "Some",
    "South America",
    "Sunday",
    "The",
    "Those",
    "Tuesday",
    "This",
    "Thursday",
    "United States",
    "UK",
    "United Kingdom",
    "Wednesday",
    "Westminster",
}

PERSON_STOPLIST = {
    "Capitol Hill",
    "Federal Reserve",
    "Hong Kong",
    "House of Commons",
    "House of Lords",
    "Labour Party",
    "Liberal Democrats",
    "Los Angeles",
    "Middle East",
    "New Hampshire",
    "New Jersey",
    "New Mexico",
    "New Orleans",
    "New York",
    "North America",
    "North Carolina",
    "North Dakota",
    "Prime Minister",
    "Puerto Rico",
    "Reform UK",
    "Rhode Island",
    "Scottish National Party",
    "Saudi Arabia",
    "Silicon Valley",
    "South America",
    "South Carolina",
    "South Dakota",
    "Supreme Court",
    "UK Government",
    "United Kingdom",
    "United States",
    "Wall Street",
    "Westminster",
    "White House",
    "World Cup",
}

CONFIG = {
    "scope_sentence": FIXED_SCOPE,
    "dataset_start": DATE_WINDOW_START,
    "dataset_end": DATE_WINDOW_END,
    "dataset_query": UK_POLITICS_QUERY,
    "NEWS_API_KEY": os.getenv("NEWS_API_KEY"),
    "GUARDIAN_API_KEY": os.getenv("GUARDIAN_API_KEY"),
    "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
    "TECHNOLOGY_KEYWORDS": TECHNOLOGY_KEYWORDS,
    "TOPIC_KEYWORDS": TOPIC_KEYWORDS,
    "CONTROLLED_PREDICATES": CONTROLLED_PREDICATES,
    "ENTITY_STOPLIST": ENTITY_STOPLIST,
    "PERSON_STOPLIST": PERSON_STOPLIST,
    "POLITICAL_PERSON_TITLES": POLITICAL_PERSON_TITLES,
    "POLITICAL_PARTIES": POLITICAL_PARTIES,
    "GOVERNMENT_BODIES": GOVERNMENT_BODIES,
    "guardian_base_url": "https://content.guardianapis.com/search",
    "guardian_section": "politics",
    "guardian_page_size": 50,
    "guardian_max_pages": 4,
    "newsapi_base_url": "https://newsapi.org/v2/everything",
    "newsapi_page_size": 100,
    "newsapi_max_pages": 2,
}
