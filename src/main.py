"""Run the credit file from the cached Form 10-K facts.

    python -m src.main

Use --refresh to call EDGAR again. The cache is otherwise sufficient, and the
test suite does not call the network.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

from src.charts import coverage_trend, leverage_trend, scorecard_comparison
from src.edgar import cache_company, extract_company, load_universe, original_filings, repo_root
from src.excel_report import build as build_workbook
from src.memos import write_memos
from src.ratios import compute
from src.scorecard import load_scorecard, score_inputs
from src.underwriting import load_borrower, underwrite
from src.validation import render as render_validation


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Corporate credit analysis from SEC Form 10-K facts.")
    parser.add_argument("--refresh", action="store_true", help="Download companyfacts again instead of using data/raw.")
    return parser


def _load_json(path: Path) -> dict:
    with path.open() as handle:
        return json.load(handle)


def run(refresh: bool = False) -> dict:
    root = repo_root()
    universe = load_universe(root / "config" / "universe.yaml")
    scorecard = load_scorecard(root / "config" / "scorecard.yaml")
    raw_dir = root / "data" / "raw"
    processed = root / "data" / "processed"
    reports = root / "reports"
    processed.mkdir(parents=True, exist_ok=True)

    history = []
    lineage = []
    filing_rows = []
    for company in universe["companies"]:
        facts_path, submissions_path = cache_company(company["cik"], raw_dir, refresh=refresh)
        facts = _load_json(facts_path)
        submissions = _load_json(submissions_path)
        rows, lines = extract_company(facts, submissions, company, universe)
        for row in rows:
            computed = compute(row)
            computed["result"] = score_inputs(computed, scorecard)
            history.append(computed)
        lineage.extend(lines)
        for filing in original_filings(submissions, company["cik"]):
            if filing["report_date"] >= "2021-01-01":
                filing_rows.append({"ticker": company["ticker"], "company": company["name"], **filing})

    history.sort(key=lambda row: (row["ticker"], row["period_end"]))
    latest = []
    for company in universe["companies"]:
        rows = [row for row in history if row["ticker"] == company["ticker"]]
        if not rows:
            raise RuntimeError(f"No annual 10-K rows extracted for {company['ticker']}.")
        current = rows[-1]
        latest.append({
            "ticker": current["ticker"],
            "company": current["company"],
            "fiscal_year": current["fiscal_year"],
            "period_end": current["period_end"],
            "statement": current,
            "result": current["result"],
        })

    borrower = load_borrower(root / "data" / "fictional_northbridge_precision_FICTIONAL.yaml")
    package = underwrite(borrower)

    _write_tables(processed, history, lineage, filing_rows, latest)
    build_workbook(history, latest, package, reports / "credit_analysis.xlsx")
    chart_dir = reports / "charts"
    chart_dir.mkdir(parents=True, exist_ok=True)
    leverage_trend(history, chart_dir / "leverage_trend.png")
    coverage_trend(history, chart_dir / "coverage_trend.png")
    scorecard_comparison(latest, chart_dir / "scorecard_comparison.png")
    write_memos(universe["companies"], history, latest, package, reports / "memos")
    validation_text, failures = render_validation(history)
    (reports / "validation.md").write_text(validation_text)

    summary = _summary(latest, package, failures)
    print(summary)
    if failures:
        raise SystemExit(1)
    return {"history": history, "latest": latest, "underwriting": package, "summary": summary}


def _write_tables(processed: Path, history, lineage, filing_rows, latest) -> None:
    statement_columns = [
        "ticker", "company", "cik", "fiscal_year", "period_start", "period_end", "filed",
        "accession", "filing_url", "revenue", "revenue_tag", "gross_profit", "gross_profit_tag",
        "operating_income", "operating_income_tag", "depreciation_and_amortization",
        "depreciation_and_amortization_tag", "ebitda", "interest_is", "interest_is_tag", "interest_tag",
        "interest_paid", "interest", "interest_note", "short_term_borrowings",
        "current_portion_long_term_debt", "long_term_debt", "finance_leases_included",
        "finance_lease_liability", "operating_lease_liability", "total_debt", "total_debt_note",
        "cash", "short_term_investments", "net_debt", "capex", "capex_tag", "cfo", "fcf",
        "cash_taxes", "impairment", "impairment_tag", "current_assets", "current_liabilities",
        "inventory", "equity", "gross_margin", "ebitda_margin", "debt_to_ebitda",
        "net_debt_to_ebitda", "ebitda_to_interest", "ebitda_minus_capex_to_interest",
        "cfo_to_debt", "fcf_to_debt", "current_ratio", "quick_ratio", "debt_to_capitalization",
    ]
    statements = pd.DataFrame(history)
    keep = [column for column in statement_columns if column in statements.columns]
    statements[keep].to_csv(processed / "annual_statements.csv", index=False)
    pd.DataFrame(lineage).to_csv(processed / "lineage.csv", index=False)
    pd.DataFrame(filing_rows).to_csv(processed / "filings.csv", index=False)
    score_rows = []
    for item in latest:
        for row in item["result"].rows:
            score_rows.append({
                "ticker": item["ticker"],
                "fiscal_year": item["fiscal_year"],
                "period_end": item["period_end"],
                "ratio": row.label,
                "value": row.value,
                "published_weight": row.published_weight,
                "effective_weight": row.effective_weight,
                "points": row.points,
                "bucket": row.bucket,
                "weighted_points": row.weighted_points,
                "note": row.note,
                "composite": item["result"].composite,
                "category": item["result"].category,
            })
    pd.DataFrame(score_rows).to_csv(processed / "scorecard.csv", index=False)


def _summary(latest, package, failures) -> str:
    lines = [
        "Corporate credit analysis",
        "Source: SEC EDGAR companyfacts, Form 10-K, cache in data/raw",
        "",
        "Latest scorecard",
        f"{'Ticker':<8}{'FY':<6}{'Debt/EBITDA':>14}{'EBITDA/Int.':>14}{'Score':>8}  Result",
    ]
    for item in latest:
        statement = item["statement"]
        def turns(value):
            return "n.m." if value is None else f"{value:.2f}x"
        lines.append(
            f"{item['ticker']:<8}{item['fiscal_year']:<6}{turns(statement.get('debt_to_ebitda')):>14}"
            f"{turns(statement.get('ebitda_to_interest')):>14}{item['result'].composite:>8.2f}  {item['result'].category}"
        )
    sized = package["sizing"]
    recommended = package["recommended"]
    lines.extend([
        "",
        "Underwriting: FICTIONAL Northbridge Precision Components, LLC",
        f"Requested: ${sized['requested']:,.0f}",
        f"Recommended commitment: ${sized['commitment']:,.0f}",
        f"Binding constraint: {sized['binding_constraint']}",
        f"Year-1 DSCR: {recommended['dscr']:.2f}x",
        f"Year-1 leverage: {recommended['leverage']:.2f}x",
        f"Schedule reconciles: {package['schedule_reconciles']}",
        "",
        "Validation: " + ("Microsoft FY2025 and the fiscal 2025 spot checks passed." if not failures else "FAILED"),
    ])
    for failure in failures:
        lines.append(f"  {failure}")
    lines.extend([
        "Outputs: reports/credit_analysis.xlsx, reports/charts/, reports/memos/, reports/validation.md",
    ])
    return "\n".join(lines)


def main() -> None:
    args = _parser().parse_args()
    run(refresh=args.refresh)


if __name__ == "__main__":
    main()
