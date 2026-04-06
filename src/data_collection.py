import hashlib
import json
from pathlib import Path

import requests

from src.config import CONFIG

RAW_DATA_DIR = Path("data/raw")


def _stable_id(source_system, url, title, published_at):
    source = f"{source_system}|{url}|{title}|{published_at}"
    return hashlib.sha256(source.encode()).hexdigest()[:16]


def _infer_article_type_hint(title, section, tags):
    text = " ".join(filter(None, [title, section, *tags])).lower()
    if any(term in text for term in ("opinion", "comment", "analysis", "editorial")):
        return "opinion"
    if any(term in text for term in ("breaking", "live", "developing", "urgent")):
        return "breaking"
    return None


def _estimate_word_count(*parts):
    text = " ".join(part for part in parts if part)
    return len(text.split()) if text else None


def _save_json_snapshot(filename, payload):
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    target = RAW_DATA_DIR / filename
    target.write_text(json.dumps(payload, indent=2))


def fetch_json(url, params=None, headers=None):
    try:
        response = requests.get(url, params=params, headers=headers, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        raise RuntimeError(f"[COLLECT] HTTP error fetching {url}: {e}") from e
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"[COLLECT] Request failed for {url}: {e}") from e
    except ValueError as e:
        raise RuntimeError(f"[COLLECT] Failed to parse JSON response from {url}: {e}") from e


def _guardian_result_to_record(result):
    fields = result.get("fields") or {}
    tags = result.get("tags") or []
    tag_labels = [tag.get("webTitle") for tag in tags if tag.get("webTitle")]
    title = fields.get("headline") or result.get("webTitle") or ""
    published_at = result.get("webPublicationDate") or ""
    updated_at = fields.get("lastModified") or published_at
    summary = fields.get("trailText") or ""
    content = fields.get("bodyText") or ""
    url = result.get("webUrl") or ""

    return {
        "id": _stable_id("guardianapi", url, title, published_at),
        "source_name": "The Guardian",
        "source_system": "guardianapi",
        "title": title,
        "url": url,
        "published_at": published_at,
        "updated_at": updated_at,
        "author": fields.get("byline"),
        "section": result.get("sectionName"),
        "tags": tag_labels,
        "summary": summary,
        "content": content,
        "word_count": int(fields["wordcount"]) if fields.get("wordcount") else _estimate_word_count(title, summary, content),
        "raw_article_type_hint": _infer_article_type_hint(title, result.get("sectionName") or "", tag_labels),
    }


def _newsapi_article_to_record(article):
    source = article.get("source") or {}
    title = article.get("title") or ""
    published_at = article.get("publishedAt") or ""
    summary = article.get("description") or ""
    content = article.get("content") or ""
    url = article.get("url") or ""
    source_name = source.get("name") or "Unknown Source"
    tags = []

    return {
        "id": _stable_id("newsapi", url, title, published_at),
        "source_name": source_name,
        "source_system": "newsapi",
        "title": title,
        "url": url,
        "published_at": published_at,
        "updated_at": published_at,
        "author": article.get("author"),
        "section": "Politics",
        "tags": tags,
        "summary": summary,
        "content": content,
        "word_count": _estimate_word_count(title, summary, content),
        "raw_article_type_hint": _infer_article_type_hint(title, "Politics", tags),
    }


def collect_guardian_articles():
    print("[COLLECT] Fetching GuardianAPI articles...")
    params = {
        "api-key": CONFIG["GUARDIAN_API_KEY"],
        "q": CONFIG["dataset_query"],
        "section": CONFIG["guardian_section"],
        "from-date": CONFIG["dataset_start"],
        "to-date": CONFIG["dataset_end"],
        "page-size": CONFIG["guardian_page_size"],
        "show-fields": "headline,trailText,bodyText,byline,lastModified,wordcount",
        "show-tags": "all",
        "order-by": "newest",
        "page": 1,
    }

    first_page = fetch_json(CONFIG["guardian_base_url"], params=params)
    _save_json_snapshot(
        f"guardian_{CONFIG['dataset_start']}_{CONFIG['dataset_end']}_page1.json",
        first_page,
    )

    response = first_page.get("response") or {}
    results = list(response.get("results") or [])
    total_pages = min(response.get("pages") or 1, CONFIG["guardian_max_pages"])

    for page in range(2, total_pages + 1):
        params["page"] = page
        payload = fetch_json(CONFIG["guardian_base_url"], params=params)
        _save_json_snapshot(
            f"guardian_{CONFIG['dataset_start']}_{CONFIG['dataset_end']}_page{page}.json",
            payload,
        )
        results.extend((payload.get("response") or {}).get("results") or [])

    return [_guardian_result_to_record(result) for result in results]


def collect_newsapi_articles():
    print("[COLLECT] Fetching NewsAPI articles...")
    params = {
        "apiKey": CONFIG["NEWS_API_KEY"],
        "q": CONFIG["dataset_query"],
        "from": CONFIG["dataset_start"],
        "to": CONFIG["dataset_end"],
        "language": "en",
        "sortBy": "publishedAt",
        "pageSize": CONFIG["newsapi_page_size"],
        "page": 1,
    }

    try:
        first_page = fetch_json(CONFIG["newsapi_base_url"], params=params)
    except RuntimeError as error:
        if "426" in str(error):
            print("[COLLECT] NewsAPI access for the exact date window is unavailable on this plan.")
            print("[COLLECT] Continuing with Guardian records only for this run.")
            return []
        raise
    _save_json_snapshot(
        f"newsapi_{CONFIG['dataset_start']}_{CONFIG['dataset_end']}_page1.json",
        first_page,
    )

    total_results = first_page.get("totalResults") or 0
    total_pages = min(
        ((total_results - 1) // CONFIG["newsapi_page_size"]) + 1 if total_results else 1,
        CONFIG["newsapi_max_pages"],
    )

    articles = list(first_page.get("articles") or [])
    for page in range(2, total_pages + 1):
        params["page"] = page
        payload = fetch_json(CONFIG["newsapi_base_url"], params=params)
        _save_json_snapshot(
            f"newsapi_{CONFIG['dataset_start']}_{CONFIG['dataset_end']}_page{page}.json",
            payload,
        )
        articles.extend(payload.get("articles") or [])

    return [_newsapi_article_to_record(article) for article in articles]


def _deduplicate_records(records):
    deduped = []
    seen_urls = set()

    for record in records:
        url = record.get("url")
        if not url or url in seen_urls:
            continue
        seen_urls.add(url)
        deduped.append(record)

    return deduped


def collect_politics_news_dataset():
    if not CONFIG["GUARDIAN_API_KEY"]:
        raise RuntimeError("[COLLECT] GUARDIAN_API_KEY is required for the fixed Guardian dataset.")
    if not CONFIG["NEWS_API_KEY"]:
        raise RuntimeError("[COLLECT] NEWS_API_KEY is required for the fixed NewsAPI dataset.")

    guardian_records = collect_guardian_articles()
    newsapi_records = collect_newsapi_articles()
    articles = _deduplicate_records(guardian_records + newsapi_records)

    print(
        f"[COLLECT] Collected {len(guardian_records)} Guardian records, "
        f"{len(newsapi_records)} NewsAPI records, {len(articles)} after deduplication."
    )

    return {"scope": CONFIG["scope_sentence"], "articles": articles}
