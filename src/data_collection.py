import json
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import parse_qsl, quote_plus, urlencode, urlsplit, urlunsplit

import requests

from src.config import CONFIG, build_guardian_page_url, build_newsapi_page_url

DEFAULT_TIMEOUT_SECONDS = 30
DEFAULT_PAGE_SIZE = 100
CORE_COLLECTION_SOURCES = tuple(CONFIG["CORE_SOURCE_ORDER"])
LEGACY_COLLECTION_SOURCES = ("newsapi",)


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
        response = requests.get(url, timeout=DEFAULT_TIMEOUT_SECONDS)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as exc:
        raise RuntimeError(f"[COLLECT] HTTP error fetching {safe_url}: {exc}") from exc
    except requests.exceptions.RequestException as exc:
        raise RuntimeError(f"[COLLECT] Request failed for {safe_url}: {exc}") from exc
    except ValueError as exc:
        raise RuntimeError(
            f"[COLLECT] Failed to parse JSON response from {safe_url}: {exc}"
        ) from exc


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


def build_parliament_search_url(page=1):
    query = quote_plus(" OR ".join(CONFIG["PARLIAMENT_QUERY_TERMS"]))
    skip = max(0, page - 1) * DEFAULT_PAGE_SIZE
    return (
        f"{CONFIG['PARLIAMENT_API_BASE'].rstrip('/')}/search?"
        f"q={query}&"
        f"take={DEFAULT_PAGE_SIZE}&"
        f"skip={skip}&"
        f"from-date={CONFIG['date_start']}&"
        f"to-date={CONFIG['date_end']}"
    )


def derive_govuk_search_base():
    content_base = CONFIG["GOVUK_CONTENT_API_BASE"].rstrip("/")
    if content_base.endswith("/api/content"):
        return f"{content_base[: -len('/api/content')]}/api/search.json"
    return f"{content_base}/search.json"


def build_govuk_search_url(page=1):
    query = quote_plus(" OR ".join(CONFIG["GOVUK_QUERY_TERMS"]))
    start = max(0, page - 1) * DEFAULT_PAGE_SIZE
    return (
        f"{derive_govuk_search_base()}?"
        f"q={query}&"
        f"count={DEFAULT_PAGE_SIZE}&"
        f"start={start}&"
        f"order=-public_timestamp"
    )


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
            "supplementary legacy source."
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


def fetch_parliament_data(save_snapshot=True):
    url = build_parliament_search_url(page=1)
    first_page = fetch_json(url)
    data = {
        "query_terms": CONFIG["PARLIAMENT_QUERY_TERMS"],
        "date_start": CONFIG["date_start"],
        "date_end": CONFIG["date_end"],
        "request_url": safe_url_for_logging(url),
        "pagesFetched": 1,
        "response": first_page,
    }
    if save_snapshot:
        save_raw_json(data, "parliament")
    return data


def fetch_govuk_data(save_snapshot=True):
    url = build_govuk_search_url(page=1)
    first_page = fetch_json(url)
    data = {
        "query_terms": CONFIG["GOVUK_QUERY_TERMS"],
        "document_formats": CONFIG["GOVUK_DOCUMENT_FORMATS"],
        "date_start": CONFIG["date_start"],
        "date_end": CONFIG["date_end"],
        "request_url": safe_url_for_logging(url),
        "pagesFetched": 1,
        "response": first_page,
    }
    if save_snapshot:
        save_raw_json(data, "govuk")
    return data


SOURCE_FETCHERS = {
    "guardian": fetch_guardian_data,
    "parliament": fetch_parliament_data,
    "govuk": fetch_govuk_data,
    "newsapi": fetch_newsapi_data,
}


def resolve_source_names(source_names=None, include_legacy_newsapi=False):
    if source_names is None:
        names = list(CORE_COLLECTION_SOURCES)
    else:
        names = list(source_names)

    if include_legacy_newsapi and "newsapi" not in names:
        names.append("newsapi")
    return names


def collect_all_sources(save_snapshots=True, source_names=None, include_legacy_newsapi=False):
    sources = {}
    errors = {}

    for source_name in resolve_source_names(
        source_names=source_names, include_legacy_newsapi=include_legacy_newsapi
    ):
        fetcher = SOURCE_FETCHERS.get(source_name)
        if fetcher is None:
            errors[source_name] = f"Unsupported source {source_name!r}"
            print(f"[COLLECT] Unsupported source configured: {source_name}")
            continue

        print(f"[COLLECT] Collecting {source_name} data...")
        try:
            sources[source_name] = fetcher(save_snapshot=save_snapshots)
        except Exception as exc:
            errors[source_name] = str(exc)
            print(f"[COLLECT] {source_name} collection failed: {exc}")

    if not sources:
        raise RuntimeError("[COLLECT] No source data could be collected from any provider.")

    return build_collection_payload(sources, errors)


def build_snapshot_overrides(
    source_snapshots=None,
    *,
    newsapi_snapshot=None,
    guardian_snapshot=None,
    parliament_snapshot=None,
    govuk_snapshot=None,
):
    overrides = dict(source_snapshots or {})
    named_overrides = {
        "newsapi": newsapi_snapshot,
        "guardian": guardian_snapshot,
        "parliament": parliament_snapshot,
        "govuk": govuk_snapshot,
    }
    for source_name, snapshot_path in named_overrides.items():
        if snapshot_path is not None:
            overrides[source_name] = snapshot_path
    return overrides


def load_cached_sources(
    source_snapshots=None,
    *,
    newsapi_snapshot=None,
    guardian_snapshot=None,
    parliament_snapshot=None,
    govuk_snapshot=None,
    source_names=None,
    include_legacy_newsapi=False,
):
    sources = {}
    errors = {}
    snapshot_overrides = build_snapshot_overrides(
        source_snapshots,
        newsapi_snapshot=newsapi_snapshot,
        guardian_snapshot=guardian_snapshot,
        parliament_snapshot=parliament_snapshot,
        govuk_snapshot=govuk_snapshot,
    )

    for source_name in resolve_source_names(
        source_names=source_names, include_legacy_newsapi=include_legacy_newsapi
    ):
        try:
            sources[source_name] = load_cached_source(
                source_name, snapshot_path=snapshot_overrides.get(source_name)
            )
        except Exception as exc:
            errors[source_name] = str(exc)
            print(f"[COLLECT] Cached {source_name} load failed: {exc}")

    if not sources:
        raise RuntimeError("[COLLECT] No cached source data could be loaded from disk.")

    return build_collection_payload(sources, errors)


def load_data_from_url(url):
    return fetch_json(url)
