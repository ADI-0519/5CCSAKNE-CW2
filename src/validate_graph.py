import argparse
import json
from dataclasses import dataclass
from pathlib import Path

from rdflib import Graph, Namespace

from src.data_normalisation import normalise_name
from src.run_queries import load_kg

NEWS = Namespace("http://example.org/news#")
SCHEMA = Namespace("https://schema.org/")

DEFAULT_COMPLETED_KG_PATH = Path("kg/generated/completed_kg.ttl")
DEFAULT_OUTPUT_PATH = Path("output/validation_results.json")


@dataclass(frozen=True)
class ValidationRule:
    rule_id: str
    title: str
    severity: str
    description: str
    query_text: str


def _row_to_dict(row, variables):
    return {
        str(var): (None if row[var] is None else normalise_name(str(row[var]))) for var in variables
    }


def load_validation_rules():
    prefix_block = "\n".join(
        [
            "PREFIX news: <http://example.org/news#>",
            "PREFIX schema: <https://schema.org/>",
            "PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>",
        ]
    )

    def rule(rule_id, title, severity, description, body):
        return ValidationRule(
            rule_id=rule_id,
            title=title,
            severity=severity,
            description=description,
            query_text=f"{prefix_block}\n\n{body.strip()}",
        )

    return [
        rule(
            "V01",
            "Ministerial statements should identify a department",
            "warning",
            "Every news:MinisterialStatement should carry news:issuedByDepartment.",
            """
            SELECT ?event ?eventName WHERE {
              ?event rdf:type news:MinisterialStatement .
              OPTIONAL { ?event schema:name ?eventName . }
              FILTER NOT EXISTS { ?event news:issuedByDepartment ?department . }
            }
            """,
        ),
        rule(
            "V02",
            "Parliamentary debates should have at least one topic",
            "warning",
            "Every news:ParliamentaryDebate should have news:concernsPolicyTopic.",
            """
            SELECT ?event ?eventName WHERE {
              ?event rdf:type news:ParliamentaryDebate .
              OPTIONAL { ?event schema:name ?eventName . }
              FILTER NOT EXISTS { ?event news:concernsPolicyTopic ?topic . }
            }
            """,
        ),
        rule(
            "V03",
            "Official source records should have sourceSystem",
            "error",
            "Every news:OfficialSourceRecord should declare news:sourceSystem.",
            """
            SELECT ?record ?recordName WHERE {
              ?record rdf:type news:OfficialSourceRecord .
              OPTIONAL { ?record schema:name ?recordName . }
              FILTER NOT EXISTS { ?record news:sourceSystem ?system . }
            }
            """,
        ),
        rule(
            "V04",
            "Official source records should have sourceTitle",
            "error",
            "Every news:OfficialSourceRecord should declare news:sourceTitle.",
            """
            SELECT ?record ?recordName WHERE {
              ?record rdf:type news:OfficialSourceRecord .
              OPTIONAL { ?record schema:name ?recordName . }
              FILTER NOT EXISTS { ?record news:sourceTitle ?title . }
            }
            """,
        ),
        rule(
            "V05",
            "reportedByArticle should point to NewsArticle",
            "error",
            "Every object of news:reportedByArticle should be typed as news:NewsArticle.",
            """
            SELECT ?event ?article WHERE {
              ?event news:reportedByArticle ?article .
              FILTER NOT EXISTS { ?article rdf:type news:NewsArticle . }
            }
            """,
        ),
        rule(
            "V06",
            "memberOfParty subjects should be PoliticalActor",
            "error",
            "Every subject of news:memberOfParty should be typed as news:PoliticalActor.",
            """
            SELECT ?actor ?party WHERE {
              ?actor news:memberOfParty ?party .
              FILTER NOT EXISTS { ?actor rdf:type news:PoliticalActor . }
            }
            """,
        ),
        rule(
            "V07",
            "memberOfParty objects should be PoliticalParty",
            "error",
            "Every object of news:memberOfParty should be typed as news:PoliticalParty.",
            """
            SELECT ?actor ?party WHERE {
              ?actor news:memberOfParty ?party .
              FILTER NOT EXISTS { ?party rdf:type news:PoliticalParty . }
            }
            """,
        ),
        rule(
            "V08",
            "representedInOfficialSource should target OfficialSourceRecord",
            "error",
            "Every object of news:representedInOfficialSource should be typed as news:OfficialSourceRecord.",
            """
            SELECT ?event ?record WHERE {
              ?event news:representedInOfficialSource ?record .
              FILTER NOT EXISTS { ?record rdf:type news:OfficialSourceRecord . }
            }
            """,
        ),
        rule(
            "V09",
            "Policy events should have occursOnDate",
            "warning",
            "Every news:PolicyEvent should declare news:occursOnDate.",
            """
            SELECT ?event ?eventName WHERE {
              ?event rdf:type news:PolicyEvent .
              OPTIONAL { ?event schema:name ?eventName . }
              FILTER NOT EXISTS { ?event news:occursOnDate ?eventDate . }
            }
            """,
        ),
        rule(
            "V10",
            "matchedToSourceRecord should target SourceRecord",
            "error",
            "Every object of news:matchedToSourceRecord should be typed as news:SourceRecord.",
            """
            SELECT ?event ?record WHERE {
              ?event news:matchedToSourceRecord ?record .
              FILTER NOT EXISTS { ?record rdf:type news:SourceRecord . }
            }
            """,
        ),
        rule(
            "V11",
            "reportedByArticle should originate from PolicyEvent",
            "error",
            "Every subject of news:reportedByArticle should be typed as news:PolicyEvent.",
            """
            SELECT ?event ?article WHERE {
              ?event news:reportedByArticle ?article .
              FILTER NOT EXISTS { ?event rdf:type news:PolicyEvent . }
            }
            """,
        ),
        rule(
            "V12",
            "issuedByDepartment should imply involvesGovernmentBody",
            "warning",
            "Every news:issuedByDepartment object should also appear through news:involvesGovernmentBody for the same event.",
            """
            SELECT ?event ?department ?eventName WHERE {
              ?event news:issuedByDepartment ?department .
              OPTIONAL { ?event schema:name ?eventName . }
              FILTER NOT EXISTS { ?event news:involvesGovernmentBody ?department . }
            }
            """,
        ),
        rule(
            "V13",
            "Policy events should be grounded in a source",
            "warning",
            "Every news:PolicyEvent should have news:reportedByArticle or news:representedInOfficialSource.",
            """
            SELECT ?event ?eventName WHERE {
              ?event rdf:type news:PolicyEvent .
              OPTIONAL { ?event schema:name ?eventName . }
              FILTER NOT EXISTS { ?event news:reportedByArticle ?article . }
              FILTER NOT EXISTS { ?event news:representedInOfficialSource ?record . }
            }
            """,
        ),
        rule(
            "V14",
            "Parliamentary debates should identify a parliamentary body",
            "warning",
            "Every news:ParliamentaryDebate should carry news:occursInParliamentaryBody.",
            """
            SELECT ?event ?eventName WHERE {
              ?event rdf:type news:ParliamentaryDebate .
              OPTIONAL { ?event schema:name ?eventName . }
              FILTER NOT EXISTS { ?event news:occursInParliamentaryBody ?body . }
            }
            """,
        ),
        rule(
            "V15",
            "Government policy events should involve a government body",
            "warning",
            "Every news:GovernmentPolicyEvent should carry news:involvesGovernmentBody.",
            """
            SELECT ?event ?eventName WHERE {
              ?event rdf:type news:GovernmentPolicyEvent .
              OPTIONAL { ?event schema:name ?eventName . }
              FILTER NOT EXISTS { ?event news:involvesGovernmentBody ?body . }
            }
            """,
        ),
        rule(
            "V16",
            "News articles should have a publisher",
            "error",
            "Every news:NewsArticle should declare news:publishedBy.",
            """
            SELECT ?article ?headline WHERE {
              ?article rdf:type news:NewsArticle .
              OPTIONAL { ?article schema:headline ?headline . }
              FILTER NOT EXISTS { ?article news:publishedBy ?publisher . }
            }
            """,
        ),
        rule(
            "V17",
            "News articles should have an articleURL",
            "error",
            "Every news:NewsArticle should declare news:articleURL.",
            """
            SELECT ?article ?headline WHERE {
              ?article rdf:type news:NewsArticle .
              OPTIONAL { ?article schema:headline ?headline . }
              FILTER NOT EXISTS { ?article news:articleURL ?url . }
            }
            """,
        ),
    ]


