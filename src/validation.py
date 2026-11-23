"""Tie reported model amounts back to Form 10-K face figures.

Microsoft's fiscal year ended June 30, 2025 was read from the financial
statements in the Form 10-K filed July 30, 2025. The other rows were read
from the consolidated statements or the debt notes of each issuer's fiscal
2025 Form 10-K. Amounts are dollars.
"""

from __future__ import annotations

from pathlib import Path

FACE = [
    {
        "ticker": "MSFT",
        "period_end": "2025-06-30",
        "filing_url": "https://www.sec.gov/Archives/edgar/data/789019/000095017025100235/msft-20250630.htm",
        "filing": "Form 10-K for the year ended June 30, 2025, filed July 30, 2025",
        "checks": {
            "revenue": 281_724_000_000,
            "operating_income": 128_528_000_000,
            "depreciation": 22_000_000_000,
            "amortization": 6_000_000_000,
            "depreciation_and_amortization": 28_000_000_000,
            "interest": 2_385_000_000,
            "short_term_borrowings": 0,
            "current_portion_long_term_debt": 2_999_000_000,
            "long_term_debt": 40_152_000_000,
            "total_debt": 43_151_000_000,
            "cash": 30_242_000_000,
            "cfo": 136_162_000_000,
            "capex": 64_551_000_000,
            "current_assets": 191_131_000_000,
            "current_liabilities": 141_218_000_000,
            "inventory": 938_000_000,
            "equity": 343_479_000_000,
            "ebitda": 156_528_000_000,
        },
        "narrative": (
            "The income statement reports revenue of $281,724 million and operating income of $128,528 million. "
            "The debt lines are short-term debt of $0, current portion of long-term debt of $2,999 million, "
            "and long-term debt of $40,152 million. Interest expense in the other-income note is $2,385 million. "
            "Depreciation of $22,000 million and amortization of intangible assets of $6,000 million are the "
            "us-gaap facts in that filing. EBITDA in this model is $156,528 million, the sum of operating income and those two amounts. "
            "The cash-flow line 'depreciation, amortization, and other' is $34,153 million. The $6,153 million difference is the 'other' component and is not included in EBITDA."
        ),
    },
    {
        "ticker": "PEP",
        "period_end": "2025-12-27",
        "filing_url": "https://www.sec.gov/Archives/edgar/data/77476/000007747626000007/pep-20251227.htm",
        "filing": "Form 10-K for the year ended December 27, 2025, filed February 3, 2026",
        "checks": {
            "revenue": 93_925_000_000,
            "operating_income": 11_498_000_000,
            "depreciation_and_amortization": 3_451_000_000,
            "interest_is": 1_121_000_000,
            "current_portion_long_term_debt": 4_030_000_000,
            "long_term_debt": 42_321_000_000,
            "short_term_borrowings": 2_831_000_000,
            "total_debt": 49_182_000_000,
            "cash": 9_159_000_000,
        },
        "narrative": (
            "Short-term debt obligations on the balance sheet are $6,861 million. The debt note splits that into "
            "current maturities of long-term debt of $4,030 million and the remainder, which is commercial paper and other short-term debt. "
            "Long-term debt obligations are $42,321 million. Total debt is $49,182 million. "
            "The income-statement line 'net interest expense and other' is $1,121 million. Cash interest paid, disclosed in the supplemental cash-flow information, is the coverage denominator when the 25 percent rule applies."
        ),
    },
    {
        "ticker": "HON",
        "period_end": "2025-12-31",
        "filing_url": "https://www.sec.gov/Archives/edgar/data/773840/000077384026000013/hon-20251231.htm",
        "filing": "Form 10-K for the year ended December 31, 2025, filed February 17, 2026",
        "checks": {
            "revenue": 37_442_000_000,
            "operating_income": 8_127_000_000,
            "depreciation_and_amortization": 1_388_000_000,
            "interest": 1_344_000_000,
            "short_term_borrowings": 5_893_000_000,
            "current_portion_long_term_debt": 1_546_000_000,
            "long_term_debt": 27_141_000_000,
            "finance_lease_liability": 64_000_000,
            "total_debt": 34_516_000_000,
            "cash": 12_487_000_000,
        },
        "narrative": (
            "The balance sheet reports commercial paper and other short-term borrowings of $5,893 million, "
            "current maturities of long-term debt of $1,546 million, and long-term debt of $27,141 million. "
            "Those debt lines include finance lease liabilities of $64 million, which this model subtracts. "
            "Operating lease liabilities are not added. Interest and other financial charges are $1,344 million. "
            "Depreciation and amortization in the cash-flow discussion is $1,388 million."
        ),
    },
    {
        "ticker": "KHC",
        "period_end": "2025-12-27",
        "filing_url": "https://www.sec.gov/Archives/edgar/data/1637459/000163745926000009/khc-20251227.htm",
        "filing": "Form 10-K for the year ended December 27, 2025, filed February 12, 2026",
        "checks": {
            "revenue": 24_942_000_000,
            "operating_income": -4_669_000_000,
            "depreciation_and_amortization": 968_000_000,
            "interest": 947_000_000,
            "short_term_borrowings": 0,
            "current_portion_long_term_debt": 1_908_000_000,
            "long_term_debt": 19_311_000_000,
            "finance_lease_liability": 160_000_000,
            "total_debt": 21_059_000_000,
            "impairment": 9_306_000_000,
        },
        "narrative": (
            "Operating income is a loss of $4,669 million. The filing presents impairment losses of $9,306 million "
            "above that line. EBITDA does not add the impairment back. Current portion of long-term debt is $1,908 million "
            "and long-term debt is $19,311 million. Finance lease obligations of $160 million are subtracted because the tagged debt concepts include capital leases. "
            "Interest expense is $947 million."
        ),
    },
    {
        "ticker": "CCL",
        "period_end": "2025-11-30",
        "filing_url": "https://www.sec.gov/Archives/edgar/data/815097/000081509726000007/ccl-20251130.htm",
        "filing": "Form 10-K for the year ended November 30, 2025, filed January 27, 2026",
        "checks": {
            "revenue": 26_622_000_000,
            "operating_income": 4_483_000_000,
            "depreciation_and_amortization": 2_790_000_000,
            "interest": 1_349_000_000,
            "short_term_borrowings": 0,
            "current_portion_long_term_debt": 2_603_000_000,
            "long_term_debt": 24_037_000_000,
            "total_debt": 26_640_000_000,
        },
        "narrative": (
            "Total revenues are $26,622 million and operating income is $4,483 million. "
            "Current portion of long-term debt is $2,603 million and long-term debt is $24,037 million. "
            "The note total, net of unamortized debt issuance costs and discounts, is $26,640 million. "
            "Interest expense, net of capitalized interest, is $1,349 million. Operating lease liabilities are presented separately and are not in total debt."
        ),
    },
]

