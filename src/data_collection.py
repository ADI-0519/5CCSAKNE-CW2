import json
from datetime import UTC, datetime
from pathlib import Path

import requests

from src.config import CONFIG


def fetch_json(url):
    print(f"[COLLECT] Fetching data from URL: {url}")
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        raise RuntimeError(f"[COLLECT] HTTP error fetching {url}: {e}") from e
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"[COLLECT] Request failed for {url}: {e}") from e
    except ValueError as e:
        raise RuntimeError(f"[COLLECT] Failed to parse JSON response from {url}: {e}") from e


def build_timestamp():
    return datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")


def ensure_parent(path):
    path.parent.mkdir(parents=True, exist_ok=True)


def save_raw_json(data, source_name, filename=None):
    raw_dir = Path(CONFIG["RAW_DATA_DIR"]) / source_name
    if filename is None:
        filename = f"{build_timestamp()}.json"

    output_path = raw_dir / filename
    ensure_parent(output_path)
    output_path.write_text(json.dumps(data, indent=2, ensure_ascii=False))
    print(f"[COLLECT] Saved raw {source_name} payload to {output_path}")
    return output_path


def fetch_newsapi_data(save_snapshot=True):
    url = CONFIG["url_newsapi_everything"]
    data = fetch_json(url)
    if save_snapshot:
        save_raw_json(data, "newsapi")
    return data


def fetch_guardian_data(save_snapshot=True):
    url = CONFIG["url_guardian"]
    data = fetch_json(url)
    if save_snapshot:
        save_raw_json(data, "guardian")
    return data


def collect_all_sources(save_snapshots=True):
    print("[COLLECT] Collecting NewsAPI data...")
    newsapi_data = fetch_newsapi_data(save_snapshot=save_snapshots)

    print("[COLLECT] Collecting Guardian data...")
    guardian_data = fetch_guardian_data(save_snapshot=save_snapshots)

    return {
        "scope": {
            "project_scope": CONFIG["project_scope"],
            "date_start": CONFIG["date_start"],
            "date_end": CONFIG["date_end"],
        },
        "sources": {
            "newsapi": newsapi_data,
            "guardian": guardian_data,
        },
    }


def load_data_from_url(url):
    return fetch_json(url)
