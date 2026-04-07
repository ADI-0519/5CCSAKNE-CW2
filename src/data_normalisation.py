import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

from src.config import CONFIG

CONTROLLED_PREDICATES = CONFIG["CONTROLLED_PREDICATES"]


def build_stable_id(url, title, published_at):
    source = url if url else f"{title}{published_at}"
    return hashlib.sha256(source.encode()).hexdigest()[:16]


def normalise_name(name):
    if not name:
        return ""
    return " ".join(str(name).strip().split())


def canonicalise_date(date_str):
    if not date_str:
        raise ValueError(f"Cannot parse date: {date_str!r}")

    for fmt in ("%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%d"):
        try:
            dt = datetime.strptime(date_str, fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        except ValueError:
            continue
    raise ValueError(f"Cannot parse date: {date_str!r}")


def is_valid_url(url):
    try:
        parts = urlparse(url)
        return parts.scheme in ("http", "https") and bool(parts.netloc)
    except Exception:
        return False


def deduplicate_list(lst):
    seen = set()
    result = []
    for item in lst:
        key = str(item)
        if key not in seen:
            seen.add(key)
            result.append(item)
    return result


def count_words(text):
    if not text:
        return 0
    return len(str(text).split())


def contains_scope_term(text, scope_terms):
    lowered = str(text or "").lower()
    return any(term in lowered for term in scope_terms)


def is_relevant_newsapi_article(article):
    source_name = normalise_name((article.get("source") or {}).get("name"))
    if not source_name:
        return False
    if source_name not in CONFIG["NEWSAPI_ALLOWED_SOURCES"]:
        return False
    if source_name in CONFIG["NEWSAPI_BLOCKED_SOURCES"]:
        return False

    title = normalise_name(article.get("title"))
    description = normalise_name(article.get("description"))
    content = normalise_name(article.get("content"))
    combined_text = " ".join(part for part in (title, description, content) if part)
    if not combined_text:
        return False

    scope_terms = CONFIG["NEWSAPI_UK_SCOPE_TERMS"]
    return contains_scope_term(combined_text, scope_terms)


def normalise_relations(relations, record_index):
    normalised = []
    for rel in relations:
        pred = rel.get("predicate")
        if pred not in CONTROLLED_PREDICATES:
            raise ValueError(
                f"[NORMALISE] Record {record_index}: unknown predicate {pred!r}. "
                f"Allowed: {sorted(CONTROLLED_PREDICATES)}"
            )
        normalised.append(
            {
                "subject": normalise_name(rel["subject"]),
                "predicate": pred,
                "object": normalise_name(rel["object"]),
            }
        )
    return deduplicate_list(normalised)


def normalise_tags(tags):
    cleaned = []
    for tag in tags or []:
        if isinstance(tag, dict):
            tag_type = normalise_name(tag.get("type")).lower()
            if tag_type == "contributor":
                continue
            label = tag.get("webTitle") or tag.get("title") or tag.get("id")
        else:
            label = str(tag)
        label = normalise_name(label)
        if label:
            cleaned.append(label)
    return deduplicate_list(cleaned)


def guardian_section_name(article):
    return normalise_name(article.get("sectionName"))


def guardian_author(article):
    fields = article.get("fields") or {}
    return normalise_name(fields.get("byline"))


def guardian_summary(article):
    fields = article.get("fields") or {}
    return normalise_name(fields.get("trailText"))


def guardian_content(article):
    fields = article.get("fields") or {}
    return normalise_name(fields.get("bodyText"))


def normalise_newsapi_articles(raw_data):
    articles = raw_data.get("articles", [])
    normalised = []

    for i, article in enumerate(articles):
        title = normalise_name(article.get("title"))
        url = article.get("url") or ""
        published_at = article.get("publishedAt") or ""
        source_name = normalise_name((article.get("source") or {}).get("name"))

        if not title or not url or not published_at or not source_name:
            continue
        if not is_valid_url(url):
            continue
        if not is_relevant_newsapi_article(article):
            continue

        summary = normalise_name(article.get("description"))
        content = normalise_name(article.get("content"))
        author = normalise_name(article.get("author"))
        section = ""
        updated_at = None
        tags = []
        text_for_word_count = content or summary or title

        normalised.append(
            {
                "id": build_stable_id(url, title, published_at),
                "source_system": "newsapi",
                "source_name": source_name,
                "title": title,
                "url": url,
                "published_at": canonicalise_date(published_at),
                "updated_at": updated_at,
                "author": author or None,
                "section": section or None,
                "summary": summary or None,
                "content": content or None,
                "tags": tags,
                "word_count": count_words(text_for_word_count),
                "raw_article_type_hint": None,
            }
        )

    print(f"[NORMALISE] Normalised {len(normalised)} NewsAPI articles.")
    return normalised


def normalise_guardian_articles(raw_data):
    response = raw_data.get("response") or {}
    articles = response.get("results", [])
    normalised = []

    for i, article in enumerate(articles):
        title = normalise_name(article.get("webTitle"))
        url = article.get("webUrl") or ""
        published_at = article.get("webPublicationDate") or ""
        source_name = "The Guardian"

        if not title or not url or not published_at:
            continue
        if not is_valid_url(url):
            continue

        fields = article.get("fields") or {}
        content = guardian_content(article)
        summary = guardian_summary(article)
        author = guardian_author(article)
        section = guardian_section_name(article)
        updated_raw = fields.get("lastModified")
        updated_at = canonicalise_date(updated_raw) if updated_raw else None
        tags = normalise_tags(article.get("tags") or [])
        raw_type_hint = "OpinionArticle" if section.lower() == "comment is free" else None
        word_count = fields.get("wordcount")
        if word_count is None:
            word_count = count_words(content or summary or title)
        else:
            try:
                word_count = int(word_count)
            except (TypeError, ValueError):
                word_count = count_words(content or summary or title)

        normalised.append(
            {
                "id": build_stable_id(url, title, published_at),
                "source_system": "guardian",
                "source_name": source_name,
                "title": title,
                "url": url,
                "published_at": canonicalise_date(published_at),
                "updated_at": updated_at,
                "author": author or None,
                "section": section or None,
                "summary": summary or None,
                "content": content or None,
                "tags": tags,
                "word_count": word_count,
                "raw_article_type_hint": raw_type_hint,
            }
        )

    print(f"[NORMALISE] Normalised {len(normalised)} Guardian articles.")
    return normalised


def normalise_collected_sources(collected_data):
    sources = collected_data.get("sources", {})
    newsapi_records = normalise_newsapi_articles(sources.get("newsapi") or {})
    guardian_records = normalise_guardian_articles(sources.get("guardian") or {})
    combined = guardian_records + newsapi_records

    seen_ids = set()
    deduped = []
    for record in combined:
        if record["id"] in seen_ids:
            continue
        seen_ids.add(record["id"])
        deduped.append(record)

    print(f"[NORMALISE] Combined normalised article count: {len(deduped)}")
    return deduped


def save_normalised_articles(records, filename="normalised_articles.json"):
    output_path = Path(CONFIG["PROCESSED_DATA_DIR"]) / filename
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(records, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[NORMALISE] Saved normalised article set to {output_path}")
    return output_path


def normalise_data(extracted_data):
    print("[NORMALISE] Starting normalisation stage...")

    if not extracted_data:
        raise ValueError("[NORMALISE] No extracted data to normalise.")

    normalised = []
    for i, record in enumerate(extracted_data):
        title = record.get("title")
        url = record.get("url")
        published_at = record.get("published_at")
        source_name = record.get("source_name")

        if not title:
            raise ValueError(f"[NORMALISE] Record {i}: missing required field 'title'.")
        if not url:
            raise ValueError(f"[NORMALISE] Record {i}: missing required field 'url'.")
        if not is_valid_url(url):
            raise ValueError(f"[NORMALISE] Record {i}: invalid URL {url!r}.")
        if not published_at:
            raise ValueError(f"[NORMALISE] Record {i}: missing required field 'published_at'.")
        if not source_name:
            raise ValueError(f"[NORMALISE] Record {i}: missing required field 'source_name'.")

        canonical_date = canonicalise_date(published_at)
        stable_id = build_stable_id(url, title, published_at)

        entities = record.get("entities", {})
        normalised_entities = {
            "organizations": deduplicate_list(
                [normalise_name(o) for o in entities.get("organizations", [])]
            ),
            "people": deduplicate_list([normalise_name(p) for p in entities.get("people", [])]),
            "politicians": deduplicate_list(
                [normalise_name(p) for p in entities.get("politicians", [])]
            ),
            "political_parties": deduplicate_list(
                [normalise_name(party) for party in entities.get("political_parties", [])]
            ),
            "government_bodies": deduplicate_list(
                [normalise_name(body) for body in entities.get("government_bodies", [])]
            ),
            "locations": deduplicate_list(
                [normalise_name(location) for location in entities.get("locations", [])]
            ),
            "technologies": deduplicate_list(
                [normalise_name(t) for t in entities.get("technologies", [])]
            ),
            "topics": deduplicate_list([normalise_name(t) for t in entities.get("topics", [])]),
            "events": deduplicate_list(
                [normalise_name(event) for event in entities.get("events", [])]
            ),
        }

        author = record.get("author")
        event_candidates = []
        for event in record.get("event_candidates", []):
            event_candidates.append(
                {
                    "name": normalise_name(event.get("name")),
                    "type": normalise_name(event.get("type")),
                    "date": event.get("date"),
                    "location": normalise_name(event.get("location"))
                    if event.get("location")
                    else None,
                    "source": normalise_name(event.get("source")),
                }
            )

        follow_up_candidates = []
        for candidate in record.get("follow_up_candidates", []):
            follow_up_candidates.append(
                {
                    "match_key": normalise_name(candidate.get("match_key")),
                    "reason": normalise_name(candidate.get("reason")),
                }
            )

        normalised.append(
            {
                "id": stable_id,
                "title": normalise_name(title),
                "url": url,
                "published_at": canonical_date,
                "updated_at": canonicalise_date(record["updated_at"])
                if record.get("updated_at")
                else None,
                "source_system": normalise_name(record.get("source_system")),
                "source_name": normalise_name(source_name),
                "author": normalise_name(author) if author else None,
                "section": normalise_name(record.get("section")) if record.get("section") else None,
                "summary": normalise_name(record.get("summary")) if record.get("summary") else None,
                "content": normalise_name(record.get("content")) if record.get("content") else None,
                "tags": deduplicate_list([normalise_name(tag) for tag in record.get("tags", [])]),
                "word_count": int(record.get("word_count") or 0),
                "article_type": normalise_name(record.get("article_type")) or "NewsArticle",
                "sentiment": normalise_name(record.get("sentiment")) or "Neutral",
                "event_candidates": event_candidates,
                "follow_up_candidates": follow_up_candidates,
                "entities": normalised_entities,
                "relations": normalise_relations(record.get("relations", []), i),
            }
        )

    print(f"[NORMALISE] Normalised {len(normalised)} extracted records.")
    return normalised
