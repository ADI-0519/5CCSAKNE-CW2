from pathlib import Path


def test_expected_project_directories_exist() -> None:
    for name in ("docs", "kg", "queries", "src", "tests"):
        assert Path(name).exists(), f"Expected {name}/ to exist"
