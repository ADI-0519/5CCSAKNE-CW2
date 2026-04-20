import hashlib
import re
from collections import defaultdict
from datetime import date

from src.config import CONFIG
from src.data_normalisation import normalise_collected_sources, normalise_name
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


def find_named_matches(text, candidates):
    text_lower = text.lower()
    matches = [candidate for candidate in candidates if candidate.lower() in text_lower]
    return unique_sorted(matches)


def phrase_pattern(phrase):
    escaped = re.escape(phrase.lower())
    return re.compile(rf"(?<![a-z0-9]){escaped}(?![a-z0-9])")


def phrase_in_text(text_lower, phrase):
    return bool(phrase_pattern(phrase).search(text_lower))


def phrase_match_count(text_lower, phrase):
    return len(phrase_pattern(phrase).findall(text_lower))


def extract_topics(text, tags=None, section=None):
    text_lower = text.lower()
    topic_scores = defaultdict(int)

    for topic_name, hints in CONFIG["TOPIC_GROUPS"].items():
        hits = sum(phrase_match_count(text_lower, hint) for hint in hints)
        if hits:
            topic_scores[topic_name] += hits

    for tag in tags or []:
        tag_lower = tag.lower()
        for topic_name, hints in CONFIG["TOPIC_GROUPS"].items():
            if phrase_in_text(tag_lower, topic_name):
                topic_scores[topic_name] += 3
            tag_hits = sum(phrase_match_count(tag_lower, hint) for hint in hints)
            if tag_hits:
                topic_scores[topic_name] += min(tag_hits, 2)

    if section:
        section_lower = section.lower()
        if "politics" in section_lower:
            topic_scores["Politics"] += 2
        if section_lower in CONFIG["OPINION_SECTION_NAMES"]:
            topic_scores["Opinion"] += 2

    if not topic_scores:
        return []

    ranked = sorted(topic_scores.items(), key=lambda item: (-item[1], item[0]))
    selected = []
    for topic_name, score in ranked:
        if score <= 0:
            continue
        if topic_name in {"Government Policy", "Politics"} and score < 2:
            continue
        selected.append(topic_name)
        if len(selected) == 4:
            break

    return selected


def extract_people(text):
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
    found = set(find_named_matches(text, CONFIG["POLITICIAN_NAMES"]))

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


def extract_locations(text):
    found = set(find_named_matches(text, CONFIG["UK_LOCATION_NAMES"]))

    for match in LOCATION_PATTERN.finditer(text):
        location = normalise_label(match.group(1))
        if is_location_candidate_valid(location):
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
_GENERIC_EVENT_NAMES = {
    "Election",
    "Ministerial Statement",
    "Parliamentary Debate",
    "Policy Announcement",
}


def has_any_phrase_signal(text_lower, phrases):
    return any(phrase_in_text(text_lower, phrase) for phrase in phrases)


def is_historical_election_reference(text_lower, phrase):
    if "election" not in phrase:
        return False
    return any(
        phrase_in_text(text_lower, f"{prefix}{phrase}")
        for prefix in ["last ", "previous ", "past "]
    )


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
    canonical_locations = set(CONFIG["UK_LOCATION_NAMES"])
    if candidate not in canonical_locations and len(tokens) == 1 and len(tokens[0]) <= 2:
        return False
    if any(token in CONFIG["EXTRACTION_LOCATION_STOPWORDS"] for token in tokens):
        return False
    if any(token in CONFIG["EXTRACTION_LOCATION_ROLE_TERMS"] for token in tokens):
        return False
    if any(token in CONFIG["EXTRACTION_ORG_NOISE_TERMS"] for token in tokens):
        return False

    candidate_lower = candidate.lower()
    if " mp" in candidate_lower or candidate_lower.endswith(" mps"):
        return False
    if any(party.lower() in candidate_lower for party in CONFIG["POLITICAL_PARTY_NAMES"]):
        return False

    return True