def execute_validation(graph: Graph, rules=None):
    rules = rules or load_validation_rules()
    results = []

    for rule in rules:
        query_result = graph.query(rule.query_text)
        variables = list(query_result.vars)
        rows = [_row_to_dict(row, variables) for row in query_result]
        results.append(
            {
                "rule_id": rule.rule_id,
                "title": rule.title,
                "severity": rule.severity,
                "description": rule.description,
                "violation_count": len(rows),
                "passed": len(rows) == 0,
                "variables": [str(var) for var in variables],
                "rows": rows,
            }
        )

    severity_totals = {}
    failed_rules = 0
    total_violations = 0
    for result in results:
        severity_totals[result["severity"]] = (
            severity_totals.get(result["severity"], 0) + result["violation_count"]
        )
        total_violations += result["violation_count"]
        if not result["passed"]:
            failed_rules += 1

    return {
        "rule_count": len(results),
        "failed_rule_count": failed_rules,
        "total_violations": total_violations,
        "severity_totals": severity_totals,
        "results": results,
    }


def save_validation_report(report, output_path=DEFAULT_OUTPUT_PATH):
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Run SPARQL-based graph validation checks.")
    parser.add_argument("--kg", type=Path, default=DEFAULT_COMPLETED_KG_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    args = parser.parse_args()

    graph = load_kg(args.kg)
    report = execute_validation(graph)
    save_validation_report(report, args.output)

    print(f"[VALIDATE] KG: {args.kg}")
    print(
        f"[VALIDATE] {report['rule_count']} rules checked, "
        f"{report['failed_rule_count']} failed, {report['total_violations']} violations found."
    )
    for result in report["results"]:
        status = "PASS" if result["passed"] else "FAIL"
        print(f"[VALIDATE] {result['rule_id']} {status}: {result['violation_count']} violation(s)")


if __name__ == "__main__":
    main()
