import hashlib
import json
import os
import re
import time
from pathlib import Path

from src.config import CONFIG

VALID_SENTIMENTS = {"Positive", "Negative", "Neutral"}
VALID_ARTICLE_TYPES = {"NewsArticle", "OpinionArticle", "BreakingNewsArticle"}
VALID_EVENT_TYPES = {
    "PolicyEvent",
    "ParliamentaryEvent",
    "GovernmentPolicyEvent",
    "ParliamentaryDebate",
    "MinisterialStatement",
}

EXTRACTION_RESPONSE_FORMAT = {
    "type": "json_schema",
    "name": "article_extraction",
    "strict": True,
    "schema": {
        "type": "object",
        "properties": {
            "people": {"type": "array", "items": {"type": "string"}},
            "organizations": {"type": "array", "items": {"type": "string"}},
            "locations": {"type": "array", "items": {"type": "string"}},
            "topics": {"type": "array", "items": {"type": "string"}},
            "politicians": {"type": "array", "items": {"type": "string"}},
            "political_parties": {"type": "array", "items": {"type": "string"}},
            "government_bodies": {"type": "array", "items": {"type": "string"}},
            "sentiment": {"type": "string", "enum": sorted(VALID_SENTIMENTS)},
            "article_type": {"type": "string", "enum": sorted(VALID_ARTICLE_TYPES)},
            "events": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "type": {"type": "string", "enum": sorted(VALID_EVENT_TYPES)},
                        "date": {"type": ["string", "null"]},
                        "location": {"type": ["string", "null"]},
                    },
                    "required": ["name", "type", "date", "location"],
                    "additionalProperties": False,
                },
            },
        },
        "required": [
            "people",
            "organizations",
            "locations",
            "topics",
            "politicians",
            "political_parties",
            "government_bodies",
            "sentiment",
            "article_type",
            "events",
        ],
        "additionalProperties": False,
    },
}


def slug_text(text):
    return re.sub(r"[^a-zA-Z0-9_-]", "_", str(text).strip()) or "item"


def build_cache_path(stage, cache_key):
    cache_dir = Path(CONFIG["OPENAI_CACHE_DIR"]) / stage
    slug = slug_text(cache_key)
    if len(slug) > 200:
        slug = hashlib.sha256(cache_key.encode()).hexdigest()
    return cache_dir / f"{slug}.json"