def label_token_set(value):
    return {token.lower() for token in normalise_label(value).split() if token}


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
    known_locations = set(CONFIG["UK_LOCATION_NAMES"])
    known_parties = set(CONFIG["POLITICAL_PARTY_NAMES"])

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
    canonical_locations = set(CONFIG["UK_LOCATION_NAMES"])
    cleaned = []
    for location in locations:
        candidate = normalise_label(location)
        if not is_location_candidate_valid(candidate):
            continue
        if candidate not in canonical_locations and overlaps_blocked_entity(candidate, blocked):
            continue
        cleaned.append(candidate)
    return unique_sorted(cleaned)


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


def extract_organisations(text):
    found = set(find_named_matches(text, CONFIG["POLITICAL_PARTY_NAMES"]))
    found.update(find_named_matches(text, CONFIG["GOVERNMENT_BODY_NAMES"]))

    for match in ORG_PATTERN.finditer(text):
        organisation = normalise_label(match.group(1))
        first_token = organisation.split()[0]
        if first_token in _ORG_LEAD_IN or first_token in CONFIG["EXTRACTION_ORG_BLOCKED_PREFIXES"]:
            continue
        if organisation not in CONFIG["ENTITY_STOPLIST"]:
            found.add(organisation)

    return sanitize_organizations(found)


def classify_politicians(people):
    politician_names = set(CONFIG["POLITICIAN_NAMES"])
    return sorted(person for person in people if person in politician_names)


def classify_political_parties(organisations):
    party_names = set(CONFIG["POLITICAL_PARTY_NAMES"])
    return sorted(organisation for organisation in organisations if organisation in party_names)


def classify_government_bodies(organisations):
    body_names = set(CONFIG["GOVERNMENT_BODY_NAMES"])
    return sorted(organisation for organisation in organisations if organisation in body_names)


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

    if section in CONFIG["OPINION_SECTION_NAMES"] or "opinion" in title or "analysis" in title:
        return "OpinionArticle"

    breaking_hits = sum(hint in combined for hint in CONFIG["BREAKING_NEWS_HINTS"])
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
    if "statement" in event_lower:
        return "MinisterialStatement"
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
    ]
    if filtered:
        return filtered[0]

    return candidates[0]


def build_salient_event_text(article):
    parts = [
        article.get("title"),
        article.get("summary"),
        " ".join(article.get("tags") or []),
    ]
    return " ".join(normalise_label(part) for part in parts if part).lower()


def event_context_signals(article, text, topics):
    text_lower = text.lower()
    salient_text_lower = build_salient_event_text(article)
    official_source = article.get("source_system") in {"govuk", "parliament"}
    parliament_written_statement = article.get("source_system") == "parliament"
    policy_signal = has_any_phrase_signal(
        salient_text_lower, CONFIG["EXTRACTION_POLICY_ANNOUNCEMENT_SIGNAL_PHRASES"]
    ) or (
        official_source
        and has_any_phrase_signal(
            text_lower, CONFIG["EXTRACTION_POLICY_ANNOUNCEMENT_SIGNAL_PHRASES"]
        )
    )
    election_signal = has_any_phrase_signal(
        salient_text_lower, CONFIG["EXTRACTION_ELECTION_SIGNAL_PHRASES"]
    )
    parliamentary_signal = any(
        phrase_in_text(salient_text_lower, phrase)
        or (official_source and phrase_in_text(text_lower, phrase))
        for phrase in [
            "committee",
            "commons",
            "house of commons",
            "house of lords",
            "lords",
            "parliament",
            "westminster",
        ]
    )
    return {
        "text_lower": text_lower,
        "salient_text_lower": salient_text_lower,
        "official_source": official_source,
        "parliament_written_statement": parliament_written_statement,
        "policy_signal": policy_signal,
        "election_signal": election_signal,
        "parliamentary_signal": parliamentary_signal,
        "topics": set(topics),
    }


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

    if "statement" in event_lower:
        return "MinisterialStatement"

    if event_type == "ParliamentaryEvent":
        return "GovernmentPolicyEvent"

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


