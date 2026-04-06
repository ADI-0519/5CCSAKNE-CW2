import json
import os
import re
from pathlib import Path

from src.config import CONFIG

VALID_SENTIMENTS = {"Positive", "Negative", "Neutral"}
VALID_ARTICLE_TYPES = {"NewsArticle", "OpinionArticle", "BreakingNewsArticle"}
VALID_EVENT_TYPES = {"NewsEvent", "PoliticalEvent", "EconomicEvent"}

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

COMPLETION_RESPONSE_FORMAT = {
    "type": "json_schema",
    "name": "article_completion",
    "strict": True,
    "schema": {
        "type": "object",
        "properties": {
            "sentiment": {"type": "string", "enum": sorted(VALID_SENTIMENTS)},
            "section": {"type": "string"},
            "article_types": {
                "type": "array",
                "items": {"type": "string", "enum": sorted(VALID_ARTICLE_TYPES)},
            },
            "additional_topics": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["sentiment", "section", "article_types", "additional_topics"],
        "additionalProperties": False,
    },
}


def _slug(text):
    return re.sub(r"[^a-zA-Z0-9_-]", "_", str(text).strip()) or "item"


def _cache_path(stage, cache_key):
    cache_dir = Path(CONFIG["OPENAI_CACHE_DIR"]) / stage
    return cache_dir / f"{_slug(cache_key)}.json"


def _load_cache(path):
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _save_cache(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _build_client():
    if os.getenv("PYTEST_CURRENT_TEST") and os.getenv("ALLOW_OPENAI_IN_TESTS") != "1":
        return None

    api_key = CONFIG.get("OPENAI_API_KEY")
    if not api_key:
        return None

    try:
        from openai import OpenAI
    except ImportError:
        return None

    return OpenAI(api_key=api_key)


def _response_to_json(response):
    output_text = getattr(response, "output_text", None)
    if output_text:
        return json.loads(output_text)

    if hasattr(response, "model_dump"):
        dumped = response.model_dump()
        return json.loads(json.dumps(dumped))

    raise ValueError("OpenAI response did not contain structured output text.")


def _request_structured_output(instructions, user_input, response_format):
    client = _build_client()
    if client is None:
        return None

    response = client.responses.create(
        model=CONFIG["OPENAI_MODEL"],
        instructions=instructions,
        input=user_input,
        text={"format": response_format},
    )
    return _response_to_json(response)


def maybe_extract_article_with_openai(article, article_text, heuristic_result):
    cache_key = article.get("id") or article.get("url") or article.get("title") or "article"
    cache_path = _cache_path("extraction", cache_key)
    cached = _load_cache(cache_path)
    if cached is not None:
        return cached

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
        result = _request_structured_output(
            instructions=instructions,
            user_input=user_input,
            response_format=EXTRACTION_RESPONSE_FORMAT,
        )
    except Exception as exc:
        print(f"[OPENAI] Extraction request failed: {exc}")
        return None

    if result is not None:
        _save_cache(cache_path, result)
    return result


def maybe_complete_article_with_openai(article_key, article_payload, heuristic_result):
    cache_path = _cache_path("completion", article_key)
    cached = _load_cache(cache_path)
    if cached is not None:
        return cached

    instructions = (
        "You are completing a UK politics and policy news knowledge graph. Use only the supplied "
        "headline, description, and current KG context. Do not invent facts. Return only "
        "JSON-compatible ontology-aligned updates."
    )
    user_input = json.dumps(
        {
            "project_scope": CONFIG["project_scope"],
            "allowed_topics": sorted(CONFIG["TOPIC_GROUPS"].keys()),
            "article": article_payload,
            "heuristic_result": heuristic_result,
        },
        ensure_ascii=False,
    )

    try:
        result = _request_structured_output(
            instructions=instructions,
            user_input=user_input,
            response_format=COMPLETION_RESPONSE_FORMAT,
        )
    except Exception as exc:
        print(f"[OPENAI] Completion request failed: {exc}")
        return None

    if result is not None:
        _save_cache(cache_path, result)
    return result
