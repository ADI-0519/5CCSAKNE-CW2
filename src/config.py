from datetime import date
import os
from dotenv import load_dotenv

load_dotenv()



CONFIG = {
    # Today's date
    "today": date.today(),

    # ======API keys======
    "NEWS_API_KEY": os.getenv("NEWS_API_KEY"),
    "GUARDIAN_API_KEY": os.getenv("GUARDIAN_API_KEY"),

    # ======NEWSAPI======
    "Keywords": ["AI", "Machine Learning", "Robotics", "Artificial Intelligence"],
    
    # Extract news articles about AI
    "url1": ('https://newsapi.org/v2/everything?'
        f'q={" OR ".join("Keywords")}&'
        f'from={"today"}&'
        'sortBy=popularity&'
        f'apiKey={os.getenv("NEWS_API_KEY")}'),

    # Extract top-headlines
    "url2": ('https://newsapi.org/v2/top-headlines?'
        'country=us&'
        f'apiKey={os.getenv("NEWS_API_KEY")}')


}