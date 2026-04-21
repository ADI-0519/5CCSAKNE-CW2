from src.openai_client import build_cache_path, load_cache_payload, save_cache_payload


def test_build_cache_path_hashes_long_keys_to_keep_windows_safe(tmp_path, monkeypatch):
    monkeypatch.setitem(
        __import__("src.openai_client", fromlist=["CONFIG"]).CONFIG,
        "OPENAI_CACHE_DIR",
        str(tmp_path / "openai-cache"),
    )

    cache_key = (
        "http://example.org/news/event/"
        "We_are_appalled_by_the_continued_restrictions_imposed_on_the_women_and_girls_of_"
        "Afghanistan__UK_statement_at_the_UN_Security_Council_2026-03-09_Westminster"
    )
    payload = {"answer": "cached"}

    cache_path = build_cache_path("rag_completion", cache_key)

    assert len(cache_path.name) < 100
    assert str(cache_path).endswith(".json")

    save_cache_payload(cache_path, payload)

    assert cache_path.exists()
    assert load_cache_payload(cache_path) == payload


def test_build_cache_path_uses_absolute_path_length_budget(tmp_path, monkeypatch):
    long_cache_root = tmp_path / (
        "very_long_workspace_prefix_for_windows_path_budget_regression_check"
        "_and_additional_nested_segments"
    )
    monkeypatch.setitem(
        __import__("src.openai_client", fromlist=["CONFIG"]).CONFIG,
        "OPENAI_CACHE_DIR",
        str(long_cache_root),
    )

    cache_key = (
        "http://example.org/news/event/"
        "statement_on_housing_reform_with_extra_descriptive_context_to_push_the_absolute_path_"
        "well_beyond_old_windows_limits_even_if_the_relative_filename_looks_safe"
    )

    cache_path = build_cache_path("rag_completion", cache_key)

    assert len(cache_path.name) < 100
    resolved_root = long_cache_root.resolve(strict=False)
    resolved_path = cache_path.resolve(strict=False)
    added_length = len(str(resolved_path)) - len(str(resolved_root))
    assert added_length <= 40, (
        f"expected digest-only fallback under long cache root, "
        f"but path grew by {added_length} chars: {resolved_path}"
    )