def load_cache_payload(path):
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def save_cache_payload(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def get_openai_unavailable_reason():
    if os.getenv("PYTEST_CURRENT_TEST") and os.getenv("ALLOW_OPENAI_IN_TESTS") != "1":
        return "OpenAI disabled during pytest"

    api_key = CONFIG.get("OPENAI_API_KEY")
    if not api_key:
        return "OPENAI_API_KEY is missing"

    try:
        from openai import OpenAI  # noqa: F401
    except ImportError:
        return "openai package is not installed in this Python environment"

    return None


def build_openai_client():
    unavailable_reason = get_openai_unavailable_reason()
    if unavailable_reason is not None:
        return None

    from openai import OpenAI

    return OpenAI(api_key=CONFIG["OPENAI_API_KEY"])


def response_to_json(response):
    output_text = getattr(response, "output_text", None)
    if output_text:
        return json.loads(output_text)

    output_parsed = getattr(response, "output_parsed", None)
    if isinstance(output_parsed, dict):
        return output_parsed

    output_items = getattr(response, "output", None)
    if isinstance(output_items, list):
        for item in output_items:
            if not isinstance(item, dict) and hasattr(item, "model_dump"):
                item = item.model_dump()

            if not isinstance(item, dict):
                continue

            content_items = item.get("content", [])
            for content in content_items:
                if not isinstance(content, dict) and hasattr(content, "model_dump"):
                    content = content.model_dump()

                if not isinstance(content, dict):
                    continue

                parsed_payload = content.get("parsed")
                if isinstance(parsed_payload, dict):
                    return parsed_payload

                text_value = content.get("text")
                if isinstance(text_value, str) and text_value.strip():
                    try:
                        return json.loads(text_value)
                    except json.JSONDecodeError:
                        continue

    if hasattr(response, "model_dump"):
        dumped = response.model_dump()

        if isinstance(dumped, dict):
            if isinstance(dumped.get("output_parsed"), dict):
                return dumped["output_parsed"]

            dumped_output = dumped.get("output")
            if isinstance(dumped_output, list):
                for item in dumped_output:
                    if not isinstance(item, dict):
                        continue
                    for content in item.get("content", []):
                        if not isinstance(content, dict):
                            continue
                        parsed_payload = content.get("parsed")
                        if isinstance(parsed_payload, dict):
                            return parsed_payload
                        text_value = content.get("text")
                        if isinstance(text_value, str) and text_value.strip():
                            try:
                                return json.loads(text_value)
                            except json.JSONDecodeError:
                                continue

        return dumped

    raise ValueError("OpenAI response did not contain structured output text.")


def request_structured_output(instructions, user_input, response_format):
    client = build_openai_client()
    if client is None:
        print(f"[OPENAI] Structured output skipped: {get_openai_unavailable_reason()}")
        return None

    last_exc = None
    for attempt in range(3):
        try:
            response = client.responses.create(
                model=CONFIG["OPENAI_MODEL"],
                instructions=instructions,
                input=user_input,
                text={"format": response_format},
                timeout=CONFIG["OPENAI_REQUEST_TIMEOUT_SECONDS"],
            )
            return response_to_json(response)
        except Exception as exc:
            last_exc = exc
            if attempt < 2:
                time.sleep(2**attempt)  # 1s, then 2s

    raise last_exc


def validate_event_payload(event):
    if not isinstance(event, dict):
        return None

    name = str(event.get("name") or "").strip()
    event_type = str(event.get("type") or "").strip()
    date = event.get("date")
    location = event.get("location")

    if not name or event_type not in VALID_EVENT_TYPES:
        return None

    if date is not None:
        date = str(date).strip() or None
    if location is not None:
        location = str(location).strip() or None

    return {
        "name": name,
        "type": event_type,
        "date": date,
        "location": location,
    }


def validate_extraction_payload(payload):
    if not isinstance(payload, dict):
        return None

    sentiment = str(payload.get("sentiment") or "").strip()
    article_type = str(payload.get("article_type") or "").strip()
    if sentiment not in VALID_SENTIMENTS or article_type not in VALID_ARTICLE_TYPES:
        return None

    validated_events = []
    for event in payload.get("events", []):
        validated_event = validate_event_payload(event)
        if validated_event is not None:
            validated_events.append(validated_event)

    validated = {
        "people": [str(item).strip() for item in payload.get("people", []) if str(item).strip()],
        "organizations": [
            str(item).strip() for item in payload.get("organizations", []) if str(item).strip()
        ],
        "locations": [
            str(item).strip() for item in payload.get("locations", []) if str(item).strip()
        ],
        "topics": [str(item).strip() for item in payload.get("topics", []) if str(item).strip()],
        "politicians": [
            str(item).strip() for item in payload.get("politicians", []) if str(item).strip()
        ],
        "political_parties": [
            str(item).strip() for item in payload.get("political_parties", []) if str(item).strip()
        ],
        "government_bodies": [
            str(item).strip() for item in payload.get("government_bodies", []) if str(item).strip()
        ],
        "sentiment": sentiment,
        "article_type": article_type,
        "events": validated_events,
    }
    return validated


def summarize_invalid_payload(payload):
    if payload is None:
        return "payload was None"
    if not isinstance(payload, dict):
        return f"payload type was {type(payload).__name__}"

    keys = sorted(payload.keys())
    summary = [f"keys={keys}"]
    if "sentiment" in payload:
        summary.append(f"sentiment={payload.get('sentiment')!r}")
    if "article_type" in payload:
        summary.append(f"article_type={payload.get('article_type')!r}")
    if "article_types" in payload:
        summary.append(f"article_types={payload.get('article_types')!r}")
    if "events" in payload and isinstance(payload.get("events"), list):
        summary.append(f"events={len(payload.get('events', []))}")
    return ", ".join(summary)


def maybe_extract_article_with_openai(article, article_text, heuristic_result):
    cache_key = article.get("id") or article.get("url") or article.get("title") or "article"
    cache_path = build_cache_path("extraction", cache_key)
    cached = load_cache_payload(cache_path)
    if cached is not None:
        validated_cached = validate_extraction_payload(cached)
        if validated_cached is not None:
            return validated_cached

    instructions = (
        "You are an information extraction assistant for a knowledge graph about current UK "
        "politics and policy news. Use only evidence from the supplied article. Do not invent "
        "entities or events. Return only ontology-aligned JSON."
    )
    user_input = json.dumps(
        {
            "project_scope": CONFIG["project_scope"],
            "allowed_topics": sorted(CONFIG["TOPIC_GROUPS"].keys()),
            "article": {
                "title": article.get("title"),
                "summary": article.get("summary"),
                "content": article.get("content"),
                "section": article.get("section"),
                "tags": article.get("tags") or [],
                "published_at": article.get("published_at"),
            },
            "heuristic_result": heuristic_result,
            "article_text": article_text,
        },
        ensure_ascii=False,
    )

    try:
        result = request_structured_output(
            instructions=instructions,
            user_input=user_input,
            response_format=EXTRACTION_RESPONSE_FORMAT,
        )
    except Exception as exc:
        print(f"[OPENAI] Extraction request failed: {exc}")
        return None

    validated_result = validate_extraction_payload(result)
    if validated_result is None:
        print(
            "[OPENAI] Extraction response was invalid and has been ignored: "
            f"{summarize_invalid_payload(result)}"
        )
        return None

    save_cache_payload(cache_path, validated_result)
    return validated_result
