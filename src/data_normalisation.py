# Code to normalise the extracted data

import hashlib
from datetime import datetime, timezone
from urllib.parse import urlparse

from src.config import CONFIG

CONTROLLED_PREDICATES = CONFIG["CONTROLLED_PREDICATES"]


def _stable_id(url, title, published_at):
    source = url if url else f"{title}{published_at}"
    return hashlib.sha256(source.encode()).hexdigest()[:16]


def _normalise_name(name):
    if not name:
        return ""
    return " ".join(name.strip().split())


def _canonicalise_date(date_str):
    """Parse a date string and return a UTC ISO-8601 string (YYYY-MM-DDTHH:MM:SSZ)."""
    for fmt in ("%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%d"):
        try:
            dt = datetime.strptime(date_str, fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        except ValueError:
            continue
    raise ValueError(f"Cannot parse date: {date_str!r}")


def _is_valid_url(url):
    try:
        parts = urlparse(url)
        return parts.scheme in ("http", "https") and bool(parts.netloc)
    except Exception:
        return False


def _dedup_list(lst):
    seen = set()
    result = []
    for item in lst:
        key = str(item)
        if key not in seen:
            seen.add(key)
            result.append(item)
    return result


def _normalise_relations(relations, record_index):
    normalised = []
    for rel in relations:
        pred = rel.get("predicate")
        if pred not in CONTROLLED_PREDICATES:
            raise ValueError(
                f"[NORMALISE] Record {record_index}: unknown predicate {pred!r}. "
                f"Allowed: {sorted(CONTROLLED_PREDICATES)}"
            )
        normalised.append({
            "subject": _normalise_name(rel["subject"]),
            "predicate": pred,
            "object": _normalise_name(rel["object"]),
        })
    return _dedup_list(normalised)


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

        # --- Required field validation (fail-fast) ---
        if not title:
            raise ValueError(f"[NORMALISE] Record {i}: missing required field 'title'.")
        if not url:
            raise ValueError(f"[NORMALISE] Record {i}: missing required field 'url'.")
        if not _is_valid_url(url):
            raise ValueError(f"[NORMALISE] Record {i}: invalid URL {url!r}.")
        if not published_at:
            raise ValueError(f"[NORMALISE] Record {i}: missing required field 'published_at'.")
        if not source_name:
            raise ValueError(f"[NORMALISE] Record {i}: missing required field 'source_name'.")

        canonical_date = _canonicalise_date(published_at)
        stable_id = _stable_id(url, title, published_at)

        entities = record.get("entities", {})
        normalised_entities = {
            "organizations": _dedup_list(
                [_normalise_name(o) for o in entities.get("organizations", [])]
            ),
            "people": _dedup_list(
                [_normalise_name(p) for p in entities.get("people", [])]
            ),
            "locations": _dedup_list(
                [_normalise_name(l) for l in entities.get("locations", [])]
            ),
            "technologies": _dedup_list(
                [_normalise_name(t) for t in entities.get("technologies", [])]
            ),
            "topics": _dedup_list(
                [_normalise_name(t) for t in entities.get("topics", [])]
            ),
        }

        author = record.get("author")

        normalised.append({
            "id": stable_id,
            "title": _normalise_name(title),
            "url": url,
            "published_at": canonical_date,
            "source_name": _normalise_name(source_name),
            "author": _normalise_name(author) if author else None,
            "summary": record.get("summary"),
            "entities": normalised_entities,
            "relations": _normalise_relations(record.get("relations", []), i),
        })

    print(f"[NORMALISE] Normalised {len(normalised)} records.")
    return normalised