LABELS = {
    "revenue": "Revenue",
    "operating_income": "Operating income",
    "depreciation": "Depreciation",
    "amortization": "Amortization of intangibles",
    "depreciation_and_amortization": "D&A used in EBITDA",
    "interest": "Interest burden",
    "interest_is": "Income-statement interest tag",
    "short_term_borrowings": "Short-term borrowings",
    "current_portion_long_term_debt": "Current portion of long-term debt",
    "long_term_debt": "Long-term debt",
    "finance_lease_liability": "Finance lease liability",
    "total_debt": "Total debt",
    "cash": "Cash",
    "cfo": "Cash from operations",
    "capex": "Capital expenditure",
    "current_assets": "Current assets",
    "current_liabilities": "Current liabilities",
    "inventory": "Inventory",
    "equity": "Stockholders' equity",
    "ebitda": "EBITDA",
    "impairment": "Impairment losses",
}


def compare(history: list[dict]) -> tuple[list[dict], list[str]]:
    indexed = {(row["ticker"], row["period_end"]): row for row in history}
    results = []
    failures = []
    for spec in FACE:
        row = indexed.get((spec["ticker"], spec["period_end"]))
        if row is None:
            failures.append(f"{spec['ticker']} {spec['period_end']} was not extracted.")
            continue
        for field, face in spec["checks"].items():
            model = row.get(field)
            if field == "finance_lease_liability" and not row.get("finance_leases_included"):
                model = row.get("finance_lease_liability")
            ok = model is not None and abs(model - face) < 1.0
            results.append({
                "ticker": spec["ticker"],
                "period_end": spec["period_end"],
                "filing": spec["filing"],
                "filing_url": spec["filing_url"],
                "field": field,
                "label": LABELS.get(field, field),
                "model": model,
                "face": face,
                "match": ok,
            })
            if not ok:
                failures.append(f"{spec['ticker']} {field}: model {model} vs 10-K {face}")
    return results, failures


def render(history: list[dict]) -> tuple[str, list[str]]:
    results, failures = compare(history)
    lines = [
        "# Validation against Form 10-K financial statements",
        "",
        "The model amount is the figure produced from the SEC companyfacts cache. The 10-K amount is the figure read from the filing cited on the row. Dollars, not millions. A match is a difference below one dollar.",
        "",
        "Microsoft's fiscal 2025 Form 10-K is the primary hand check. Revenue, operating income, depreciation, amortization, the debt lines, interest expense, and the two ratios below were read from that filing. The other issuers are the same test on the fiscal 2025 statements.",
        "",
        "| Company | Period end | Item | Model | 10-K | Match | Filing |",
        "| --- | --- | --- | ---: | ---: | --- | --- |",
    ]
    for item in results:
        mark = "yes" if item["match"] else "NO"
        model = "missing" if item["model"] is None else f"{item['model']:,.0f}"
        lines.append(
            f"| {item['ticker']} | {item['period_end']} | {item['label']} | {model} | {item['face']:,.0f} | {mark} | {item['filing_url']} |"
        )
    msft = next(row for row in history if row["ticker"] == "MSFT" and row["period_end"] == "2025-06-30")
    debt_ebitda = msft["total_debt"] / msft["ebitda"]
    coverage = msft["ebitda"] / msft["interest"]
    lines.extend([
        "",
        "## Microsoft fiscal 2025 ratios",
        "",
        FACE[0]["narrative"],
        "",
        f"Debt / EBITDA = {msft['total_debt']:,.0f} / {msft['ebitda']:,.0f} = {debt_ebitda:.4f}x.",
        f"EBITDA / Interest = {msft['ebitda']:,.0f} / {msft['interest']:,.0f} = {coverage:.2f}x.",
        "",
        "Both ratios use only the tied amounts above. Debt is short-term debt plus the current portion of long-term debt plus long-term debt. Finance leases and operating leases are not in that total. EBITDA is operating income plus depreciation plus amortization of intangibles.",
        "",
        "## Notes on the other filings",
        "",
    ])
    for spec in FACE[1:]:
        lines.append(f"**{spec['ticker']}.** {spec['narrative']} Filing: {spec['filing_url']}")
        lines.append("")
    lines.append("No amount in this file was typed in as a substitute for a missing filing figure. Where the model and the 10-K differ, the match column says NO.")
    lines.append("")
    return "\n".join(lines), failures
