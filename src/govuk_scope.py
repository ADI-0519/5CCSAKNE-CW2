from src.config import CONFIG

FILTER_RULES = CONFIG["FILTER_RULES"]


def _normalise_text(value):
    if not value:
        return ""
    return " ".join(str(value).strip().split())


def govuk_result_format(item):
    return _normalise_text(item.get("format")).lower()


def govuk_result_text(item):
    parts = [
        item.get("title"),
        item.get("description"),
        item.get("document_type"),
        " ".join(str(org) for org in item.get("organisations") or []),
    ]
    return _normalise_text(" ".join(part for part in parts if part)).lower()


def govuk_result_is_noise(item):
    text = govuk_result_text(item)
    return any(term in text for term in FILTER_RULES["govuk_excluded_text_terms"])


def govuk_result_has_scope_signal(item):
    text = govuk_result_text(item)
    return any(term in text for term in FILTER_RULES["govuk_scope_signal_terms"])


def govuk_result_is_in_scope(item):
    document_format = govuk_result_format(item)
    if document_format not in CONFIG["GOVUK_DOCUMENT_FORMATS"]:
        return False
    if govuk_result_is_noise(item):
        return False
    if document_format in CONFIG["GOVUK_ALWAYS_INCLUDE_FORMATS"]:
        return True
    return govuk_result_has_scope_signal(item)
