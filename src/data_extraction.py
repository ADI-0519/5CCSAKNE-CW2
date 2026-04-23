import hashlib
import re
from collections import defaultdict
from datetime import date
from functools import lru_cache

from src.config import CONFIG
from src.data_normalisation import normalise_collected_sources, normalise_name
from src.domain_knowledge import (
    GOVERNMENT_BODY_NAME_SET,
    POLITICAL_PARTY_NAME_SET,
    POLITICIAN_NAME_SET,
    TOPIC_NAME_SET,
    UK_LOCATION_NAME_SET,
    canonicalise_government_body_name,
    canonicalise_political_party_name,
    classify_known_government_bodies,
    classify_known_political_parties,
    classify_known_politicians,
    has_ministerial_statement_signal,
    infer_government_bodies_from_text,
)
from src.extraction_support import (
    GENERIC_EVENT_NAMES,
    derive_event_names,
    event_context_signals,
    is_historical_election_reference,
    phrase_in_text,
    phrase_match_count,
)
from src.openai_client import maybe_extract_article_with_openai

ORG_SUFFIX = (
    r"(?:Party|Office|Treasury|Parliament|Commons|Lords|Ministry|Department|"
    r"Cabinet|Council|Commission|Government|News|Media|Times|Post|Journal|"
    r"Review|Guardian|BBC)"
)
ORG_PATTERN = re.compile(
    r"\b([A-Z][a-zA-Z0-9&'\-]+(?:\s+[A-Z][a-zA-Z0-9&'\-]+)*\s+" + ORG_SUFFIX + r")\b"
)
PERSON_PATTERN = re.compile(r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b")
LOCATION_PATTERN = re.compile(
    r"\b(?:in|at|from|across|throughout|near)\s+"
    r"([A-Z][a-zA-Z'\-]+(?:\s+[A-Z][a-zA-Z'\-]+)?)\b"
)

CANONICAL_LOCATION_NAMES = UK_LOCATION_NAME_SET
KNOWN_GOVERNMENT_BODY_NAMES = GOVERNMENT_BODY_NAME_SET
KNOWN_POLITICAL_PARTY_NAMES = POLITICAL_PARTY_NAME_SET
KNOWN_POLITICIAN_NAMES = POLITICIAN_NAME_SET
KNOWN_TOPIC_NAMES = TOPIC_NAME_SET
CANONICAL_LEXICONS = CONFIG["CANONICAL_LEXICONS"]
FILTER_RULES = CONFIG["FILTER_RULES"]
NLP_CONFIG = CONFIG["NLP_CONFIG"]


@lru_cache(maxsize=1)
def get_spacy_nlp():
    if not NLP_CONFIG["enable_spacy_ner"]:
        return None

    try:
        import spacy
    except ImportError:
        return None

    try:
        return spacy.load(NLP_CONFIG["spacy_model_name"])
    except Exception as exc:
        print(f"[NLP] spacy model {NLP_CONFIG['spacy_model_name']!r} unavailable: {exc}")
        return None


def extract_spacy_entities(text):
    nlp = get_spacy_nlp()
    if nlp is None or not text.strip():
        return {"people": [], "organizations": [], "locations": []}

    people = set()
    organizations = set()
    locations = set()

    doc = nlp(text)
    for ent in getattr(doc, "ents", []):
        label = str(getattr(ent, "label_", "")).upper()
        value = normalise_label(getattr(ent, "text", ""))
        if not value:
            continue
        if label == "PERSON":
            people.add(value)
        elif label == "ORG":
            organizations.add(value)
        elif label in {"GPE", "LOC"}:
            locations.add(value)

    return {
        "people": unique_sorted(people),
        "organizations": unique_sorted(organizations),
        "locations": unique_sorted(locations),
    }


def build_article_id(url, title, published_at):
    source = url if url else f"{title}{published_at}"
    return hashlib.sha256(source.encode()).hexdigest()[:16]


def normalise_label(text):
    return normalise_name(text)


def build_article_text(article):
    parts = [
        article.get("title"),
        article.get("summary"),
        article.get("content"),
        article.get("section"),
        " ".join(article.get("tags") or []),
    ]
    return " ".join(normalise_label(part) for part in parts if part)


def unique_sorted(values):
    cleaned = []
    seen = set()
    for value in values:
        label = normalise_label(value)
        if label and label not in seen:
            seen.add(label)
            cleaned.append(label)
    return sorted(cleaned)


def is_generic_fallback_event_name(name):
    return normalize_event_name(name) in GENERIC_EVENT_NAMES


def mark_event_candidate_flags(event):
    enriched = dict(event)
    enriched["is_generic_fallback"] = bool(event.get("is_generic_fallback")) or (
        is_generic_fallback_event_name(event.get("name"))
    )
    return enriched


def find_named_matches(text, candidates):
    text_lower = text.lower()
    matches = []
    for candidate in candidates:
        pattern = r"(?<![a-z0-9])" + re.escape(candidate.lower()) + r"(?![a-z0-9])"
        if re.search(pattern, text_lower):
            matches.append(candidate)
    return unique_sorted(matches)


def extract_topics(text, tags=None, section=None, source_system=None):
    text_lower = text.lower()
    topic_scores = defaultdict(int)

    for topic_name, hints in CANONICAL_LEXICONS["topic_groups"].items():
        hits = sum(phrase_match_count(text_lower, hint) for hint in hints)
        if hits:
            topic_scores[topic_name] += hits

    for tag in tags or []:
        tag_lower = tag.lower()
        for topic_name, hints in CANONICAL_LEXICONS["topic_groups"].items():
            if phrase_in_text(tag_lower, topic_name):
                topic_scores[topic_name] += 3
            tag_hits = sum(phrase_match_count(tag_lower, hint) for hint in hints)
            if tag_hits:
                topic_scores[topic_name] += min(tag_hits, 2)

    if section:
        section_lower = section.lower()
        if "politics" in section_lower:
            topic_scores["Politics"] += 2
        if section_lower in FILTER_RULES["opinion_section_names"]:
            topic_scores["Opinion"] += 2

    if not topic_scores:
        return []

    ranked = sorted(topic_scores.items(), key=lambda item: (-item[1], item[0]))
    min_score = 1 if source_system in {"parliament", "govuk"} else 2
    selected = []
    for topic_name, score in ranked:
        if score < min_score:
            continue
        selected.append(topic_name)
        if len(selected) == 3:
            break

    return selected


def extract_people(text, spacy_candidates=None):
    entity_stoplist = CONFIG["ENTITY_STOPLIST"]
    person_stoplist = CONFIG["PERSON_STOPLIST"]
    blocked_person_words = {
        "Office",
        "Council",
        "Government",
        "Parliament",
        "Policy",
        "Support",
        "Returns",
        "Committee",
        "Department",
        "Ministry",
        "Treasury",
        "Party",
        "Commission",
        "Agency",
        "Bill",
        "Statement",
        "Budget",
        "Review",
        "Court",
        "News",
        "Media",
        "Asylum",
        "Immigration",
        "Politics",
        "Political",
        "Election",
        "Elections",
        "Labour",
        "Reform",
        "Brexit",
        "Opinion",
        "Weekly",
        "Exclusive",
        "World",
        "National",
        "European",
        "International",
        "Comment",
        "Analysis",
        "Local",
        "British",
        "When",
        "While",
        "From",
    }
    found = set(find_named_matches(text, KNOWN_POLITICIAN_NAMES))
    found.update(spacy_candidates or [])

    for match in PERSON_PATTERN.finditer(text):
        name = normalise_label(match.group(1))
        if name in entity_stoplist or name in person_stoplist:
            continue
        if any(char.isdigit() for char in name):
            continue
        parts = name.split()
        if len(parts) < 2 or len(parts) > 3:
            continue
        if any(len(part) <= 2 for part in parts):
            continue
        if any(
            part.lower() in {"the", "and", "for", "of", "to", "in", "on", "as"} for part in parts
        ):
            continue
        if parts[0].endswith("ing"):
            continue
        if parts[0] in CONFIG["EXTRACTION_PERSON_BLOCKED_PREFIXES"]:
            continue
        if any(part in blocked_person_words for part in parts):
            continue
        found.add(name)

    return sanitize_people(found)


def extract_locations(text, spacy_candidates=None):
    text_lower = text.lower()
    found = set(find_named_matches(text, CANONICAL_LOCATION_NAMES))
    found.update(spacy_candidates or [])

    for match in LOCATION_PATTERN.finditer(text):
        location = normalise_label(match.group(1))
        if not is_location_candidate_valid(location):
            continue
        if location not in CANONICAL_LOCATION_NAMES and phrase_match_count(text_lower, location.lower()) < 2:
            continue
        found.add(location)

    return sanitize_locations(found)


_ORG_LEAD_IN = {"As", "From", "For", "But", "And", "By", "In", "On", "With", "Via"}
_EVENT_TYPE_PRIORITY = {
    "PolicyEvent": 0,
    "ParliamentaryEvent": 1,
    "GovernmentPolicyEvent": 1,
    "ParliamentaryDebate": 2,
    "MinisterialStatement": 2,
}


def is_location_candidate_valid(location):
    candidate = normalise_label(location)
    if not candidate:
        return False

    if (
        candidate in CONFIG["ENTITY_STOPLIST"]
        or candidate in CONFIG["EXTRACTION_LOCATION_BLOCKLIST"]
    ):
        return False

    tokens = candidate.split()
    canonical_locations = CANONICAL_LOCATION_NAMES
    if candidate not in canonical_locations and len(tokens) == 1 and len(tokens[0]) <= 2:
        return False
    if any(token in CONFIG["EXTRACTION_LOCATION_STOPWORDS"] for token in tokens):
        return False
    if any(token in CONFIG["EXTRACTION_LOCATION_ROLE_TERMS"] for token in tokens):
        return False
    if any(token in CONFIG["EXTRACTION_ORG_NOISE_TERMS"] for token in tokens):
        return False
    if canonicalise_government_body_name(candidate) != candidate:
        return False
    if re.search(r"[A-Za-z]+\d", candidate):
        return False
    if candidate == candidate.lower() and candidate not in canonical_locations:
        return False

    candidate_lower = candidate.lower()
    if " mp" in candidate_lower or candidate_lower.endswith(" mps"):
        return False
    if any(party.lower() in candidate_lower for party in KNOWN_POLITICAL_PARTY_NAMES):
        return False

    return True


def label_token_set(value):
    return {token.lower() for token in normalise_label(value).split() if token}


def event_label_matches_context(label, context_text):
    candidate = normalise_label(label).lower()
    if not candidate:
        return False
    if phrase_in_text(context_text, candidate):
        return True
    token_set = label_token_set(label)
    context_tokens = {token for token in context_text.split() if token}
    return bool(token_set) and token_set.issubset(context_tokens)


def overlaps_blocked_entity(candidate, blocked_entities):
    candidate_tokens = label_token_set(candidate)
    if not candidate_tokens:
        return False

    for blocked in blocked_entities:
        blocked_tokens = label_token_set(blocked)
        if not blocked_tokens:
            continue
        if candidate_tokens == blocked_tokens:
            return True
        if candidate_tokens.issubset(blocked_tokens) or blocked_tokens.issubset(candidate_tokens):
            return True
    return False


def sanitize_people(people):
    cleaned = []
    for person in people:
        candidate = normalise_label(person)
        if not candidate:
            continue
        parts = candidate.split()
        if len(parts) < 2 or len(parts) > 3:
            continue
        if parts[0] in CONFIG["EXTRACTION_PERSON_BLOCKED_PREFIXES"]:
            continue
        if any(token in CONFIG["EXTRACTION_ORG_NOISE_TERMS"] for token in parts):
            continue
        cleaned.append(candidate)
    return unique_sorted(cleaned)


def sanitize_organizations(organizations):
    cleaned = []
    known_news_orgs = {"BBC News", "Financial Times", "Sky News", "The Guardian"}
    known_locations = CANONICAL_LOCATION_NAMES
    known_parties = KNOWN_POLITICAL_PARTY_NAMES

    for organization in organizations:
        candidate = normalise_label(organization)
        if not candidate:
            continue
        parts = candidate.split()
        if parts[0] in CONFIG["EXTRACTION_ORG_BLOCKED_PREFIXES"]:
            continue
        if (
            "News" in parts
            and candidate not in known_news_orgs
            and any(
                token in known_locations
                or token in known_parties
                or token in CONFIG["EXTRACTION_ORG_NOISE_TERMS"]
                for token in parts[:-1]
            )
        ):
            continue
        if sum(token in CONFIG["EXTRACTION_ORG_NOISE_TERMS"] for token in parts) >= 2:
            continue
        cleaned.append(candidate)
    return unique_sorted(cleaned)


def sanitize_locations(locations, blocked_entities=None):
    blocked = {
        normalise_label(item) for item in (blocked_entities or set()) if normalise_label(item)
    }
    canonical_locations = CANONICAL_LOCATION_NAMES
    cleaned = []
    for location in locations:
        candidate = normalise_label(location)
        if not is_location_candidate_valid(candidate):
            continue
        if candidate not in canonical_locations and overlaps_blocked_entity(candidate, blocked):
            continue
        cleaned.append(candidate)
    return unique_sorted(cleaned)


def choose_event_topics(event_name, context_text, record_topics):
    selected = []
    name_lower = normalise_label(event_name).lower()
    for topic in record_topics:
        hints = CANONICAL_LEXICONS["topic_groups"].get(topic, [])
        if phrase_in_text(context_text, topic.lower()) or any(
            phrase_in_text(context_text, hint) for hint in hints
        ):
            selected.append(topic)

    if selected:
        return unique_sorted(selected)
    if len(record_topics) == 1:
        return list(record_topics)
    if "Parliament" in record_topics and any(
        phrase in name_lower
        for phrase in ["debate", "pmqs", "prime minister's questions", "commons", "lords"]
    ):
        return ["Parliament"]
    return []


def choose_event_entities(event_name, context_text, candidates):
    selected = [
        candidate
        for candidate in candidates
        if event_label_matches_context(candidate, context_text)
    ]
    if selected:
        return unique_sorted(selected)
    if len(candidates) == 1:
        return list(candidates)
    return []


def choose_event_parliamentary_body(event_name, event_type, context_text, government_bodies):
    parliamentary_bodies = [
        body for body in government_bodies if body in CANONICAL_LEXICONS["parliamentary_body_names"]
    ]
    if not parliamentary_bodies:
        return None
    selected = choose_event_entities(event_name, context_text, parliamentary_bodies)
    if selected:
        return selected[0]
    if (
        event_type in {"ParliamentaryEvent", "ParliamentaryDebate"}
        and len(parliamentary_bodies) == 1
    ):
        return parliamentary_bodies[0]
    return None


def build_event_evidence_spans(article, event_name, event_type, event_topics, actors, bodies):
    parts = [article.get("title"), article.get("summary"), article.get("content")]
    fragments = []
    event_signals = {normalise_label(event_name).lower(), normalise_label(event_type).lower()}
    event_signals.update(normalise_label(topic).lower() for topic in event_topics)
    event_signals.update(normalise_label(actor).lower() for actor in actors)
    event_signals.update(normalise_label(body).lower() for body in bodies)

    for part in parts:
        cleaned = normalise_label(part)
        if not cleaned:
            continue
        cleaned_lower = cleaned.lower()
        if any(signal and signal in cleaned_lower for signal in event_signals):
            fragments.append(cleaned)
        if len(fragments) == 3:
            break

    return unique_sorted(fragments[:3])


def build_event_context_text(article, event_name, event_type, event_payload):
    parts = [
        normalise_label(event_name),
        normalise_label(event_type),
        normalise_label(article.get("title")),
        normalise_label(article.get("summary")),
        " ".join(normalise_label(tag) for tag in (article.get("tags") or [])),
    ]
    parts.extend(
        normalise_label(span) for span in (event_payload.get("evidence_spans") or []) if span
    )

    content = normalise_label(article.get("content"))
    if content:
        content_lower = content.lower()
        signal_terms = {
            normalise_label(event_name).lower(),
            normalise_label(event_type).lower(),
        }
        signal_terms.update(
            normalise_label(value).lower()
            for key in [
                "policy_topics",
                "political_actors",
                "government_bodies",
                "political_parties",
            ]
            for value in (event_payload.get(key) or [])
            if value
        )
        parliamentary_body = normalise_label(event_payload.get("parliamentary_body"))
        if parliamentary_body:
            signal_terms.add(parliamentary_body.lower())
        if any(term and term in content_lower for term in signal_terms):
            parts.append(content)

    return " ".join(part for part in parts if part).lower()


def normalise_confidence_value(value):
    lowered = str(value or "").strip().lower()
    return lowered if lowered in {"high", "medium", "low"} else ""


def resolve_event_extraction_method(event, used_heuristic_support):
    explicit_method = str(event.get("extraction_method") or "").strip().lower()
    if explicit_method in {"heuristic", "openai", "hybrid"}:
        return explicit_method

    source = str(event.get("source") or "").strip().lower()
    if source == "openai":
        return "hybrid" if used_heuristic_support else "openai"
    if source == "heuristic":
        return "heuristic"
    return "hybrid"


def choose_more_specific_event_type(current_type, event_name):
    inferred_type = infer_event_type(event_name)
    if _EVENT_TYPE_PRIORITY.get(inferred_type, -1) > _EVENT_TYPE_PRIORITY.get(current_type, -1):
        return inferred_type
    return current_type


def parse_iso_date(value):
    if not value:
        return None
    try:
        return date.fromisoformat(str(value)[:10])
    except ValueError:
        return None


def normalize_event_name(event_name):
    normalized = normalise_label(event_name)
    if not normalized:
        return ""
    lowered = normalized.lower()
    if lowered in {"prime minister's questions (pmqs)", "pmqs"}:
        return "Prime Minister's Questions"
    if lowered == "debate":
        return "Parliamentary Debate"
    return normalized


def govuk_supports_event_fallback(article):
    if article.get("source_system") != "govuk":
        return False

    section = normalise_label(article.get("section")).lower()
    if not section:
        return False
    if section in CONFIG["GOVUK_NON_EVENT_SECTIONS"]:
        return False
    return section in CONFIG["GOVUK_EVENT_FALLBACK_SECTIONS"]


def govuk_has_explicit_event_signal(article, text):
    if article.get("source_system") != "govuk":
        return False

    signal_text = " ".join(
        normalise_label(part).lower()
        for part in [article.get("title"), article.get("summary"), article.get("content")]
        if part
    )
    return any(
        phrase_in_text(signal_text, phrase)
        for phrase in CONFIG["GOVUK_EXPLICIT_EVENT_SIGNAL_TERMS"]
    )


def build_govuk_fallback_event(article, text, topics, locations):
    if article.get("source_system") != "govuk":
        return []
    section = normalise_label(article.get("section")).lower()
    if not section or section in CONFIG["GOVUK_NON_EVENT_SECTIONS"]:
        return []
    if section not in (
        set(CONFIG["GOVUK_EVENT_FALLBACK_SECTIONS"]) | {"policy_paper", "consultation"}
    ):
        return []
    if not govuk_has_explicit_event_signal(article, text):
        return []

    event_date = (article.get("published_at") or "")[:10] or None
    title = normalize_event_name(article.get("title"))
    if not title:
        return []

    text_lower = text.lower()
    event_type = "GovernmentPolicyEvent"
    if "statement" in title.lower() and has_ministerial_statement_signal(
        title, article.get("summary"), article.get("content")
    ):
        event_type = "MinisterialStatement"

    return [
        {
            "name": title,
            "type": event_type,
            "date": event_date,
            "location": choose_event_location(title, event_type, locations, text_lower, topics),
            "source": "heuristic",
        }
    ]


def event_date_is_plausible(article, event_date):
    parsed_event_date = parse_iso_date(event_date)
    if parsed_event_date is None:
        return event_date is None

    start_date = parse_iso_date(CONFIG["date_start"])
    end_date = parse_iso_date(CONFIG["date_end"])
    article_date = parse_iso_date(article.get("published_at"))
    if start_date and parsed_event_date < start_date:
        return False
    if end_date and parsed_event_date > end_date:
        return False
    if article_date and abs((parsed_event_date - article_date).days) > 31:
        return False
    return True


def extract_organisations(text, spacy_candidates=None):
    found = set(find_named_matches(text, KNOWN_POLITICAL_PARTY_NAMES))
    found.update(find_named_matches(text, KNOWN_GOVERNMENT_BODY_NAMES))
    found.update(spacy_candidates or [])

    for match in ORG_PATTERN.finditer(text):
        organisation = normalise_label(match.group(1))
        first_token = organisation.split()[0]
        if first_token in _ORG_LEAD_IN or first_token in CONFIG["EXTRACTION_ORG_BLOCKED_PREFIXES"]:
            continue
        if organisation not in CONFIG["ENTITY_STOPLIST"]:
            found.add(organisation)

    return sanitize_organizations(found)


def classify_politicians(people):
    return classify_known_politicians(people)


def classify_political_parties(organisations):
    return [
        canonicalise_political_party_name(name)
        for name in classify_known_political_parties(organisations)
    ]


def classify_government_bodies(organisations):
    return classify_known_government_bodies(organisations)


def classify_sentiment(text):
    text_lower = text.lower()
    positive = sum(
        phrase_match_count(text_lower, term) for term in CONFIG["POSITIVE_SENTIMENT_TERMS"]
    )
    negative = sum(
        phrase_match_count(text_lower, term) for term in CONFIG["NEGATIVE_SENTIMENT_TERMS"]
    )

    if negative > positive:
        return "Negative"
    if positive > negative:
        return "Positive"
    return "Neutral"


def classify_article_type(article, text):
    section = (article.get("section") or "").strip().lower()
    title = (article.get("title") or "").strip().lower()
    summary = (article.get("summary") or "").strip().lower()
    combined = f"{title} {summary} {text.lower()}"

    if (
        section in FILTER_RULES["opinion_section_names"]
        or "opinion" in title
        or "analysis" in title
    ):
        return "OpinionArticle"

    breaking_hits = sum(hint in combined for hint in FILTER_RULES["breaking_news_hints"])
    if title.startswith("live") or title.endswith("as it happened"):
        return "BreakingNewsArticle"
    if breaking_hits >= 2:
        return "BreakingNewsArticle"

    return "NewsArticle"


def infer_event_type(event_name):
    event_lower = event_name.lower()
    if (
        "debate" in event_lower
        or "prime minister's questions" in event_lower
        or "pmqs" in event_lower
    ):
        return "ParliamentaryDebate"
    if has_ministerial_statement_signal(event_name):
        return "MinisterialStatement"
    if "statement" in event_lower:
        return "GovernmentPolicyEvent"
    if "budget" in event_lower or "spending review" in event_lower:
        return "GovernmentPolicyEvent"
    if any(hint in event_lower for hint in CONFIG["ECONOMIC_EVENT_HINTS"]):
        return "GovernmentPolicyEvent"
    if any(
        phrase in event_lower for phrase in ["bill", "reading", "committee", "commons", "lords"]
    ):
        return "ParliamentaryEvent"
    return "PolicyEvent"


def preferred_event_location(locations, text_lower, topics):
    # parliamentary events almost always happen in London so prefer it when signal is clear
    if not locations:
        return None
    if (
        "Parliament" in topics
        or "parliament" in text_lower
        or "westminster" in text_lower
        or "house of commons" in text_lower
    ):
        if "Westminster" in locations:
            return "Westminster"
        if "London" in locations:
            return "London"
    return locations[0]


def choose_event_location(event_name, event_type, locations, text_lower, topics):
    candidates = sanitize_locations(locations)
    if not candidates:
        return None

    event_lower = event_name.lower()
    parliamentary_like = (
        event_type in {"ParliamentaryEvent", "ParliamentaryDebate"}
        or "parliament" in event_lower
        or "debate" in event_lower
        or "pmqs" in event_lower
        or "prime minister's questions" in event_lower
        or "Parliament" in topics
    )

    if parliamentary_like:
        if "Westminster" in candidates:
            return "Westminster"
        if "London" in candidates:
            return "London"
        filtered = [
            candidate
            for candidate in candidates
            if candidate not in CONFIG["EXTRACTION_BROAD_EVENT_LOCATIONS"]
            and (candidate in CANONICAL_LOCATION_NAMES or candidate.lower() in event_lower)
        ]
        if filtered:
            return filtered[0]
        return None

    if "London" in candidates:
        return "London"

    filtered = [
        candidate
        for candidate in candidates
        if candidate not in CONFIG["EXTRACTION_BROAD_EVENT_LOCATIONS"]
        and (candidate in CANONICAL_LOCATION_NAMES or candidate.lower() in event_lower)
    ]
    if filtered:
        return filtered[0]

    return candidates[0] if candidates[0] in CANONICAL_LOCATION_NAMES else None


def generic_event_fallback_blocked(article, article_type=None):
    # generic fallback tends to adds noise, not value for this source
    if article.get("source_system") == "parliament":
        return True

    title_lower = normalise_label(article.get("title")).lower()
    url_lower = str(article.get("url") or "").lower()
    section_lower = normalise_label(article.get("section")).lower()
    inferred_type = article_type or article.get("raw_article_type_hint")

    if inferred_type == "OpinionArticle" or section_lower in FILTER_RULES["opinion_section_names"]:
        return True

    if (
        "obituary" in title_lower
        or "q&a" in title_lower
        or "| letters" in title_lower
        or title_lower.startswith("live")
        or title_lower.endswith("as it happened")
        or "live/" in url_lower
    ):
        return True

    return False


def coerce_event_type_for_source(article, event_name, event_type, signals):
    if article.get("source_system") != "parliament":
        return event_type

    event_lower = event_name.lower()
    parliamentary_specific = any(
        phrase in event_lower
        for phrase in [
            "debate",
            "parliamentary vote",
            "committee",
            "prime minister's questions",
            "pmqs",
            "house of commons",
            "house of lords",
            "lords debate",
            "commons debate",
        ]
    )
    if parliamentary_specific:
        return event_type

    if "statement" in event_lower or (
        signals.get("parliament_written_statement")
        and (
            phrase_in_text(signals["salient_text_lower"], "statement")
            or phrase_in_text(signals["text_lower"], "statement")
        )
    ):
        return "MinisterialStatement"

    if event_type in {"PolicyEvent", "GovernmentPolicyEvent", "ParliamentaryEvent"}:
        return "ParliamentaryEvent"

    return event_type


def event_supported_by_context(event_name, signals):
    event_lower = event_name.lower()
    salient_text_lower = signals["salient_text_lower"]
    text_lower = signals["text_lower"]
    official_source = signals["official_source"]
    policy_signal = signals["policy_signal"]
    election_signal = signals["election_signal"]
    parliamentary_signal = signals["parliamentary_signal"]
    topics = signals["topics"]

    if event_lower in {"policy announcement", "ministerial statement"}:
        return policy_signal or official_source
    if "election" in event_lower:
        return election_signal and not is_historical_election_reference(
            salient_text_lower, event_lower
        )
    if "prime minister's questions" in event_lower or "pmqs" in event_lower:
        return (
            phrase_in_text(salient_text_lower, "prime minister's questions")
            or phrase_in_text(salient_text_lower, "pmqs")
            or (official_source and phrase_in_text(text_lower, "prime minister's questions"))
        )
    if "debate" in event_lower:
        return parliamentary_signal or phrase_in_text(salient_text_lower, "debate")
    if "budget" in event_lower:
        return phrase_in_text(salient_text_lower, "budget") or (
            official_source and phrase_in_text(text_lower, "budget")
        )
    if "statement" in event_lower:
        return phrase_in_text(salient_text_lower, "statement") or (
            official_source and phrase_in_text(text_lower, "statement")
        )
    return (
        event_lower in salient_text_lower
        or (official_source and event_lower in text_lower)
        or bool(topics & {"Government Policy", "Parliament"})
    )


def sanitize_event_candidates(article, text, entities, topics, locations, events):
    signals = event_context_signals(article, text, topics)
    valid_locations = set(sanitize_locations(locations))
    record_level_inferred_bodies = infer_government_bodies_from_text(
        " ".join(
            part
            for part in [article.get("title"), article.get("summary"), article.get("content")]
            if part
        )
    )
    sanitized = []
    seen = set()
    for event in events:
        name = normalize_event_name(event.get("name"))
        event_date = event.get("date") or None
        if (
            not name
            or not event_supported_by_context(name, signals)
            or not event_date_is_plausible(article, event_date)
        ):
            continue

        event_type = choose_more_specific_event_type(
            normalise_label(event.get("type")) or "PolicyEvent",
            name,
        )
        event_type = coerce_event_type_for_source(article, name, event_type, signals)
        location = normalise_label(event.get("location"))
        if location and location not in valid_locations:
            location = preferred_event_location(
                sorted(valid_locations), signals["text_lower"], topics
            )
        if location and location not in CANONICAL_LOCATION_NAMES and location.lower() not in name.lower():
            location = None

        key = (name, event_type, event_date, location or None)
        if key in seen:
            continue
        seen.add(key)
        context_text = build_event_context_text(article, name, event_type, event)
        heuristic_topics = choose_event_topics(name, context_text, topics)
        heuristic_actors = choose_event_entities(
            name, context_text, entities.get("politicians", [])
        )
        heuristic_bodies = choose_event_entities(
            name, context_text, entities.get("government_bodies", [])
        )
        heuristic_parties = choose_event_entities(
            name, context_text, entities.get("political_parties", [])
        )
        heuristic_parliamentary_body = choose_event_parliamentary_body(
            name, event_type, context_text, entities.get("government_bodies", [])
        )
        event_topics = unique_sorted(event.get("policy_topics", []) or heuristic_topics)
        event_actors = unique_sorted(event.get("political_actors", []) or heuristic_actors)
        explicit_or_heuristic_bodies = event.get("government_bodies", []) or heuristic_bodies
        if (
            not explicit_or_heuristic_bodies
            and event_type == "MinisterialStatement"
            and record_level_inferred_bodies
        ):
            explicit_or_heuristic_bodies = record_level_inferred_bodies
        event_bodies = unique_sorted(
            canonicalise_government_body_name(name)
            for name in explicit_or_heuristic_bodies
            if canonicalise_government_body_name(name)
        )
        event_parties = unique_sorted(
            canonicalise_political_party_name(name)
            for name in (event.get("political_parties", []) or heuristic_parties)
            if canonicalise_political_party_name(name)
        )
        event_parliamentary_body = (
            normalise_label(event.get("parliamentary_body") or heuristic_parliamentary_body) or None
        )
        evidence_spans = unique_sorted(
            event.get("evidence_spans", [])
            or build_event_evidence_spans(
                article, name, event_type, event_topics, event_actors, event_bodies
            )
        )
        extraction_method = resolve_event_extraction_method(
            event,
            used_heuristic_support=any(
                [
                    not event.get("policy_topics") and bool(heuristic_topics),
                    not event.get("political_actors") and bool(heuristic_actors),
                    not event.get("government_bodies") and bool(heuristic_bodies),
                    not event.get("political_parties") and bool(heuristic_parties),
                    not event.get("parliamentary_body") and bool(heuristic_parliamentary_body),
                    not event.get("evidence_spans") and bool(evidence_spans),
                ]
            ),
        )
        if event_type == "MinisterialStatement" and article.get("source_system") != "parliament":
            ministerial_context = " ".join(
                [
                    name,
                    article.get("title") or "",
                    article.get("summary") or "",
                    " ".join(event_bodies),
                    " ".join(evidence_spans),
                ]
            )
            if not has_ministerial_statement_signal(ministerial_context):
                event_type = "GovernmentPolicyEvent"
        if (
            article.get("source_system") == "parliament"
            and name in {"Policy Announcement", "Ministerial Statement"}
            and event_type == "MinisterialStatement"
            and not event_bodies
        ):
            event_type = "ParliamentaryEvent"
        sanitized.append(
            mark_event_candidate_flags(
                {
                    "name": name,
                    "type": event_type,
                    "date": event_date,
                    "location": location or None,
                    "source": event.get("source") or "heuristic",
                    "policy_topics": event_topics,
                    "political_actors": event_actors,
                    "government_bodies": event_bodies,
                    "parliamentary_body": event_parliamentary_body,
                    "political_parties": event_parties,
                    "evidence_spans": evidence_spans,
                    "confidence": infer_event_confidence(
                        article,
                        name,
                        event_type,
                        event,
                        signals,
                        evidence_spans=evidence_spans,
                        event_topics=event_topics,
                        event_actors=event_actors,
                        event_bodies=event_bodies,
                        event_parties=event_parties,
                        parliamentary_body=event_parliamentary_body,
                        heuristic_topics=heuristic_topics,
                        heuristic_actors=heuristic_actors,
                        heuristic_bodies=heuristic_bodies,
                        heuristic_parties=heuristic_parties,
                        heuristic_parliamentary_body=heuristic_parliamentary_body,
                    ),
                    "extraction_method": extraction_method,
                }
            )
        )

    govuk_explicit_signal = govuk_has_explicit_event_signal(article, text)
    has_specific_event = any(event["name"] not in GENERIC_EVENT_NAMES for event in sanitized)
    if article.get("source_system") == "govuk":
        if not govuk_explicit_signal and not has_specific_event:
            return []
        if govuk_explicit_signal and not has_specific_event:
            govuk_fallback = build_govuk_fallback_event(
                article, text, topics, sorted(valid_locations)
            )
            if govuk_fallback:
                return govuk_fallback

    if has_specific_event:
        sanitized = [event for event in sanitized if event["name"] not in GENERIC_EVENT_NAMES]
    elif sanitized and govuk_supports_event_fallback(article):
        govuk_fallback = build_govuk_fallback_event(article, text, topics, sorted(valid_locations))
        if govuk_fallback:
            sanitized = govuk_fallback

    return sanitized


def extract_events(article, text, topics, locations):
    signals = event_context_signals(article, text, topics)
    text_lower = signals["text_lower"]
    event_names = derive_event_names(signals)

    event_date = (article.get("published_at") or "")[:10] or None
    policy_signal = signals["policy_signal"]
    election_signal = signals["election_signal"]
    parliamentary_signal = signals["parliamentary_signal"]
    parliament_written_statement = signals["parliament_written_statement"]
    govuk_explicit_signal = govuk_has_explicit_event_signal(article, text)
    fallback_blocked = generic_event_fallback_blocked(article)

    events = []
    for event_name in event_names:
        event_type = infer_event_type(event_name)
        events.append(
            mark_event_candidate_flags(
                {
                    "name": event_name,
                    "type": event_type,
                    "date": event_date,
                    "location": choose_event_location(
                        event_name, event_type, locations, text_lower, topics
                    ),
                    "source": "heuristic",
                }
            )
        )

    if (
        not events
        and any(topic in topics for topic in ["Parliament", "Government Policy"])
        and policy_signal
        and (article.get("source_system") != "govuk" or govuk_explicit_signal)
        and not fallback_blocked
    ):
        if parliament_written_statement:
            fallback_type = "GovernmentPolicyEvent"
        else:
            fallback_type = (
                "ParliamentaryEvent"
                if "Parliament" in topics and parliamentary_signal
                else "GovernmentPolicyEvent"
            )
        events.append(
            mark_event_candidate_flags(
                {
                    "name": "Policy Announcement",
                    "type": fallback_type,
                    "date": event_date,
                    "location": choose_event_location(
                        "Policy Announcement", fallback_type, locations, text_lower, topics
                    ),
                    "source": "heuristic",
                }
            )
        )

    if not events:
        if "Election" in topics and election_signal:
            events.append(
                mark_event_candidate_flags(
                    {
                        "name": "Election",
                        "type": "PolicyEvent",
                        "date": event_date,
                        "location": choose_event_location(
                            "Election", "PolicyEvent", locations, text_lower, topics
                        ),
                        "source": "heuristic",
                    }
                )
            )
        elif (
            "Government Policy" in topics
            and policy_signal
            and (article.get("source_system") != "govuk" or govuk_explicit_signal)
            and not fallback_blocked
        ):
            events.append(
                mark_event_candidate_flags(
                    {
                        "name": "Policy Announcement",
                        "type": "GovernmentPolicyEvent",
                        "date": event_date,
                        "location": choose_event_location(
                            "Policy Announcement",
                            "GovernmentPolicyEvent",
                            locations,
                            text_lower,
                            topics,
                        ),
                        "source": "heuristic",
                    }
                )
            )
        elif {"Economic Policy", "Public Spending", "Taxation"} & set(topics):
            fiscal_signal = any(
                phrase_in_text(text_lower, phrase)
                for phrase in [
                    "spring budget",
                    "autumn budget",
                    "spending review",
                    "fiscal statement",
                ]
            )
            if fiscal_signal:
                events.append(
                    mark_event_candidate_flags(
                        {
                            "name": "Budget",
                            "type": "GovernmentPolicyEvent",
                            "date": event_date,
                            "location": choose_event_location(
                                "Budget", "GovernmentPolicyEvent", locations, text_lower, topics
                            ),
                            "source": "heuristic",
                        }
                    )
                )

    return events


def add_topic_based_fallback_events(article, text, topics, locations, events):
    if events:
        return events

    govuk_events = build_govuk_fallback_event(article, text, topics, locations)
    if govuk_events:
        return govuk_events
    if article.get("source_system") == "govuk" and not govuk_has_explicit_event_signal(
        article, text
    ):
        return events

    if generic_event_fallback_blocked(article):
        return events

    event_date = (article.get("published_at") or "")[:10] or None
    signals = event_context_signals(article, text, topics)
    text_lower = signals["text_lower"]
    policy_signal = signals["policy_signal"]
    election_signal = signals["election_signal"]

    if "Election" in topics and election_signal:
        return [
            mark_event_candidate_flags(
                {
                    "name": "Election",
                    "type": "PolicyEvent",
                    "date": event_date,
                    "location": choose_event_location(
                        "Election", "PolicyEvent", locations, text_lower, topics
                    ),
                    "source": "heuristic",
                }
            )
        ]

    if "Government Policy" in topics and policy_signal:
        return [
            mark_event_candidate_flags(
                {
                    "name": "Policy Announcement",
                    "type": "GovernmentPolicyEvent",
                    "date": event_date,
                    "location": choose_event_location(
                        "Policy Announcement",
                        "GovernmentPolicyEvent",
                        locations,
                        text_lower,
                        topics,
                    ),
                    "source": "heuristic",
                }
            )
        ]

    if {"Economic Policy", "Public Spending", "Taxation"} & set(topics):
        # only generate Budget fallback if text actually names fiscal event
        fiscal_signal = any(
            phrase_in_text(text_lower, phrase)
            for phrase in ["spring budget", "autumn budget", "spending review", "fiscal statement"]
        )
        if fiscal_signal:
            return [
                mark_event_candidate_flags(
                    {
                        "name": "Budget",
                        "type": "GovernmentPolicyEvent",
                        "date": event_date,
                        "location": choose_event_location(
                            "Budget", "GovernmentPolicyEvent", locations, text_lower, topics
                        ),
                        "source": "heuristic",
                    }
                )
            ]

    return events


def infer_event_confidence(
    article,
    event_name,
    event_type,
    event_payload,
    signals,
    *,
    evidence_spans=None,
    event_topics=None,
    event_actors=None,
    event_bodies=None,
    event_parties=None,
    parliamentary_body=None,
    heuristic_topics=None,
    heuristic_actors=None,
    heuristic_bodies=None,
    heuristic_parties=None,
    heuristic_parliamentary_body=None,
):
    explicit_confidence = normalise_confidence_value(event_payload.get("confidence"))
    if explicit_confidence:
        return explicit_confidence

    source_name = str(event_payload.get("source") or "").strip().lower()
    event_lower = event_name.lower()
    generic_name = event_name in GENERIC_EVENT_NAMES
    official_source = article.get("source_system") in {"govuk", "parliament"}
    score = 0

    if official_source and not generic_name:
        score += 2
    elif source_name == "openai" and not generic_name:
        score += 1

    if event_type == "MinisterialStatement" and (
        "statement" in event_lower
        or phrase_in_text(signals["salient_text_lower"], "statement")
        or phrase_in_text(signals["text_lower"], "statement")
    ):
        score += 1

    event_topics = unique_sorted(event_topics or [])
    event_actors = unique_sorted(event_actors or [])
    event_bodies = unique_sorted(event_bodies or [])
    event_parties = unique_sorted(event_parties or [])
    evidence_spans = unique_sorted(evidence_spans or [])

    support_count = sum(
        bool(values)
        for values in [event_topics, event_actors, event_bodies, event_parties, evidence_spans]
    ) + int(bool(parliamentary_body))
    if support_count >= 3:
        score += 2
    elif support_count >= 1:
        score += 1

    agreement_signals = 0
    if set(event_topics) & set(heuristic_topics or []):
        agreement_signals += 1
    if set(event_actors) & set(heuristic_actors or []):
        agreement_signals += 1
    if set(event_bodies) & set(heuristic_bodies or []):
        agreement_signals += 1
    if set(event_parties) & set(heuristic_parties or []):
        agreement_signals += 1
    if parliamentary_body and parliamentary_body == heuristic_parliamentary_body:
        agreement_signals += 1

    if agreement_signals >= 2:
        score += 2
    elif agreement_signals == 1:
        score += 1

    if generic_name:
        score -= 2

    if score >= 4:
        return "high"
    if score >= 1:
        return "medium"
    return "low"


def merge_event_scoped_entities(
    topics,
    politicians,
    political_parties,
    government_bodies,
    events,
):
    merged_topics = list(topics)
    merged_politicians = list(politicians)
    merged_parties = list(political_parties)
    merged_bodies = list(government_bodies)

    for event in events or []:
        merged_topics.extend(event.get("policy_topics", []))
        merged_politicians.extend(event.get("political_actors", []))
        merged_parties.extend(event.get("political_parties", []))
        merged_bodies.extend(event.get("government_bodies", []))
        parliamentary_body = event.get("parliamentary_body")
        if parliamentary_body:
            merged_bodies.append(parliamentary_body)

    return {
        "topics": unique_sorted(merged_topics),
        "politicians": sanitize_people(merged_politicians),
        "political_parties": unique_sorted(merged_parties),
        "government_bodies": unique_sorted(merged_bodies),
    }


def build_follow_up_candidates(article, topics, article_type):
    candidates = []
    event_names = [
        event.get("name") for event in article.get("event_candidates", []) if event.get("name")
    ]
    source_name = article.get("source_name")
    if article_type == "BreakingNewsArticle" and source_name and event_names:
        candidates.append(
            {
                "match_key": f"{source_name}|{event_names[0]}",
                "reason": "same source and event progression",
            }
        )
    return candidates


def build_relations(article_id, article, entities, events):
    relations = []

    for organisation in entities["organizations"]:
        relations.append({"subject": article_id, "predicate": "mentions", "object": organisation})

    for person in entities["people"]:
        relations.append({"subject": article_id, "predicate": "mentions", "object": person})

    for location in entities["locations"]:
        relations.append({"subject": article_id, "predicate": "located_in", "object": location})

    for topic in entities["topics"]:
        relations.append({"subject": article_id, "predicate": "mentions", "object": topic})

    for event in events:
        relations.append(
            {"subject": article_id, "predicate": "involved_in", "object": event["name"]}
        )

    if article.get("author"):
        relations.append(
            {"subject": article_id, "predicate": "authored_by", "object": article["author"]}
        )

    if article.get("source_name"):
        relations.append(
            {
                "subject": article_id,
                "predicate": "published_by",
                "object": article["source_name"],
            }
        )

    return relations


def merge_event_candidates(
    existing_events, suggested_events, default_date=None, default_location=None
):
    merged = {
        event["name"]: mark_event_candidate_flags(event)
        for event in existing_events
        if event.get("name")
    }

    for event in suggested_events or []:
        event_name = normalise_label(event.get("name"))
        if not event_name:
            continue

        merged[event_name] = {
            "name": event_name,
            "type": normalise_label(event.get("type")) or "PolicyEvent",
            "date": event.get("date") or default_date,
            "location": normalise_label(event.get("location")) or default_location,
            "source": "openai",
            "policy_topics": unique_sorted(event.get("policy_topics", [])),
            "political_actors": unique_sorted(event.get("political_actors", [])),
            "government_bodies": unique_sorted(
                canonicalise_government_body_name(name)
                for name in event.get("government_bodies", [])
                if canonicalise_government_body_name(name)
            ),
            "parliamentary_body": normalise_label(event.get("parliamentary_body")) or None,
            "political_parties": unique_sorted(
                canonicalise_political_party_name(name)
                for name in event.get("political_parties", [])
                if canonicalise_political_party_name(name)
            ),
            "evidence_spans": unique_sorted(event.get("evidence_spans", [])),
            "confidence": normalise_label(event.get("confidence")) or "medium",
            "extraction_method": str(event.get("extraction_method") or "").strip().lower(),
            "is_generic_fallback": bool(event.get("is_generic_fallback"))
            or is_generic_fallback_event_name(event_name),
        }

    return [merged[name] for name in sorted(merged)]


def should_use_openai_extraction(article, heuristic_result):
    source_system = article.get("source_system")
    if source_system not in CONFIG["TEXTUAL_SOURCE_SYSTEMS"]:
        return False

    article_type = heuristic_result.get("article_type")
    title_lower = normalise_label(article.get("title")).lower()
    url_lower = str(article.get("url") or "").lower()

    structural_live_signal = (
        title_lower.startswith("live")
        or title_lower.endswith("as it happened")
        or "live/" in url_lower
    )
    commentary_signal = (
        article_type == "OpinionArticle"
        or "| letters" in title_lower
        or "q&a" in title_lower
        or "obituary" in title_lower
    )
    if structural_live_signal or commentary_signal:
        return False

    has_core_structure = bool(heuristic_result.get("events")) and bool(
        heuristic_result.get("topics")
    )
    has_institution_or_actor = bool(heuristic_result.get("government_bodies")) or bool(
        heuristic_result.get("politicians")
    )
    if has_core_structure and has_institution_or_actor:
        return False

    return True


def apply_openai_extraction(article, text, heuristic_result):
    if not should_use_openai_extraction(article, heuristic_result):
        return heuristic_result

    llm_result = maybe_extract_article_with_openai(article, text, heuristic_result)
    if not llm_result:
        return heuristic_result

    topics = unique_sorted(
        heuristic_result["topics"]
        + [topic for topic in llm_result.get("topics", []) if topic in KNOWN_TOPIC_NAMES]
    )
    organisations = unique_sorted(
        heuristic_result["organizations"] + llm_result.get("organizations", [])
    )
    people = unique_sorted(heuristic_result["people"] + llm_result.get("people", []))
    locations = unique_sorted(heuristic_result["locations"] + llm_result.get("locations", []))

    politicians = unique_sorted(classify_politicians(people) + llm_result.get("politicians", []))
    political_parties = unique_sorted(
        classify_political_parties(organisations)
        + [
            canonicalise_political_party_name(name)
            for name in llm_result.get("political_parties", [])
            if canonicalise_political_party_name(name)
        ]
    )
    government_bodies = unique_sorted(
        classify_government_bodies(organisations)
        + [
            canonicalise_government_body_name(name)
            for name in llm_result.get("government_bodies", [])
            if canonicalise_government_body_name(name)
        ]
        + infer_government_bodies_from_text(text)
    )

    blocked_people = set(organisations) | set(political_parties) | set(government_bodies)
    organisations = sanitize_organizations(organisations)
    people = sanitize_people(person for person in people if person not in blocked_people)
    politicians = sanitize_people(person for person in politicians if person not in blocked_people)
    blocked_locations = blocked_people | set(people) | set(politicians)
    locations = sanitize_locations(locations, blocked_entities=blocked_locations)

    article_type = heuristic_result["article_type"]
    llm_type = llm_result.get("article_type")
    title_lower = (article.get("title") or "").lower()
    url_lower = (article.get("url") or "").lower()
    # title/URL live-blog signals are definitive -> ignore LLM when they fire
    structural_signal = (
        title_lower.startswith("live")
        or title_lower.endswith("as it happened")
        or "live/" in url_lower
    )
    if structural_signal:
        article_type = "BreakingNewsArticle"
    elif llm_type in {"NewsArticle", "OpinionArticle", "BreakingNewsArticle"}:
        article_type = llm_type

    sentiment = heuristic_result["sentiment"]
    if llm_result.get("sentiment") in {"Positive", "Negative", "Neutral"}:
        sentiment = llm_result["sentiment"]

    events = merge_event_candidates(
        heuristic_result["events"],
        llm_result.get("events", []),
        default_date=heuristic_result["default_event_date"],
        default_location=preferred_event_location(locations, text.lower(), topics),
    )
    scoped_entities = merge_event_scoped_entities(
        topics,
        politicians,
        political_parties,
        government_bodies,
        events,
    )

    return {
        "people": people,
        "organizations": organisations,
        "locations": locations,
        "topics": scoped_entities["topics"],
        "politicians": scoped_entities["politicians"],
        "political_parties": scoped_entities["political_parties"],
        "government_bodies": scoped_entities["government_bodies"],
        "sentiment": sentiment,
        "article_type": article_type,
        "events": events,
    }


def prepare_articles(raw_data):
    if isinstance(raw_data, list):
        return raw_data

    if not raw_data:
        raise ValueError("[EXTRACT] No data provided to extraction stage.")

    if "sources" in raw_data:
        return normalise_collected_sources(raw_data)

    raise ValueError("[EXTRACT] Unsupported input format for extraction stage.")


def extract_article_record(article):
    text = build_article_text(article)
    spacy_entities = extract_spacy_entities(text)
    article_id = article.get("id") or build_article_id(
        article.get("url", ""),
        article.get("title", ""),
        article.get("published_at", ""),
    )

    people = extract_people(text, spacy_candidates=spacy_entities["people"])
    organisations = extract_organisations(text, spacy_candidates=spacy_entities["organizations"])
    locations = extract_locations(text, spacy_candidates=spacy_entities["locations"])
    topics = extract_topics(text, tags=article.get("tags"), section=article.get("section"), source_system=article.get("source_system"))
    politicians = classify_politicians(people)
    political_parties = classify_political_parties(organisations)
    government_bodies = unique_sorted(
        classify_government_bodies(organisations)
        + infer_government_bodies_from_text(
            " ".join(p for p in [article.get("title"), article.get("summary")] if p)
        )
    )
    blocked_people = set(organisations) | set(political_parties) | set(government_bodies)
    organisations = sanitize_organizations(organisations)
    people = sanitize_people(person for person in people if person not in blocked_people)
    politicians = sanitize_people(person for person in politicians if person not in blocked_people)
    blocked_locations = blocked_people | set(people) | set(politicians)
    locations = sanitize_locations(locations, blocked_entities=blocked_locations)
    sentiment = classify_sentiment(text)
    article_type = article.get("raw_article_type_hint") or classify_article_type(article, text)
    events = extract_events(article, text, topics, locations)
    merged_extraction = apply_openai_extraction(
        article,
        text,
        {
            "people": people,
            "organizations": organisations,
            "locations": locations,
            "topics": topics,
            "politicians": politicians,
            "political_parties": political_parties,
            "government_bodies": government_bodies,
            "sentiment": sentiment,
            "article_type": article_type,
            "events": events,
            "default_event_date": (article.get("published_at") or "")[:10] or None,
        },
    )
    people = merged_extraction["people"]
    organisations = merged_extraction["organizations"]
    locations = merged_extraction["locations"]
    topics = merged_extraction["topics"]
    politicians = merged_extraction["politicians"]
    political_parties = merged_extraction["political_parties"]
    government_bodies = merged_extraction["government_bodies"]
    sentiment = merged_extraction["sentiment"]
    article_type = merged_extraction["article_type"]
    organisations = sanitize_organizations(organisations)
    people = sanitize_people(person for person in people if person not in set(organisations))
    politicians = sanitize_people(
        person for person in politicians if person not in set(organisations)
    )
    blocked_locations = set(organisations) | set(political_parties) | set(government_bodies)
    blocked_locations |= set(people) | set(politicians)
    locations = sanitize_locations(locations, blocked_entities=blocked_locations)
    if article.get("raw_article_type_hint") in {
        "NewsArticle",
        "OpinionArticle",
        "BreakingNewsArticle",
    }:
        article_type = article["raw_article_type_hint"]
    entities = {
        "people": people,
        "politicians": politicians,
        "organizations": organisations,
        "political_parties": political_parties,
        "government_bodies": government_bodies,
        "locations": locations,
        "topics": topics,
        "technologies": [],
        "events": [],
    }
    events = add_topic_based_fallback_events(
        article, text, topics, locations, merged_extraction["events"]
    )
    events = sanitize_event_candidates(article, text, entities, topics, locations, events)
    enriched_article = dict(article)
    enriched_article["event_candidates"] = events
    follow_up_candidates = build_follow_up_candidates(enriched_article, topics, article_type)
    entities["events"] = [event["name"] for event in events]

    return {
        "id": article_id,
        "source_system": article.get("source_system"),
        "source_name": article.get("source_name"),
        "title": article.get("title"),
        "url": article.get("url"),
        "published_at": article.get("published_at"),
        "updated_at": article.get("updated_at"),
        "author": article.get("author"),
        "section": article.get("section"),
        "summary": article.get("summary"),
        "content": article.get("content"),
        "tags": article.get("tags") or [],
        "word_count": article.get("word_count") or 0,
        "article_type": article_type,
        "sentiment": sentiment,
        "follow_up_candidates": follow_up_candidates,
        "event_candidates": events,
        "entities": entities,
        "relations": build_relations(article_id, article, entities, events),
    }


def extract_relevant_information(raw_data):
    print("[EXTRACT] Starting extraction stage...")

    articles = prepare_articles(raw_data)
    if not articles:
        raise ValueError("[EXTRACT] No articles found in input data.")

    extracted = []
    progress_every = max(1, int(CONFIG.get("EXTRACTION_PROGRESS_EVERY", 25)))
    for index, article in enumerate(articles):
        if index and index % progress_every == 0:
            print(f"[EXTRACT] Progress: {index}/{len(articles)} records processed...")
        try:
            extracted.append(extract_article_record(article))
        except Exception as exc:
            raise RuntimeError(f"[EXTRACT] Failed processing article {index}: {exc}") from exc

    print(f"[EXTRACT] Extracted {len(extracted)} records.")
    return extracted


def build_extraction_audit_metrics(records):
    metrics = {
        "record_count": len(records),
        "event_count": 0,
        "generic_fallback_event_count": 0,
        "records_with_generic_fallback": 0,
        "generic_fallback_name_counts": {},
        "confidence_counts": {},
        "extraction_method_counts": {},
    }

    fallback_name_counts = defaultdict(int)
    confidence_counts = defaultdict(int)
    extraction_method_counts = defaultdict(int)

    for record in records:
        events = record.get("event_candidates", [])
        metrics["event_count"] += len(events)
        has_generic_fallback = False
        for event in events:
            if event.get("is_generic_fallback"):
                has_generic_fallback = True
                metrics["generic_fallback_event_count"] += 1
                fallback_name_counts[event.get("name") or "Unknown"] += 1
            confidence_key = str(event.get("confidence") or "unknown").strip().lower() or "unknown"
            confidence_counts[confidence_key] += 1
            extraction_key = (
                str(event.get("extraction_method") or "unknown").strip().lower() or "unknown"
            )
            extraction_method_counts[extraction_key] += 1
        if has_generic_fallback:
            metrics["records_with_generic_fallback"] += 1

    metrics["generic_fallback_name_counts"] = dict(sorted(fallback_name_counts.items()))
    metrics["confidence_counts"] = dict(sorted(confidence_counts.items()))
    metrics["extraction_method_counts"] = dict(sorted(extraction_method_counts.items()))
    return metrics