def sanitize_event_candidates(article, text, topics, locations, events):
    signals = event_context_signals(article, text, topics)
    valid_locations = set(sanitize_locations(locations))
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

        key = (name, event_type, event_date, location or None)
        if key in seen:
            continue
        seen.add(key)
        sanitized.append(
            {
                "name": name,
                "type": event_type,
                "date": event_date,
                "location": location or None,
                "source": event.get("source") or "heuristic",
            }
        )

    has_specific_event = any(event["name"] not in _GENERIC_EVENT_NAMES for event in sanitized)
    if has_specific_event:
        sanitized = [event for event in sanitized if event["name"] not in _GENERIC_EVENT_NAMES]

    return sanitized


def extract_events(article, text, topics, locations):
    signals = event_context_signals(article, text, topics)
    text_lower = signals["text_lower"]
    salient_text_lower = signals["salient_text_lower"]
    official_source = signals["official_source"]
    event_names = set()

    for hint in CONFIG["ECONOMIC_EVENT_HINTS"] + CONFIG["POLITICAL_EVENT_HINTS"]:
        in_salient_text = phrase_in_text(salient_text_lower, hint)
        in_full_text = phrase_in_text(text_lower, hint)
        if in_salient_text or (official_source and in_full_text):
            signal_text = salient_text_lower if in_salient_text else text_lower
            if is_historical_election_reference(signal_text, hint):
                continue
            event_names.add(hint.title())

    if phrase_in_text(salient_text_lower, "spring statement") or (
        official_source and phrase_in_text(text_lower, "spring statement")
    ):
        event_names.add("Spring Statement")
    if phrase_in_text(salient_text_lower, "leadership contest"):
        event_names.add("Leadership Contest")
    if (
        phrase_in_text(salient_text_lower, "parliamentary vote")
        or phrase_in_text(salient_text_lower, "commons vote")
        or (official_source and phrase_in_text(text_lower, "parliamentary vote"))
    ):
        event_names.add("Parliamentary Vote")
    if (
        phrase_in_text(salient_text_lower, "prime minister's questions")
        or phrase_in_text(salient_text_lower, "pmqs")
        or (official_source and phrase_in_text(text_lower, "prime minister's questions"))
    ):
        event_names.add("Prime Minister's Questions")
    if (
        phrase_in_text(salient_text_lower, "lords debate")
        or phrase_in_text(salient_text_lower, "commons debate")
        or phrase_in_text(salient_text_lower, "house of lords debate")
        or phrase_in_text(salient_text_lower, "house of commons debate")
    ):
        event_names.add("Debate")

    event_date = (article.get("published_at") or "")[:10] or None
    policy_signal = signals["policy_signal"]
    election_signal = signals["election_signal"]
    parliamentary_signal = signals["parliamentary_signal"]
    parliament_written_statement = signals["parliament_written_statement"]

    events = []
    for event_name in sorted(event_names):
        event_type = infer_event_type(event_name)
        events.append(
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

    if (
        not events
        and any(topic in topics for topic in ["Parliament", "Government Policy"])
        and policy_signal
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

    if not events:
        if "Election" in topics and election_signal:
            events.append(
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
        elif "Government Policy" in topics and (
            policy_signal
            or any(
                phrase_in_text(text_lower, phrase)
                for phrase in ["government", "minister", "ministers", "prime minister", "treasury"]
            )
        ):
            events.append(
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

    return events


def add_topic_based_fallback_events(article, text, topics, locations, events):
    if events:
        return events

    event_date = (article.get("published_at") or "")[:10] or None
    signals = event_context_signals(article, text, topics)
    text_lower = signals["text_lower"]
    policy_signal = signals["policy_signal"] or any(
        phrase_in_text(signals["salient_text_lower"], phrase)
        or (signals["official_source"] and phrase_in_text(text_lower, phrase))
        for phrase in ["government", "minister", "ministers", "prime minister", "treasury"]
    )
    election_signal = signals["election_signal"]

    if "Election" in topics and election_signal:
        return [
            {
                "name": "Election",
                "type": "PolicyEvent",
                "date": event_date,
                "location": choose_event_location(
                    "Election", "PolicyEvent", locations, text_lower, topics
                ),
                "source": "heuristic",
            }
        ]

    if "Government Policy" in topics and policy_signal:
        return [
            {
                "name": "Policy Announcement",
                "type": "GovernmentPolicyEvent",
                "date": event_date,
                "location": choose_event_location(
                    "Policy Announcement", "GovernmentPolicyEvent", locations, text_lower, topics
                ),
                "source": "heuristic",
            }
        ]

    if {"Economic Policy", "Public Spending", "Taxation"} & set(topics):
        # only generate Budget fallback if text actually names fiscal event
        fiscal_signal = any(
            phrase_in_text(text_lower, phrase)
            for phrase in ["spring budget", "autumn budget", "spending review", "fiscal statement"]
        )
        if fiscal_signal:
            return [
                {
                    "name": "Budget",
                    "type": "GovernmentPolicyEvent",
                    "date": event_date,
                    "location": choose_event_location(
                        "Budget", "GovernmentPolicyEvent", locations, text_lower, topics
                    ),
                    "source": "heuristic",
                }
            ]

    return events


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
    merged = {event["name"]: dict(event) for event in existing_events if event.get("name")}

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
        }

    return [merged[name] for name in sorted(merged)]


def apply_openai_extraction(article, text, heuristic_result):
    llm_result = maybe_extract_article_with_openai(article, text, heuristic_result)
    if not llm_result:
        return heuristic_result

    topics = unique_sorted(
        heuristic_result["topics"]
        + [topic for topic in llm_result.get("topics", []) if topic in CONFIG["TOPIC_GROUPS"]]
    )
    organisations = unique_sorted(
        heuristic_result["organizations"] + llm_result.get("organizations", [])
    )
    people = unique_sorted(heuristic_result["people"] + llm_result.get("people", []))
    locations = unique_sorted(heuristic_result["locations"] + llm_result.get("locations", []))

    politicians = unique_sorted(classify_politicians(people) + llm_result.get("politicians", []))
    political_parties = unique_sorted(
        classify_political_parties(organisations) + llm_result.get("political_parties", [])
    )
    government_bodies = unique_sorted(
        classify_government_bodies(organisations) + llm_result.get("government_bodies", [])
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

    return {
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
    article_id = article.get("id") or build_article_id(
        article.get("url", ""),
        article.get("title", ""),
        article.get("published_at", ""),
    )

    people = extract_people(text)
    organisations = extract_organisations(text)
    locations = extract_locations(text)
    topics = extract_topics(text, tags=article.get("tags"), section=article.get("section"))
    politicians = classify_politicians(people)
    political_parties = classify_political_parties(organisations)
    government_bodies = classify_government_bodies(organisations)
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
    events = add_topic_based_fallback_events(
        article,
        text,
        topics,
        locations,
        merged_extraction["events"],
    )
    events = sanitize_event_candidates(article, text, topics, locations, events)
    enriched_article = dict(article)
    enriched_article["event_candidates"] = events
    follow_up_candidates = build_follow_up_candidates(enriched_article, topics, article_type)

    entities = {
        "people": people,
        "politicians": politicians,
        "organizations": organisations,
        "political_parties": political_parties,
        "government_bodies": government_bodies,
        "locations": locations,
        "topics": topics,
        "technologies": [],
        "events": [event["name"] for event in events],
    }

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
    for index, article in enumerate(articles):
        try:
            extracted.append(extract_article_record(article))
        except Exception as exc:
            raise RuntimeError(f"[EXTRACT] Failed processing article {index}: {exc}") from exc

    print(f"[EXTRACT] Extracted {len(extracted)} records.")
    return extracted
