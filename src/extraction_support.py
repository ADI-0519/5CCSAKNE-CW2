import re

from src.config import CONFIG
from src.data_normalisation import normalise_name

GENERIC_EVENT_NAMES = frozenset(
    {
        "Election",
        "Ministerial Statement",
        "Parliamentary Debate",
        "Policy Announcement",
    }
)


def normalise_label(text):
    return normalise_name(text)


def phrase_pattern(phrase):
    escaped = re.escape(phrase.lower())
    return re.compile(rf"(?<![a-z0-9]){escaped}(?![a-z0-9])")


def phrase_in_text(text_lower, phrase):
    return bool(phrase_pattern(phrase).search(text_lower))


def phrase_match_count(text_lower, phrase):
    return len(phrase_pattern(phrase).findall(text_lower))


def has_any_phrase_signal(text_lower, phrases):
    return any(phrase_in_text(text_lower, phrase) for phrase in phrases)


def is_historical_election_reference(text_lower, phrase):
    if "election" not in phrase:
        return False
    return any(
        phrase_in_text(text_lower, f"{prefix}{phrase}")
        for prefix in ["last ", "previous ", "past "]
    )


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


def derive_event_names(signals):
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

    return sorted(event_names)
