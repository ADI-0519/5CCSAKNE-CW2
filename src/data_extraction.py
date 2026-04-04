# Code to extract relevant information from the collected data

import re
import hashlib

from src.config import CONFIG

# ---------------------------------------------------------------------------
# Org suffix pattern used to detect organization names
# ---------------------------------------------------------------------------
_ORG_SUFFIX = (
    r"(?:Inc|Corp|Corporation|Ltd|LLC|Co|Group|Technologies|Systems|Solutions|Labs|"
    r"AI|Tech|Institute|Foundation|University|Agency|Bureau|Department|"
    r"Ministry|Committee|Commission|Organization|Organisation|Association|"
    r"Society|Alliance|Coalition|Network|Platform|Media|News|Times|Post|"
    r"Journal|Review|Report)"
)
_ORG_PATTERN = re.compile(
    r"\b([A-Z][a-zA-Z0-9]+(?:\s+[A-Z][a-zA-Z0-9]+)*\s+" + _ORG_SUFFIX + r"[.]?)\b"
)

# Two capitalized words: typical first-name last-name pattern
_PERSON_PATTERN = re.compile(r"\b([A-Z][a-z]+\s+[A-Z][a-z]+)\b")

# "in/at/from/near [Capitalized phrase]"
_LOCATION_PATTERN = re.compile(
    r"\b(?:in|at|from|near|across)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b"
)


def _stable_id(url, title, published_at):
    source = url if url else f"{title}{published_at}"
    return hashlib.sha256(source.encode()).hexdigest()[:16]


def _extract_technologies(text):
    text_lower = text.lower()
    found = set()
    for term in CONFIG["TECHNOLOGY_KEYWORDS"]:
        if term.lower() in text_lower:
            found.add(term)
    return sorted(found)


def _extract_topics(text):
    text_lower = text.lower()
    found = set()
    for term in CONFIG["TOPIC_KEYWORDS"]:
        if term.lower() in text_lower:
            found.add(term)
    return sorted(found)


def _extract_organizations(text):
    found = set()
    for m in _ORG_PATTERN.finditer(text):
        org = m.group(1).strip()
        if org not in CONFIG["ENTITY_STOPLIST"]:
            found.add(org)
    return sorted(found)


def _extract_people(text):
    entity_stoplist = CONFIG["ENTITY_STOPLIST"]
    person_stoplist = CONFIG["PERSON_STOPLIST"]
    found = set()
    for m in _PERSON_PATTERN.finditer(text):
        name = m.group(1)
        if name not in entity_stoplist and name not in person_stoplist:
            found.add(name)
    return sorted(found)


def _extract_locations(text):
    entity_stoplist = CONFIG["ENTITY_STOPLIST"]
    found = set()
    for m in _LOCATION_PATTERN.finditer(text):
        loc = m.group(1)
        if loc not in entity_stoplist:
            found.add(loc)
    return sorted(found)


def _generate_relations(article_id, entities):
    relations = []

    # Article mentions every detected entity
    for tech in entities["technologies"]:
        relations.append({"subject": article_id, "predicate": "mentions", "object": tech})
    for org in entities["organizations"]:
        relations.append({"subject": article_id, "predicate": "mentions", "object": org})
    for person in entities["people"]:
        relations.append({"subject": article_id, "predicate": "mentions", "object": person})
    for loc in entities["locations"]:
        relations.append({"subject": article_id, "predicate": "located_in", "object": loc})
    for topic in entities["topics"]:
        relations.append({"subject": article_id, "predicate": "mentions", "object": topic})

    # Co-occurrence signal: an org that appears alongside a technology likely uses it
    for org in entities["organizations"]:
        for tech in entities["technologies"]:
            relations.append({"subject": org, "predicate": "uses_technology", "object": tech})

    return relations


def extract_relevant_information(raw_data):
    print("[EXTRACT] Starting extraction stage...")

    if not raw_data:
        raise ValueError("[EXTRACT] No data provided to extraction stage.")

    articles = raw_data.get("articles", [])
    if not articles:
        raise ValueError("[EXTRACT] No articles found in raw data.")

    extracted = []
    for i, article in enumerate(articles):
        try:
            url = article.get("url") or ""
            title = article.get("title") or ""
            published_at = article.get("publishedAt") or ""

            # Concatenate all text for entity detection
            full_text = " ".join(filter(None, [
                title,
                article.get("description") or "",
                article.get("content") or "",
            ]))

            article_id = _stable_id(url, title, published_at)

            entities = {
                "organizations": _extract_organizations(full_text),
                "people": _extract_people(full_text),
                "locations": _extract_locations(full_text),
                "technologies": _extract_technologies(full_text),
                "topics": _extract_topics(full_text),
            }

            relations = _generate_relations(article_id, entities)

            extracted.append({
                "id": article_id,
                "title": title,
                "url": url,
                "published_at": published_at,
                "source_name": (article.get("source") or {}).get("name") or "",
                "author": article.get("author"),
                "summary": article.get("description") or article.get("content"),
                "entities": entities,
                "relations": relations,
            })
        except Exception as e:
            raise RuntimeError(f"[EXTRACT] Failed processing article {i}: {e}") from e

    print(f"[EXTRACT] Extracted {len(extracted)} records.")
    return extracted