# Code to collect data from a specified URL

import requests


def load_data_from_url(url):
    print("[COLLECT] Fetching data from URL...")
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        raise RuntimeError(f"[COLLECT] HTTP error fetching {url}: {e}") from e
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"[COLLECT] Request failed for {url}: {e}") from e
    except ValueError as e:
        raise RuntimeError(f"[COLLECT] Failed to parse JSON response from {url}: {e}") from e