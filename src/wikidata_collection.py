"""Collect structured entity data from the Wikidata SPARQL endpoint.

This module queries Wikidata for UK politicians, political parties, and
government bodies.  It serves as the structured data source for the KG
pipeline, complementing the textual data extracted from Guardian articles.

No API key is required.  All queries use the public Wikidata Query Service.
"""

import json
import time
from pathlib import Path

import requests

from src.config import CONFIG

WIKIDATA_SPARQL_URL = "https://query.wikidata.org/sparql"
REQUEST_HEADERS = {
    "Accept": "application/sparql-results+json",
    "User-Agent": "5CCSAKNE-CW2-KG-Pipeline/1.0 (university coursework project)",
}
REQUEST_TIMEOUT = 90

RAW_SNAPSHOT_DIR = Path(CONFIG["RAW_DATA_DIR"]) / "wikidata"

# ---------------------------------------------------------------------------
# SPARQL queries
# ---------------------------------------------------------------------------

POLITICIANS_QUERY = """
SELECT DISTINCT
  ?person ?personLabel ?personDescription
  ?partyLabel ?constituencyLabel
  ?genderLabel ?dateOfBirth
WHERE {
  ?person wdt:P31 wd:Q5 ;
          wdt:P106 wd:Q82955 ;
          wdt:P27 wd:Q145 ;
          wdt:P102 ?party .
  OPTIONAL { ?person wdt:P768 ?constituency . }
  OPTIONAL { ?person wdt:P21 ?gender . }
  OPTIONAL { ?person wdt:P569 ?dateOfBirth . }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en" . }
}
LIMIT 2000
"""

POLITICAL_PARTIES_QUERY = """
SELECT DISTINCT
  ?party ?partyLabel ?partyDescription
  ?inception ?dissolved
  ?headquartersLabel ?leaderLabel
WHERE {
  ?party wdt:P31/wdt:P279* wd:Q7278 .
  ?party wdt:P17 wd:Q145 .

  OPTIONAL { ?party wdt:P571 ?inception . }
  OPTIONAL { ?party wdt:P576 ?dissolved . }
  OPTIONAL { ?party wdt:P159 ?headquarters . }
  OPTIONAL { ?party wdt:P488 ?leader . }

  SERVICE wikibase:label { bd:serviceParam wikibase:language "en" . }
}
"""

GOVERNMENT_BODIES_QUERY = """
SELECT DISTINCT
  ?body ?bodyLabel ?bodyDescription
  ?headquartersLabel
WHERE {
  ?body wdt:P17 wd:Q145 .
  ?body wdt:P31 ?type .
  FILTER(?type IN (
    wd:Q11204,
    wd:Q327333,
    wd:Q2001305,
    wd:Q476068,
    wd:Q1752676
  ))

  OPTIONAL { ?body wdt:P159 ?headquarters . }

  SERVICE wikibase:label { bd:serviceParam wikibase:language "en" . }
}
LIMIT 500
"""


# ---------------------------------------------------------------------------
# Execution helpers
# ---------------------------------------------------------------------------


