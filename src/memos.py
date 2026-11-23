"""Credit memos. Ratios are filled from the calculated file. They are not retyped."""

from __future__ import annotations

from pathlib import Path

from src.underwriting import memo as underwriting_memo


def _m(value: float | None, digits: int = 1) -> str:
    if value is None:
        return "n.m."
    return f"{value / 1_000_000:,.{digits}f}"


def _x(value: float | None) -> str:
    if value is None:
        return "n.m."
    return f"{value:.2f}x"


def _pct(value: float | None) -> str:
    if value is None:
        return "n.m."
    return f"{value * 100:.1f}%"


def company_memo(company: dict, history: list[dict], scored: dict) -> str:
    latest = history[-1]
    prior = history[-2] if len(history) > 1 else None
    result = scored["result"]
    lines = [
        f"# {company['name']} ({company['ticker']})",
        "",
        f"Prepared by Vanuja Ekanayake, BBA Finance candidate, Baruch College Zicklin School of Business.",
        "",
        f"Recommendation: **{result.category}**. Composite {result.composite:.2f} on a 1.00 to 4.00 scale "
        f"for the fiscal year ended {latest['period_end']}.",
        "",
        company["business"],
        company.get("analytical_note", "").strip(),
        "",
        f"Figures are the latest Form 10-K amounts on file for each period end. "
        f"The fiscal {latest['fiscal_year']} column used in this memo is taken from {latest['filing_url']}.",
        "",
        "## Reported results",
        "",
        "| Item | Amount ($ millions) | Basis | Tag |",
        "| --- | ---: | --- | --- |",
    ]
    statement = [
        ("Revenue", "revenue", "revenue_tag"),
        ("Gross profit", "gross_profit", "gross_profit_tag"),
        ("Operating income", "operating_income", "operating_income_tag"),
        ("Depreciation and amortization", "depreciation_and_amortization", "depreciation_and_amortization_tag"),
        ("EBITDA", "ebitda", None),
        ("Income-statement interest", "interest_is", "interest_is_tag"),
        ("Cash interest paid", "interest_paid", "interest_paid_tag"),
        ("Interest used in coverage", "interest", "interest_tag"),
        ("Short-term borrowings", "short_term_borrowings", None),
        ("Current portion of long-term debt", "current_portion_long_term_debt", None),
        ("Long-term debt", "long_term_debt", None),
        ("Total debt", "total_debt", None),
        ("Cash and cash equivalents", "cash", "cash_tag"),
        ("Short-term investments (not in net debt)", "short_term_investments", "short_term_investments_tag"),
        ("Net debt", "net_debt", None),
        ("Capital expenditure", "capex", "capex_tag"),
        ("Cash from operations", "cfo", "cfo_tag"),
        ("Free cash flow", "fcf", None),
        ("Impairment losses (not added back)", "impairment", "impairment_tag"),
    ]
    for label, key, tag_key in statement:
        if key not in latest or latest.get(key) is None and key != "finance_lease_liability":
            if latest.get(key) is None:
                continue
        debt_tags = latest.get("debt_tags") or {}
        tag = latest.get(tag_key) if tag_key else "calculated"
        if key in debt_tags and debt_tags[key]:
            tag = debt_tags[key]
        if key == "ebitda":
            tag = "operating income + D&A"
        if key in {"total_debt", "net_debt", "fcf"}:
            tag = "calculated"
        lines.append(f"| {label} | {_m(latest.get(key))} | reported | {tag or ''} |")
    if latest.get("interest_note"):
        lines.append("")
        lines.append(latest["interest_note"])
    if latest.get("total_debt_note"):
        lines.append(latest["total_debt_note"])
    if latest.get("finance_leases_included") and latest.get("finance_lease_liability") is not None:
        lines.append(
            f"Finance lease liabilities of {_m(latest['finance_lease_liability'])} million were inside the debt tags and have been subtracted."
        )
    elif latest.get("finance_lease_liability"):
        lines.append(
            f"Finance lease liabilities of {_m(latest['finance_lease_liability'])} million are tagged separately from funded debt and are not in total debt."
        )
    if latest.get("operating_lease_liability"):
        lines.append(
            f"Operating lease liabilities of {_m(latest['operating_lease_liability'])} million are excluded from total debt."
        )
    if latest.get("impairment"):
        lines.append(
            f"Impairment losses of {_m(latest['impairment'])} million are disclosed in the filing "
            f"({latest.get('impairment_tag')}). EBITDA does not add them back."
        )
    lines.extend(["", "## Ratios and score", ""])
    lines.append("| Ratio | Value | Weight | Points | Bucket | Weighted points | Why it scored this way |")
    lines.append("| --- | ---: | ---: | ---: | --- | ---: | --- |")
    for row in result.rows:
        if row.value is None:
            value = "n.m."
        elif row.ratio_id == "debt_to_capitalization":
            value = _pct(row.value)
        elif row.ratio_id == "current_ratio":
            value = f"{row.value:.2f}x"
        else:
            value = _x(row.value)
        points = "" if row.points is None else str(row.points)
        weighted = "" if row.weighted_points is None else f"{row.weighted_points:.2f}"
        lines.append(
            f"| {row.label} | {value} | {row.effective_weight:.0%} | {points} | {row.bucket or ''} | {weighted} | {row.note} |"
        )
    lines.append("")
    lines.append(
        f"Gross margin {_pct(latest.get('gross_margin'))}. EBITDA margin {_pct(latest.get('ebitda_margin'))}. "
        f"Quick ratio {_x(latest.get('quick_ratio'))}. Free cash flow {_m(latest.get('fcf'))} million. "
        "Quick ratio and gross margin are reported and are not separate scorecard lines. "
        "The current ratio is the liquidity line in the scorecard. Quick ratio is (current assets − inventory) / current liabilities."
    )
    held_down = [row for row in result.drivers() if row.points is not None and row.points < 4]
    lines.append("")
    if held_down:
        names = ", ".join(f"{row.label} ({row.points} points, {row.bucket})" for row in held_down)
        lines.append(f"Ratios below the top bucket: {names}.")
    else:
        lines.append("Every scored ratio is in the top bucket.")
    if prior is not None:
        lines.append("")
        lines.append(
            f"Prior fiscal year ended {prior['period_end']}: Debt/EBITDA {_x(prior.get('debt_to_ebitda'))}, "
            f"EBITDA/Interest {_x(prior.get('ebitda_to_interest'))}, "
            f"FCF {_m(prior.get('fcf'))} million."
        )
    lines.extend([
        "",
        "## Limits of this memo",
        "",
        "Total debt excludes operating leases and, where the issuer's debt tags contain them, finance leases.",
        "Net debt does not deduct short-term investments.",
        "EBITDA is operating income plus depreciation and amortization. It does not add back impairments, stock-based compensation, or restructuring.",
        "This is not a rating-agency opinion and it is not a commitment to lend.",
        "",
    ])
    return "\n".join(lines)


