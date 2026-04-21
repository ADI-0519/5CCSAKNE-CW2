import json
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import requests

from src.config import CONFIG, build_guardian_page_url
from src.govuk_scope import govuk_result_is_in_scope

DEFAULT_TIMEOUT_SECONDS = 30
DEFAULT_PAGE_SIZE = 100
DEFAULT_GOVUK_MAX_PAGES = 20
CORE_COLLECTION_SOURCES = tuple(CONFIG["CORE_SOURCE_ORDER"])


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
    skip = max(0, page - 1) * DEFAULT_PAGE_SIZE
    return (
        f"{CONFIG['PARLIAMENT_API_BASE'].rstrip('/')}/api/writtenstatements/statements?"
        f"madeWhenFrom={CONFIG['date_start']}&"
        f"madeWhenTo={CONFIG['date_end']}&"
        f"take={DEFAULT_PAGE_SIZE}&"
        f"skip={skip}"
    )


def derive_govuk_search_base():
    content_base = CONFIG["GOVUK_CONTENT_API_BASE"].rstrip("/")
    if content_base.endswith("/api/content"):
        return f"{content_base[: -len('/api/content')]}/api/search.json"
    return f"{content_base}/search.json"


def build_govuk_search_url(page=1):
    start = max(0, page - 1) * DEFAULT_PAGE_SIZE
    params = [
        ("q", " OR ".join(CONFIG["GOVUK_QUERY_TERMS"])),
        ("count", str(DEFAULT_PAGE_SIZE)),
        ("start", str(start)),
        ("order", "-public_timestamp"),
        (
            "filter_public_timestamp",
            f"from:{CONFIG['date_start']},to:{CONFIG['date_end']}",
        ),
    ]
    for document_format in CONFIG["GOVUK_DOCUMENT_FORMATS"]:
        params.append(("filter_format", document_format))
    return f"{derive_govuk_search_base()}?{urlencode(params)}"


def govuk_result_date(item):
    return str(
        item.get("public_timestamp") or item.get("timestamp") or item.get("updated_at") or ""
    )[:10]


def govuk_result_in_window(item):
    result_date = govuk_result_date(item)
    return bool(result_date) and CONFIG["date_start"] <= result_date <= CONFIG["date_end"]


def govuk_result_is_older_than_window(item):
    result_date = govuk_result_date(item)
    return bool(result_date) and result_date < CONFIG["date_start"]


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


def _flatten_parliament_item(item):
    flat = dict(item.get("value") or {})
    # rename fields to what normaliser looks for
    if "dateMade" in flat:
        flat["date"] = flat.pop("dateMade")
    if "text" in flat:
        flat["body"] = flat.pop("text")
    if "answeringBodyName" in flat:
        flat["bodyName"] = flat.pop("answeringBodyName")

    for link in item.get("links") or []:
        if link.get("rel") == "self" and link.get("href"):
            href = link["href"]
            if href.startswith("/"):
                href = "https://questions-statements.parliament.uk" + href
            flat["url"] = href
            break
    return flat


def fetch_parliament_data(save_snapshot=True):
    url = build_parliament_search_url(page=1)
    first_page = fetch_json(url)
    first_page["results"] = [
        _flatten_parliament_item(item) for item in (first_page.get("results") or [])
    ]
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
    collected_results = []
    pages_fetched = 0
    total = None
    last_url = None

    for page in range(1, DEFAULT_GOVUK_MAX_PAGES + 1):
        url = build_govuk_search_url(page=page)
        page_data = fetch_json(url)
        pages_fetched += 1
        last_url = url

        total = page_data.get("total", total)
        page_results = page_data.get("results", []) if isinstance(page_data, dict) else []
        if not page_results:
            break

        collected_results.extend(
            item
            for item in page_results
            if isinstance(item, dict)
            and govuk_result_in_window(item)
            and govuk_result_is_in_scope(item)
        )

        if any(govuk_result_is_older_than_window(item) for item in page_results):
            break

        start = page_data.get("start")
        if total is not None and isinstance(start, int) and start + DEFAULT_PAGE_SIZE >= total:
            break

    data = {
        "query_terms": CONFIG["GOVUK_QUERY_TERMS"],
        "document_formats": CONFIG["GOVUK_DOCUMENT_FORMATS"],
        "date_start": CONFIG["date_start"],
        "date_end": CONFIG["date_end"],
        "request_url": safe_url_for_logging(last_url or build_govuk_search_url(page=1)),
        "pagesFetched": pages_fetched,
        "response": {
            "results": collected_results,
            "total": total if total is not None else len(collected_results),
            "start": 0,
        },
    }
    if save_snapshot:
        save_raw_json(data, "govuk")
    return data


SOURCE_FETCHERS = {
    "guardian": fetch_guardian_data,
    "parliament": fetch_parliament_data,
    "govuk": fetch_govuk_data,
}


def resolve_source_names(source_names=None):
    if source_names is None:
        return list(CORE_COLLECTION_SOURCES)
    return list(source_names)


def collect_all_sources(save_snapshots=True, source_names=None):
    sources = {}
    errors = {}

    for source_name in resolve_source_names(source_names=source_names):
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
    guardian_snapshot=None,
    parliament_snapshot=None,
    govuk_snapshot=None,
):
    overrides = dict(source_snapshots or {})
    named_overrides = {
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
    guardian_snapshot=None,
    parliament_snapshot=None,
    govuk_snapshot=None,
    source_names=None,
):
    sources = {}
    errors = {}
    snapshot_overrides = build_snapshot_overrides(
        source_snapshots,
        guardian_snapshot=guardian_snapshot,
        parliament_snapshot=parliament_snapshot,
        govuk_snapshot=govuk_snapshot,
    )

    for source_name in resolve_source_names(source_names=source_names):
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
