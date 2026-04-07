import json
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import requests

from src.config import CONFIG, build_guardian_page_url, build_newsapi_page_url


def safe_url_for_logging(url):
    parts = urlsplit(url)
    query_params = []
    for key, value in parse_qsl(parts.query, keep_blank_values=True):
        if key.lower() in {"apikey", "api-key"}:
            query_params.append((key, "REDACTED"))
        else:
            query_params.append((key, value))
    return urlunsplit(
        (parts.scheme, parts.netloc, parts.path, urlencode(query_params), parts.fragment)
    )


def fetch_json(url):
    safe_url = safe_url_for_logging(url)
    print(f"[COLLECT] Fetching data from URL: {safe_url}")
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        raise RuntimeError(f"[COLLECT] HTTP error fetching {safe_url}: {e}") from e
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"[COLLECT] Request failed for {safe_url}: {e}") from e
    except ValueError as e:
        raise RuntimeError(f"[COLLECT] Failed to parse JSON response from {safe_url}: {e}") from e


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
    output_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[COLLECT] Saved raw {source_name} payload to {output_path}")
    return output_path


def load_json_file(path):
    input_path = Path(path)
    if not input_path.exists():
        raise FileNotFoundError(f"[COLLECT] JSON file not found: {input_path}")
    return json.loads(input_path.read_text(encoding="utf-8"))


def latest_snapshot_path(source_name):
    source_dir = Path(CONFIG["RAW_DATA_DIR"]) / source_name
    if not source_dir.exists():
        raise FileNotFoundError(f"[COLLECT] Snapshot directory not found: {source_dir}")

    snapshots = sorted(source_dir.glob("*.json"))
    if not snapshots:
        raise FileNotFoundError(f"[COLLECT] No JSON snapshots found in {source_dir}")
    return snapshots[-1]


def load_cached_source(source_name, snapshot_path=None):
    source_path = (
        Path(snapshot_path) if snapshot_path is not None else latest_snapshot_path(source_name)
    )
    data = load_json_file(source_path)
    print(f"[COLLECT] Loaded cached {source_name} payload from {source_path}")
    return data


def build_collection_payload(sources, errors=None):
    return {
        "scope": {
            "project_scope": CONFIG["project_scope"],
            "date_start": CONFIG["date_start"],
            "date_end": CONFIG["date_end"],
        },
        "sources": sources,
        "collection_errors": errors or {},
    }


def fetch_newsapi_data(save_snapshot=True):
    first_page = fetch_json(build_newsapi_page_url(page=1))
    total_results = first_page.get("totalResults", 0)
    articles = list(first_page.get("articles", []))

    data = {
        "status": first_page.get("status"),
        "totalResults": total_results,
        "articles": articles,
        "pagesFetched": 1,
        "resultLimitNote": (
            "NewsAPI developer-tier access is limited to the first 100 results. "
            "The pipeline therefore fetches page 1 only and treats NewsAPI as a "
            "supplementary source."
        ),
    }
    if save_snapshot:
        save_raw_json(data, "newsapi")
    return data


def fetch_guardian_data(save_snapshot=True):
    first_page = fetch_json(build_guardian_page_url(page=1))
    response = first_page.get("response") or {}
    total_pages = max(1, response.get("pages", 1))

    results = list(response.get("results", []))
    for page in range(2, total_pages + 1):
        page_data = fetch_json(build_guardian_page_url(page=page))
        page_response = page_data.get("response") or {}
        results.extend(page_response.get("results", []))

    data = {
        "response": {
            **response,
            "results": results,
            "pagesFetched": total_pages,
        }
    }
    if save_snapshot:
        save_raw_json(data, "guardian")
    return data


def collect_all_sources(save_snapshots=True):
    sources = {}
    errors = {}

    print("[COLLECT] Collecting NewsAPI data...")
    try:
        sources["newsapi"] = fetch_newsapi_data(save_snapshot=save_snapshots)
    except Exception as exc:
        errors["newsapi"] = str(exc)
        print(f"[COLLECT] NewsAPI collection failed: {exc}")

    print("[COLLECT] Collecting Guardian data...")
    try:
        sources["guardian"] = fetch_guardian_data(save_snapshot=save_snapshots)
    except Exception as exc:
        errors["guardian"] = str(exc)
        print(f"[COLLECT] Guardian collection failed: {exc}")

    if not sources:
        raise RuntimeError("[COLLECT] No source data could be collected from any provider.")

    return build_collection_payload(sources, errors)


def load_cached_sources(newsapi_snapshot=None, guardian_snapshot=None):
    sources = {}
    errors = {}

    for source_name, snapshot_path in (
        ("newsapi", newsapi_snapshot),
        ("guardian", guardian_snapshot),
    ):
        try:
            sources[source_name] = load_cached_source(source_name, snapshot_path=snapshot_path)
        except Exception as exc:
            errors[source_name] = str(exc)
            print(f"[COLLECT] Cached {source_name} load failed: {exc}")

    if not sources:
        raise RuntimeError("[COLLECT] No cached source data could be loaded from disk.")

    return build_collection_payload(sources, errors)


def load_data_from_url(url):
    return fetch_json(url)