def write_memos(companies: list[dict], history: list[dict], scored_latest: list[dict],
                underwriting: dict, directory: Path) -> list[Path]:
    directory.mkdir(parents=True, exist_ok=True)
    written = []
    by_company = {company["ticker"]: company for company in companies}
    for scored in scored_latest:
        ticker = scored["ticker"]
        rows = [row for row in history if row["ticker"] == ticker]
        text = company_memo(by_company[ticker], rows, scored)
        path = directory / f"{ticker}.md"
        path.write_text(text)
        written.append(path)
    fictional = directory / "FICTIONAL_northbridge.md"
    fictional.write_text(underwriting_memo(underwriting))
    written.append(fictional)
    summary = directory / "portfolio_summary.md"
    summary.write_text(_summary(scored_latest))
    written.append(summary)
    return written


def _summary(scored_latest: list[dict]) -> str:
    lines = [
        "# Portfolio summary",
        "",
        "Same definitions, five different balance sheets. The composite is the published weighted score for the latest fiscal year.",
        "",
        "| Company | FY | Debt/EBITDA | Net debt/EBITDA | EBITDA/Interest | Composite | Result |",
        "| --- | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in scored_latest:
        statement = row["statement"]
        lines.append(
            f"| {row['ticker']} | {row['fiscal_year']} | {_x(statement.get('debt_to_ebitda'))} | "
            f"{_x(statement.get('net_debt_to_ebitda'))} | {_x(statement.get('ebitda_to_interest'))} | "
            f"{row['result'].composite:.2f} | {row['result'].category} |"
        )
    lines.append("")
    lines.append("A negative net-debt multiple is a net cash position. n.m. means the multiple is not meaningful, which here is EBITDA that is not positive.")
    lines.append("")
    return "\n".join(lines)
