import os
from datetime import date

from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Entity extraction dictionaries
# ---------------------------------------------------------------------------

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
    "healthcare",
    "finance",
    "economy",
    "climate",
    "education",
    "politics",
    "security",
    "privacy",
    "regulation",
    "policy",
    "research",
    "startup",
    "investment",
    "funding",
    "acquisition",
    "merger",
    "IPO",
    "innovation",
    "sustainability",
    "energy",
    "space",
    "defense",
    "government",
]

# Allowed predicate names; any other predicate causes a validation failure.
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

# Words that look like entity names but should be ignored.
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
    "North America",
    "South America",
    "United States",
    "United Kingdom",
}

# Two-word capitalized phrases that look like names but are places/orgs.
PERSON_STOPLIST = {
    "New York",
    "Los Angeles",
    "San Francisco",
    "Las Vegas",
    "New Orleans",
    "United States",
    "United Kingdom",
    "North Korea",
    "South Korea",
    "North America",
    "South America",
    "Middle East",
    "White House",
    "Supreme Court",
    "Federal Reserve",
    "Wall Street",
    "Main Street",
    "Capitol Hill",
    "Silicon Valley",
    "World Cup",
    "Super Bowl",
    "New Jersey",
    "New Mexico",
    "New Hampshire",
    "West Virginia",
    "North Carolina",
    "South Carolina",
    "North Dakota",
    "South Dakota",
    "Rhode Island",
    "Puerto Rico",
    "Hong Kong",
    "Saudi Arabia",
}

# ---------------------------------------------------------------------------
# Main config
# ---------------------------------------------------------------------------

CONFIG = {
    "today": date.today(),
    "NEWS_API_KEY": os.getenv("NEWS_API_KEY"),
    "GUARDIAN_API_KEY": os.getenv("GUARDIAN_API_KEY"),
    "Keywords": ["AI", "Machine Learning", "Robotics", "Artificial Intelligence"],
    "TECHNOLOGY_KEYWORDS": TECHNOLOGY_KEYWORDS,
    "TOPIC_KEYWORDS": TOPIC_KEYWORDS,
    "CONTROLLED_PREDICATES": CONTROLLED_PREDICATES,
    "ENTITY_STOPLIST": ENTITY_STOPLIST,
    "PERSON_STOPLIST": PERSON_STOPLIST,
}

CONFIG["url_ai"] = (
    "https://newsapi.org/v2/everything?"
    f"q={' OR '.join(CONFIG['Keywords'])}&"
    f"from={CONFIG['today']}&"
    "sortBy=popularity&"
    f"apiKey={CONFIG['NEWS_API_KEY']}"
)

CONFIG["url_headlines"] = (
    f"https://newsapi.org/v2/top-headlines?country=us&apiKey={CONFIG['NEWS_API_KEY']}"
)
