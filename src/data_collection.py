# Code to collect data from a specified URL

import requests

def load_data_from_url(url):
    print("Collecting data...")
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to retrieve data from {url}. Status code: {response.status_code}")
        return None