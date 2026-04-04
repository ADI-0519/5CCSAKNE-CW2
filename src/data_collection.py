import requests
from datetime import date
import os
from dotenv import load_dotenv

#config
load_dotenv()
today = date.today()
config = {
    "NEWS_API_KEY": os.getenv("NEWS_API_KEY"),
    "GUARDIAN_API_KEY": os.getenv("GUARDIAN_API_KEY"),
    "Keywords": ["AI", "Machine Learning", "Robotics", "Artificial Intelligence"]
}


def data_collection():
    print("Collecting data...")

# Extract news articles about AI
    url = ('https://newsapi.org/v2/everything?'
        f'q={" OR ".join(config["Keywords"])}&'
        f'from={today}&'
        'sortBy=popularity&'
        f'apiKey={os.getenv("NEWS_API_KEY")}')
    response = requests.get(url)

    print(response.json())

# # Extract top-headlines
#     url2 = ('https://newsapi.org/v2/top-headlines?'
#         'country=us&'
#         f'apiKey={os.getenv("NEWS_API_KEY")}')
#     response2 = requests.get(url2)
#     print(response2.json())


data_collection()