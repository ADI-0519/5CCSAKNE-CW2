import hashlib
import re
from collections import defaultdict

from src.config import CONFIG
from src.data_normalisation import normalise_collected_sources, normalise_newsapi_articles

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
    if not text:
        return ""
    return " ".join(str(text).strip().split())


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
        if any(part in blocked_person_words for part in parts):
            continue
        found.add(name)

    return sorted(found)


def extract_locations(text):
    found = set(find_named_matches(text, CONFIG["UK_LOCATION_NAMES"]))

    for match in LOCATION_PATTERN.finditer(text):
        location = normalise_label(match.group(1))
        if location not in CONFIG["ENTITY_STOPLIST"]:
            found.add(location)

    return sorted(found)


def extract_organisations(text):
    found = set(find_named_matches(text, CONFIG["POLITICAL_PARTY_NAMES"]))
    found.update(find_named_matches(text, CONFIG["GOVERNMENT_BODY_NAMES"]))

    for match in ORG_PATTERN.finditer(text):
        organisation = normalise_label(match.group(1))
        if organisation not in CONFIG["ENTITY_STOPLIST"]:
            found.add(organisation)

    return sorted(found)


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
    if any(hint in event_lower for hint in CONFIG["ECONOMIC_EVENT_HINTS"]):
        return "EconomicEvent"
    return "PoliticalEvent"


def extract_events(article, text, topics, locations):
    text_lower = text.lower()
    event_names = set()

    for hint in CONFIG["ECONOMIC_EVENT_HINTS"] + CONFIG["POLITICAL_EVENT_HINTS"]:
        if phrase_in_text(text_lower, hint):
            event_names.add(hint.title())

    if phrase_in_text(text_lower, "spring statement"):
        event_names.add("Spring Statement")
    if phrase_in_text(text_lower, "budget") and phrase_in_text(text_lower, "spring"):
        event_names.add("UK Spring Budget")
    if phrase_in_text(text_lower, "leadership contest"):
        event_names.add("Leadership Contest")
    if phrase_in_text(text_lower, "parliamentary vote") or phrase_in_text(
        text_lower, "commons vote"
    ):
        event_names.add("Parliamentary Vote")

    event_date = (article.get("published_at") or "")[:10] or None
    default_location = locations[0] if locations else None

    events = []
    for event_name in sorted(event_names):
        events.append(
            {
                "name": event_name,
                "type": infer_event_type(event_name),
                "date": event_date,
                "location": default_location,
                "source": "heuristic",
            }
        )

    policy_signal = any(
        phrase_in_text(text_lower, phrase)
        for phrase in [
            "announced",
            "announcement",
            "unveiled",
            "set out",
            "proposal",
            "proposed",
            "plans",
            "bill",
        ]
    )

    if (
        not events
        and any(topic in topics for topic in ["Election", "Parliament", "Government Policy"])
        and policy_signal
    ):
        events.append(
            {
                "name": "Policy Announcement",
                "type": "PoliticalEvent",
                "date": event_date,
                "location": default_location,
                "source": "heuristic",
            }
        )

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


def prepare_articles(raw_data):
    if isinstance(raw_data, list):
        return raw_data

    if not raw_data:
        raise ValueError("[EXTRACT] No data provided to extraction stage.")

    if "sources" in raw_data:
        return normalise_collected_sources(raw_data)

    if raw_data.get("articles"):
        return normalise_newsapi_articles(raw_data)

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
    people = sorted(person for person in people if person not in blocked_people)
    politicians = sorted(person for person in politicians if person not in blocked_people)
    sentiment = classify_sentiment(text)
    article_type = article.get("raw_article_type_hint") or classify_article_type(article, text)
    events = extract_events(article, text, topics, locations)
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
