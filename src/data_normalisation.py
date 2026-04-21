import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

from src.config import CONFIG
from src.govuk_scope import govuk_result_is_in_scope

CONTROLLED_PREDICATES = CONFIG["CONTROLLED_PREDICATES"]

MOJIBAKE_MARKERS = ("\u00c3", "\u00c2", "\u00e2\u20ac")
MOJIBAKE_REPLACEMENTS = {
    "\u00e2\u20ac\u2122": "\u2019",
    "\u00e2\u20ac\u2018": "\u2018",
    "\u00e2\u20ac\u0153": "\u201c",
    "\u00e2\u20ac\x9d": "\u201d",
    "\u00e2\u20ac\u201c": "\u2013",
    "\u00e2\u20ac\u201d": "\u2014",
    "\u00e2\u20ac\u00a6": "\u2026",
    "\u00c2\u00a0": " ",
}


def mojibake_score(text):
    return sum(str(text).count(marker) for marker in MOJIBAKE_MARKERS)


def repair_common_mojibake(text):
    repaired = str(text)
    best = repaired
    best_score = mojibake_score(repaired)

    for _ in range(2):
        try:
            candidate = repaired.encode("latin-1").decode("utf-8")
        except (UnicodeEncodeError, UnicodeDecodeError):
            break
        candidate_score = mojibake_score(candidate)
        if candidate_score < best_score:
            best = candidate
            best_score = candidate_score
            repaired = candidate
        else:
            break

    for broken, fixed in MOJIBAKE_REPLACEMENTS.items():
        best = best.replace(broken, fixed)

    return best


def build_stable_id(url, title, published_at):
    source = url if url else f"{title}{published_at}"
    return hashlib.sha256(source.encode()).hexdigest()[:16]


def normalise_name(name):
    if not name:
        return ""
    repaired = repair_common_mojibake(name)
    return " ".join(str(repaired).strip().split())


def canonicalise_date(date_str):
    if not date_str:
        raise ValueError(f"Cannot parse date: {date_str!r}")

    for fmt in ("%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
        try:
            dt = datetime.strptime(date_str, fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        except ValueError:
            continue
    raise ValueError(f"Cannot parse date: {date_str!r}")


def is_within_configured_window(date_str):
    canonical = canonicalise_date(str(date_str))
    date_only = canonical[:10]
    return CONFIG["date_start"] <= date_only <= CONFIG["date_end"]


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


def _first_present(mapping, keys, default=None):
    for key in keys:
        value = mapping.get(key)
        if value not in (None, ""):
            return value
    return default


def _coerce_iterable(value):
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _normalise_search_result_url(value):
    value = normalise_name(value)
    if not value:
        return ""
    if value.startswith("http://") or value.startswith("https://"):
        return value
    if value.startswith("/"):
        return f"https://www.gov.uk{value}"
    return f"https://www.gov.uk/{value.lstrip('/')}"


def _extract_text_fragments(value):
    if isinstance(value, str):
        cleaned = normalise_name(value)
        return [cleaned] if cleaned else []
    if isinstance(value, dict):
        fragments = []
        for item in value.values():
            fragments.extend(_extract_text_fragments(item))
        return fragments
    if isinstance(value, list):
        fragments = []
        for item in value:
            fragments.extend(_extract_text_fragments(item))
        return fragments
    return []


def normalise_parliament_records(raw_data):
    response = raw_data.get("response") or {}
    candidates = []

    if isinstance(response, dict):
        if isinstance(response.get("results"), list):
            candidates = response["results"]
        elif isinstance(response.get("items"), list):
            candidates = response["items"]
        elif isinstance(response.get("value"), list):
            candidates = response["value"]
    elif isinstance(response, list):
        candidates = response

    normalised = []
    for item in candidates:
        if not isinstance(item, dict):
            continue

        title = normalise_name(
            _first_present(item, ["title", "name", "displayTitle", "sortTitle", "subject"])
        )
        url = _first_present(item, ["url", "webUrl", "link", "uri"], "") or ""
        published_at = _first_present(
            item,
            [
                "date",
                "publishedAt",
                "published_at",
                "startDate",
                "sittingDate",
                "value",
                "updated",
            ],
        )

        if not title or not url or not published_at:
            continue
        if not is_valid_url(url):
            continue
        if not is_within_configured_window(published_at):
            continue

        tags = deduplicate_list(
            _extract_text_fragments(item.get("tags"))
            + _extract_text_fragments(item.get("topics"))
            + _extract_text_fragments(item.get("keywords"))
            + _extract_text_fragments(item.get("houses"))
        )

        summary = normalise_name(
            _first_present(item, ["summary", "description", "snippet", "excerpt"], "")
        )
        content_fragments = []
        for key in ("content", "body", "abstract", "resultDescription", "description"):
            content_fragments.extend(_extract_text_fragments(item.get(key)))
        content = normalise_name(" ".join(content_fragments)) or None

        body_name = normalise_name(
            _first_present(
                item,
                ["house", "houseName", "chamber", "section", "category", "bodyName"],
                "",
            )
        )

        normalised.append(
            {
                "id": build_stable_id(url, title, published_at),
                "source_system": "parliament",
                "source_name": "UK Parliament",
                "title": title,
                "url": url,
                "published_at": canonicalise_date(str(published_at)),
                "updated_at": None,
                "author": None,
                "section": body_name or None,
                "summary": summary or None,
                "content": content,
                "tags": tags,
                "word_count": count_words(content or summary or title),
                "raw_article_type_hint": "NewsArticle",
            }
        )

    print(f"[NORMALISE] Normalised {len(normalised)} Parliament source records.")
    return normalised


def normalise_govuk_records(raw_data):
    response = raw_data.get("response") or {}
    results = response.get("results", []) if isinstance(response, dict) else []
    normalised = []

    for item in results:
        if not isinstance(item, dict):
            continue

        title = normalise_name(_first_present(item, ["title"]))
        url = _normalise_search_result_url(_first_present(item, ["link", "base_path", "url"], ""))
        published_at = _first_present(item, ["public_timestamp", "timestamp", "updated_at"])

        if not title or not url or not published_at:
            continue
        if not is_valid_url(url):
            continue
        if not is_within_configured_window(published_at):
            continue
        if not govuk_result_is_in_scope(item):
            continue

        format_label = normalise_name(_first_present(item, ["format"]))
        document_type = normalise_name(_first_present(item, ["document_type"]))
        section = format_label or document_type or None

        tags = deduplicate_list(
            [format_label, document_type]
            + _extract_text_fragments(item.get("organisations"))
            + _extract_text_fragments(item.get("government_name"))
        )

        summary = normalise_name(_first_present(item, ["description"], ""))
        content = summary or None

        normalised.append(
            {
                "id": build_stable_id(url, title, published_at),
                "source_system": "govuk",
                "source_name": "GOV.UK",
                "title": title,
                "url": url,
                "published_at": canonicalise_date(str(published_at)),
                "updated_at": None,
                "author": None,
                "section": section,
                "summary": summary or None,
                "content": content,
                "tags": tags,
                "word_count": count_words(content or title),
                "raw_article_type_hint": "NewsArticle",
            }
        )

    print(f"[NORMALISE] Normalised {len(normalised)} GOV.UK source records.")
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
        if not is_within_configured_window(published_at):
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
    guardian_records = normalise_guardian_articles(sources.get("guardian") or {})
    parliament_records = normalise_parliament_records(sources.get("parliament") or {})
    govuk_records = normalise_govuk_records(sources.get("govuk") or {})
    combined = guardian_records + parliament_records + govuk_records

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
