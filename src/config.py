from datetime import date
import os
from dotenv import load_dotenv

load_dotenv()

CONFIG = {
    "today": date.today(),
    "NEWS_API_KEY": os.getenv("NEWS_API_KEY"),
    "GUARDIAN_API_KEY": os.getenv("GUARDIAN_API_KEY"),
    "Keywords": ["AI", "Machine Learning", "Robotics", "Artificial Intelligence"],
}

CONFIG["url_ai"] = (
    'https://newsapi.org/v2/everything?'
    f'q={" OR ".join(CONFIG["Keywords"])}&'
    f'from={CONFIG["today"]}&'
    'sortBy=popularity&'
    f'apiKey={CONFIG["NEWS_API_KEY"]}'
)

CONFIG["url_headlines"] = (
    'https://newsapi.org/v2/top-headlines?'
    'country=us&'
    f'apiKey={CONFIG["NEWS_API_KEY"]}'
)