def run_sparql_query(query, label="query"):
    """Execute a SPARQL query against the Wikidata endpoint."""
    print(f"[WIKIDATA] Running {label}...")
    try:
        response = requests.get(
            WIKIDATA_SPARQL_URL,
            params={"query": query},
            headers=REQUEST_HEADERS,
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        data = response.json()
        bindings = data.get("results", {}).get("bindings", [])
        print(f"[WIKIDATA] {label}: {len(bindings)} results")
        return bindings
    except requests.exceptions.RequestException as exc:
        print(f"[WIKIDATA] {label} failed: {exc}")
        return []


def binding_value(binding, key):
    """Extract a plain string value from a SPARQL result binding."""
    entry = binding.get(key)
    if entry is None:
        return None
    return entry.get("value")


def parse_politician(binding):
    """Convert a SPARQL binding row into a politician record."""
    return {
        "wikidata_uri": binding_value(binding, "person"),
        "name": binding_value(binding, "personLabel"),
        "description": binding_value(binding, "personDescription"),
        "party": binding_value(binding, "partyLabel"),
        "constituency": binding_value(binding, "constituencyLabel"),
        "gender": binding_value(binding, "genderLabel"),
        "date_of_birth": binding_value(binding, "dateOfBirth"),
    }


def parse_party(binding):
    """Convert a SPARQL binding row into a political party record."""
    return {
        "wikidata_uri": binding_value(binding, "party"),
        "name": binding_value(binding, "partyLabel"),
        "description": binding_value(binding, "partyDescription"),
        "inception": binding_value(binding, "inception"),
        "dissolved": binding_value(binding, "dissolved"),
        "headquarters": binding_value(binding, "headquartersLabel"),
        "leader": binding_value(binding, "leaderLabel"),
    }


def parse_government_body(binding):
    """Convert a SPARQL binding row into a government body record."""
    return {
        "wikidata_uri": binding_value(binding, "body"),
        "name": binding_value(binding, "bodyLabel"),
        "description": binding_value(binding, "bodyDescription"),
        "headquarters": binding_value(binding, "headquartersLabel"),
    }


def deduplicate_by_name(records):
    """Keep one record per unique name (first occurrence wins)."""
    seen = set()
    deduped = []
    for record in records:
        name = record.get("name")
        if not name or name in seen:
            continue
        seen.add(name)
        deduped.append(record)
    return deduped


def is_valid_label(name):
    """Reject Wikidata URIs or Q-IDs that leaked through as labels."""
    if not name:
        return False
    if name.startswith("http://") or name.startswith("https://"):
        return False
    if len(name) <= 3 and name.startswith("Q") and name[1:].isdigit():
        return False
    return True


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def collect_wikidata(save_snapshot=True):
    """Fetch politicians, parties, and government bodies from Wikidata."""

    # Fetch with a small delay between queries to be polite to the endpoint
    politician_bindings = run_sparql_query(POLITICIANS_QUERY, "politicians")
    time.sleep(2)
    party_bindings = run_sparql_query(POLITICAL_PARTIES_QUERY, "political parties")
    time.sleep(2)
    body_bindings = run_sparql_query(GOVERNMENT_BODIES_QUERY, "government bodies")

    politicians = deduplicate_by_name(
        [
            parse_politician(b)
            for b in politician_bindings
            if is_valid_label(binding_value(b, "personLabel"))
        ]
    )
    parties = deduplicate_by_name(
        [parse_party(b) for b in party_bindings if is_valid_label(binding_value(b, "partyLabel"))]
    )
    government_bodies = deduplicate_by_name(
        [
            parse_government_body(b)
            for b in body_bindings
            if is_valid_label(binding_value(b, "bodyLabel"))
        ]
    )

    payload = {
        "source": "wikidata",
        "endpoint": WIKIDATA_SPARQL_URL,
        "politicians": politicians,
        "political_parties": parties,
        "government_bodies": government_bodies,
    }

    print(
        f"[WIKIDATA] Collected: {len(politicians)} politicians, "
        f"{len(parties)} parties, {len(government_bodies)} government bodies"
    )

    if save_snapshot:
        RAW_SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
        snapshot_path = RAW_SNAPSHOT_DIR / "wikidata_entities.json"
        snapshot_path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        print(f"[WIKIDATA] Saved snapshot to {snapshot_path}")

    return payload


def load_cached_wikidata(snapshot_path=None):
    """Load a previously saved Wikidata snapshot from disk."""
    if snapshot_path is not None:
        path = Path(snapshot_path)
    else:
        path = RAW_SNAPSHOT_DIR / "wikidata_entities.json"

    if not path.exists():
        raise FileNotFoundError(f"[WIKIDATA] Snapshot not found: {path}")

    data = json.loads(path.read_text(encoding="utf-8"))
    print(
        f"[WIKIDATA] Loaded cached snapshot from {path}: "
        f"{len(data.get('politicians', []))} politicians, "
        f"{len(data.get('political_parties', []))} parties, "
        f"{len(data.get('government_bodies', []))} government bodies"
    )
    return data


if __name__ == "__main__":
    payload = collect_wikidata(save_snapshot=True)
    print(
        f"\nResults: {len(payload['politicians'])} politicians, "
        f"{len(payload['political_parties'])} parties, "
        f"{len(payload['government_bodies'])} government bodies"
    )
