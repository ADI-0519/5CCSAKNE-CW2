"""Unit tests for data_normalisation module."""

import pytest
from src.data_normalisation import (
    _stable_id,
    _canonicalise_date,
    _is_valid_url,
    _normalise_name,
    normalise_data,
)


class TestStableId:
    def test_uses_url_when_present(self):
        id1 = _stable_id("https://example.com/a", "Title", "2024-01-01")
        id2 = _stable_id("https://example.com/a", "Different Title", "2024-01-02")
        assert id1 == id2  # URL takes precedence

    def test_falls_back_to_title_plus_date(self):
        id1 = _stable_id("", "My Title", "2024-01-01")
        id2 = _stable_id("", "My Title", "2024-01-01")
        assert id1 == id2

    def test_is_16_chars(self):
        assert len(_stable_id("https://x.com", "", "")) == 16


class TestCanonicalisedDate:
    def test_parses_iso_z(self):
        result = _canonicalise_date("2024-01-15T10:00:00Z")
        assert result == "2024-01-15T10:00:00Z"

    def test_parses_date_only(self):
        result = _canonicalise_date("2024-01-15")
        assert result.startswith("2024-01-15")

    def test_raises_on_invalid_date(self):
        with pytest.raises(ValueError, match="Cannot parse date"):
            _canonicalise_date("not-a-date")

    def test_raises_on_empty_date(self):
        with pytest.raises((ValueError, TypeError)):
            _canonicalise_date("")


class TestIsValidUrl:
    def test_valid_https_url(self):
        assert _is_valid_url("https://example.com/article") is True

    def test_valid_http_url(self):
        assert _is_valid_url("http://example.com/") is True

    def test_rejects_ftp(self):
        assert _is_valid_url("ftp://example.com/file") is False

    def test_rejects_empty_string(self):
        assert _is_valid_url("") is False

    def test_rejects_relative_path(self):
        assert _is_valid_url("/just/a/path") is False


class TestNormaliseName:
    def test_trims_whitespace(self):
        assert _normalise_name("  hello world  ") == "hello world"

    def test_collapses_internal_spaces(self):
        assert _normalise_name("hello   world") == "hello world"

    def test_empty_returns_empty(self):
        assert _normalise_name("") == ""

    def test_none_returns_empty(self):
        assert _normalise_name(None) == ""


class TestNormaliseData:
    def _valid_record(self, **overrides):
        base = {
            "id": "abc123",
            "title": "Test Article Title",
            "url": "https://example.com/test",
            "published_at": "2024-01-15T10:00:00Z",
            "source_name": "Test Source",
            "author": "Jane Doe",
            "summary": "A test summary.",
            "entities": {
                "organizations": ["Acme Corp"],
                "people": ["Jane Doe"],
                "locations": ["London"],
                "technologies": ["AI"],
                "topics": ["research"],
            },
            "relations": [
                {"subject": "abc123", "predicate": "mentions", "object": "AI"},
            ],
        }
        base.update(overrides)
        return base

    def test_returns_normalised_records(self):
        result = normalise_data([self._valid_record()])
        assert len(result) == 1
        r = result[0]
        assert r["title"] == "Test Article Title"
        assert r["published_at"] == "2024-01-15T10:00:00Z"

    def test_raises_on_empty_input(self):
        with pytest.raises(ValueError, match="No extracted data"):
            normalise_data([])

    def test_raises_on_none_input(self):
        with pytest.raises((ValueError, TypeError)):
            normalise_data(None)

    def test_raises_on_missing_title(self):
        with pytest.raises(ValueError, match="title"):
            normalise_data([self._valid_record(title="")])

    def test_raises_on_missing_url(self):
        with pytest.raises(ValueError, match="url"):
            normalise_data([self._valid_record(url="")])

    def test_raises_on_invalid_url(self):
        with pytest.raises(ValueError, match="invalid URL"):
            normalise_data([self._valid_record(url="not-a-url")])

    def test_raises_on_missing_published_at(self):
        with pytest.raises(ValueError, match="published_at"):
            normalise_data([self._valid_record(published_at="")])

    def test_raises_on_missing_source_name(self):
        with pytest.raises(ValueError, match="source_name"):
            normalise_data([self._valid_record(source_name="")])

    def test_raises_on_unknown_predicate(self):
        record = self._valid_record(
            relations=[{"subject": "abc123", "predicate": "invented_by", "object": "AI"}]
        )
        with pytest.raises(ValueError, match="unknown predicate"):
            normalise_data([record])

    def test_deduplicates_entities(self):
        record = self._valid_record(
            entities={
                "organizations": ["Acme Corp", "Acme Corp"],
                "people": [],
                "locations": [],
                "technologies": ["AI", "AI"],
                "topics": [],
            },
            relations=[],
        )
        result = normalise_data([record])
        assert result[0]["entities"]["organizations"] == ["Acme Corp"]
        assert result[0]["entities"]["technologies"] == ["AI"]

    def test_generates_stable_id_from_url(self):
        result = normalise_data([self._valid_record()])
        import hashlib
        expected = hashlib.sha256(b"https://example.com/test").hexdigest()[:16]
        assert result[0]["id"] == expected

    def test_canonicalises_date_to_utc(self):
        record = self._valid_record(published_at="2024-06-01T08:00:00Z")
        result = normalise_data([record])
        assert result[0]["published_at"] == "2024-06-01T08:00:00Z"