"""SEC EDGAR companyfacts pull and annual Form 10-K extraction.

Figures are read from
https://data.sec.gov/api/xbrl/companyfacts/CIK##########.json.
The User-Agent identifies this project. It contains no email address and no
phone number. A User-Agent that contains "github.com" is rejected by the
SEC edge with HTTP 403, so the header does not include that URL.

The client sleeps between requests. The SEC fair-access policy is 10 requests
per second. Cached JSON in data/raw is reused unless a refresh is requested.
Tests must not call the network. They read fixtures or the cache.
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

import yaml

USER_AGENT = "corporate-credit-analysis research Vanuja-E"
REQUEST_PAUSE_SECONDS = 0.2
COMPANYFACTS_URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik}.json"

REVENUE_TAGS = (
    "Revenues",
    "RevenueFromContractWithCustomerExcludingAssessedTax",
    "RevenueFromContractWithCustomerIncludingAssessedTax",
    "SalesRevenueNet",
)
GROSS_PROFIT_TAGS = ("GrossProfit",)
COST_TAGS = (
    "CostOfRevenue",
    "CostOfGoodsAndServicesSold",
    "CostOfGoodsSold",
    "CostOfSales",
)
DA_TAGS = (
    "DepreciationDepletionAndAmortization",
    "DepreciationAndAmortization",
)
DEPRECIATION_TAG = "Depreciation"
AMORTIZATION_TAG = "AmortizationOfIntangibleAssets"
CAPEX_TAGS = (
    "PaymentsToAcquirePropertyPlantAndEquipment",
    "PaymentsToAcquireProductiveAssets",
)
CASH_INTEREST_TAGS = ("InterestPaid", "InterestPaidNet")
IMPAIRMENT_TAGS = (
    "GoodwillAndIntangibleAssetImpairment",
    "AssetImpairmentCharges",
)
FLOW_TAGS = (
    "OperatingIncomeLoss",
    "NetCashProvidedByUsedInOperatingActivities",
    "IncomeTaxesPaidNet",
    "IncomeTaxesPaid",
    DEPRECIATION_TAG,
    AMORTIZATION_TAG,
    *REVENUE_TAGS,
    *GROSS_PROFIT_TAGS,
    *COST_TAGS,
    *DA_TAGS,
    *CAPEX_TAGS,
    *CASH_INTEREST_TAGS,
    *IMPAIRMENT_TAGS,
    "InterestExpenseNonoperating",
    "InterestAndDebtExpense",
    "InterestExpense",
    "InterestExpenseDebt",
)
STOCK_TAGS = (
    "LongTermDebt",
    "LongTermDebtCurrent",
    "LongTermDebtNoncurrent",
    "LongTermDebtAndCapitalLeaseObligations",
    "LongTermDebtAndCapitalLeaseObligationsCurrent",
    "LongTermDebtAndCapitalLeaseObligationsIncludingCurrentMaturities",
    "DebtCurrent",
    "ShortTermBorrowings",
    "CommercialPaper",
    "FinanceLeaseLiability",
    "OperatingLeaseLiability",
    "CashAndCashEquivalentsAtCarryingValue",
    "ShortTermInvestments",
    "AssetsCurrent",
    "LiabilitiesCurrent",
    "InventoryNet",
    "StockholdersEquity",
)


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_universe(path: Path | None = None) -> dict:
    path = path or repo_root() / "config" / "universe.yaml"
    with path.open() as handle:
        return yaml.safe_load(handle)


def _cik10(cik: str) -> str:
    return str(cik).zfill(10)


def filing_url(cik: str, accession: str, primary_document: str | None = None) -> str:
    cik_n = str(int(cik))
    accession_compact = accession.replace("-", "")
    base = f"https://www.sec.gov/Archives/edgar/data/{cik_n}/{accession_compact}"
    if primary_document:
        return f"{base}/{primary_document}"
    return f"{base}/{accession}-index.html"


def fetch_json(url: str, dest: Path, refresh: bool = False) -> Path:
    """Download one JSON document, or return the cache."""
    if dest.exists() and dest.stat().st_size > 0 and not refresh:
        return dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(
        url,
        headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=180) as response:
            payload = response.read()
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"EDGAR request failed for {url}: HTTP {exc.code}") from exc
    dest.write_bytes(payload)
    time.sleep(REQUEST_PAUSE_SECONDS)
    return dest


def cache_company(cik: str, raw_dir: Path, refresh: bool = False) -> tuple[Path, Path]:
    cik10 = _cik10(cik)
    facts = fetch_json(
        COMPANYFACTS_URL.format(cik=cik10),
        raw_dir / f"CIK{cik10}.json",
        refresh=refresh,
    )
    submissions = fetch_json(
        SUBMISSIONS_URL.format(cik=cik10),
        raw_dir / f"CIK{cik10}_submissions.json",
        refresh=refresh,
    )
    return facts, submissions


def _parse_date(value: str) -> datetime:
    return datetime.strptime(value, "%Y-%m-%d")


def _annual_duration(fact: dict) -> bool:
    start = fact.get("start")
    end = fact.get("end")
    if not start or not end:
        return False
    days = (_parse_date(end) - _parse_date(start)).days
    return 300 <= days <= 380


def _frame_rank(fact: dict) -> tuple:
    frame = fact.get("frame") or ""
    if len(frame) == 6 and frame.startswith("CY") and frame[2:].isdigit():
        rank = 0
    elif frame and "Q" not in frame:
        rank = 1
    elif not frame:
        rank = 2
    else:
        rank = 3
    return (rank, fact.get("accn") or "")


def choose_fact(facts: list[dict]) -> tuple[dict | None, str]:
    """Keep one annual fact per period end. Latest filing wins.

    Form 10-K and fiscal-period FY are required before this function is called.
    A later filing's comparative column replaces the original column. That is
    the restated figure of record. The accession of the chosen fact is the cite.
    """
    if not facts:
        return None, ""
    filed = max(fact.get("filed") or "" for fact in facts)
    pool = [fact for fact in facts if (fact.get("filed") or "") == filed]
    pool.sort(key=_frame_rank)
    chosen = pool[0]
    values = {fact.get("val") for fact in pool}
    note = ""
    if len(values) > 1:
        shown = ", ".join(str(value) for value in sorted(values, key=lambda item: (item is None, item)))
        note = f"Same filing date carried more than one value ({shown}). The annual frame was kept."
    return chosen, note


def index_tag(node: dict | None, flow: bool) -> dict[str, list[dict]]:
    grouped: dict[str, list[dict]] = {}
    if not node:
        return grouped
    for fact in node.get("units", {}).get("USD", []):
        if fact.get("form") != "10-K" or fact.get("fp") != "FY" or not fact.get("end"):
            continue
        if flow and not _annual_duration(fact):
            continue
        if not flow and fact.get("start"):
            continue
        grouped.setdefault(fact["end"], []).append(fact)
    return grouped


def _pick(grouped: dict[str, list[dict]], end: str) -> tuple[dict | None, str]:
    return choose_fact(grouped.get(end, []))


def _first_tag(indexes: dict[str, dict[str, list[dict]]], tags: tuple[str, ...], end: str):
    for tag in tags:
        fact, note = _pick(indexes.get(tag, {}), end)
        if fact is not None and fact.get("val") is not None:
            return tag, fact, note
    return None, None, ""


def _amount(fact: dict | None, payments: bool = False) -> tuple[float | None, str]:
    if fact is None or fact.get("val") is None:
        return None, ""
    value = float(fact["val"])
    note = ""
    if payments and value < 0:
        value = abs(value)
        note = "Payments tag was negative. Stored as a positive cash outflow."
    return value, note


def _submission_index(payload: dict) -> dict[str, dict]:
    recent = payload.get("filings", {}).get("recent", {})
    forms = recent.get("form", [])
    found: dict[str, dict] = {}
    for index, form in enumerate(forms):
        if form != "10-K":
            continue
        accession = recent["accessionNumber"][index]
        found[accession] = {
            "form": form,
            "filed": recent["filingDate"][index],
            "report_date": recent["reportDate"][index],
            "primary_document": recent["primaryDocument"][index],
        }
    return found


def _cite(cik: str, fact: dict, submissions: dict[str, dict]) -> dict:
    accession = fact.get("accn") or ""
    meta = submissions.get(accession, {})
    return {
        "accession": accession,
        "filed": fact.get("filed"),
        "form": fact.get("form"),
        "frame": fact.get("frame"),
        "filing_url": filing_url(cik, accession, meta.get("primary_document")),
        "filing_index_url": filing_url(cik, accession, None),
    }


def _debt_components(indexes: dict, end: str) -> dict:
    """Select the balance-sheet debt lines for one period end.

    The arithmetic of total debt is in ratios.total_debt. This function only
    chooses tags and splits a combined current-debt line when that is how the
    issuer tagged short-term borrowings and current maturities.
    """
    def value(tag: str) -> float | None:
        fact, _note = _pick(indexes.get(tag, {}), end)
        if fact is None or fact.get("val") is None:
            return None
        return float(fact["val"])

    notes: list[str] = []
    tags: dict[str, str] = {}
    long_term = value("LongTermDebtNoncurrent")
    current = value("LongTermDebtCurrent")
    finance_included = False
    if long_term is not None and current is not None:
        tags["long_term_debt"] = "LongTermDebtNoncurrent"
        tags["current_portion_long_term_debt"] = "LongTermDebtCurrent"
        reported_total = value("LongTermDebt")
        if reported_total is not None and abs(reported_total - (long_term + current)) > 1_000_000:
            notes.append(
                "LongTermDebt differs from current plus noncurrent by more than $1 million. "
                "Current and noncurrent carrying amounts are used."
            )
        short_term, short_tag, short_note = _short_term(indexes, end)
        notes.extend(short_note)
        tags["short_term_borrowings"] = short_tag
    elif (
        value("LongTermDebtAndCapitalLeaseObligations") is not None
        and value("LongTermDebtAndCapitalLeaseObligationsCurrent") is not None
    ):
        long_term = value("LongTermDebtAndCapitalLeaseObligations")
        current = value("LongTermDebtAndCapitalLeaseObligationsCurrent")
        tags["long_term_debt"] = "LongTermDebtAndCapitalLeaseObligations"
        tags["current_portion_long_term_debt"] = "LongTermDebtAndCapitalLeaseObligationsCurrent"
        finance_included = True
        notes.append("Long-term debt tags are the combined debt and capital-lease concepts.")
        short_term, short_tag, short_note = _short_term(indexes, end)
        notes.extend(short_note)
        tags["short_term_borrowings"] = short_tag
    elif value("DebtCurrent") is not None and value("LongTermDebtNoncurrent") is not None:
        long_term = value("LongTermDebtNoncurrent")
        tags["long_term_debt"] = "LongTermDebtNoncurrent"
        debt_current = value("DebtCurrent")
        reported_long = value("LongTermDebt")
        if reported_long is not None:
            current = reported_long - long_term
            short_term = debt_current - current
            tags["current_portion_long_term_debt"] = "LongTermDebt minus LongTermDebtNoncurrent"
            tags["short_term_borrowings"] = "DebtCurrent residual after current maturities"
            if -1_000_000 <= short_term < 0:
                short_term = 0.0
            if short_term < -1_000_000:
                notes.append("DebtCurrent is below implied current maturities. DebtCurrent is used as the whole current balance.")
                current = debt_current
                short_term = 0.0
                tags["current_portion_long_term_debt"] = "DebtCurrent"
                tags["short_term_borrowings"] = "included in DebtCurrent"
        else:
            current = debt_current
            short_term = 0.0
            tags["current_portion_long_term_debt"] = "DebtCurrent"
            tags["short_term_borrowings"] = "included in DebtCurrent"
        notes.append(
            "DebtCurrent is treated as short-term borrowings plus current maturities, "
            "so it is not added on top of a separate short-term tag."
        )
    else:
        long_term = value("LongTermDebtNoncurrent")
        current = value("LongTermDebtCurrent")
        short_term, short_tag, short_note = _short_term(indexes, end)
        notes.append("The debt-tag set is incomplete for this period.")
        notes.extend(short_note)
        tags["short_term_borrowings"] = short_tag
    return {
        "short_term_borrowings": short_term,
        "current_portion_long_term_debt": current,
        "long_term_debt": long_term,
        "finance_leases_included": finance_included,
        "finance_lease_liability": value("FinanceLeaseLiability"),
        "operating_lease_liability": value("OperatingLeaseLiability"),
        "debt_tags": tags,
        "debt_notes": notes,
    }


def _short_term(indexes: dict, end: str) -> tuple[float, str, list[str]]:
    found = []
    for tag in ("ShortTermBorrowings", "CommercialPaper"):
        fact, _note = _pick(indexes.get(tag, {}), end)
        if fact is not None and fact.get("val") is not None:
            found.append((tag, float(fact["val"])))
    if not found:
        return 0.0, "not tagged; treated as zero", ["Short-term borrowings were not tagged and are treated as zero."]
    tag, amount = max(found, key=lambda item: item[1])
    notes = []
    if len(found) == 2 and abs(found[0][1] - found[1][1]) > 1_000_000:
        notes.append(
            "ShortTermBorrowings and CommercialPaper differ. The larger balance is used so the two are not added."
        )
    return amount, tag, notes


def extract_company(facts_payload: dict, submissions_payload: dict, company: dict, settings: dict) -> tuple[list[dict], list[dict]]:
    """Return annual statement rows and a tag-level lineage."""
    gaap = facts_payload.get("facts", {}).get("us-gaap", {})
    indexes: dict[str, dict[str, list[dict]]] = {}
    for tag in set(FLOW_TAGS + STOCK_TAGS):
        indexes[tag] = index_tag(gaap.get(tag), flow=tag in set(FLOW_TAGS))
    filings = _submission_index(submissions_payload)
    ends = set()
    for tag in REVENUE_TAGS:
        ends.update(indexes.get(tag, {}))
    min_year = int(settings.get("min_fiscal_year", 2021))
    max_years = int(settings.get("max_years", 5))
    kept = sorted(end for end in ends if int(end[:4]) >= min_year and int(end[5:7]) >= 6)
    if len(kept) > max_years:
        kept = kept[-max_years:]

    rows: list[dict] = []
    lineage: list[dict] = []
    cik = company["cik"]
    for end in kept:
        revenue_tag, revenue_fact, revenue_note = _first_tag(indexes, REVENUE_TAGS, end)
        if revenue_fact is None:
            continue
        revenue, _sign = _amount(revenue_fact)
        record = {
            "ticker": company["ticker"],
            "company": company["name"],
            "cik": cik,
            "sector": company["sector"],
            "fiscal_year": int(end[:4]),
            "period_start": revenue_fact.get("start"),
            "period_end": end,
            "revenue": revenue,
            "revenue_tag": revenue_tag,
        }
        record.update(_cite(cik, revenue_fact, filings))
        lineage.append(_line(record, "revenue", revenue_tag, revenue, revenue_fact, revenue_note))

        def take_flow(metric: str, tags: tuple[str, ...], payments: bool = False):
            tag, fact, note = _first_tag(indexes, tags, end)
            amount, sign_note = _amount(fact, payments=payments)
            notes = " ".join(part for part in (note, sign_note) if part)
            record[metric] = amount
            record[f"{metric}_tag"] = tag
            if fact is not None:
                lineage.append(_line(record, metric, tag, amount, fact, notes))
            elif notes:
                lineage.append(_line(record, metric, tag, amount, {"filed": None, "accn": None, "form": "10-K", "frame": None}, notes))

        take_flow("operating_income", ("OperatingIncomeLoss",))
        take_flow("gross_profit_reported", GROSS_PROFIT_TAGS)
        take_flow("cost_of_revenue", COST_TAGS)
        take_flow("da_combined", DA_TAGS)
        take_flow("depreciation", (DEPRECIATION_TAG,))
        take_flow("amortization", (AMORTIZATION_TAG,))
        take_flow("capex", CAPEX_TAGS, payments=True)
        take_flow("cfo", ("NetCashProvidedByUsedInOperatingActivities",))
        take_flow("interest_paid", CASH_INTEREST_TAGS)
        take_flow("cash_taxes", ("IncomeTaxesPaidNet", "IncomeTaxesPaid"))
        take_flow("impairment", IMPAIRMENT_TAGS)
        interest_tag, interest_fact, interest_note = _first_tag(indexes, (
            "InterestExpenseNonoperating",
            "InterestAndDebtExpense",
            "InterestExpense",
            "InterestExpenseDebt",
        ), end)
        interest_amount, _sign = _amount(interest_fact)
        record["interest_is"] = interest_amount
        record["interest_tag"] = interest_tag
        if interest_fact is not None:
            lineage.append(_line(record, "interest_is", interest_tag, interest_amount, interest_fact, interest_note))

        if record["da_combined"] is not None:
            record["depreciation_and_amortization"] = record["da_combined"]
            record["depreciation_and_amortization_tag"] = record["da_combined_tag"]
        elif record["depreciation"] is not None and record["amortization"] is not None:
            record["depreciation_and_amortization"] = record["depreciation"] + record["amortization"]
            record["depreciation_and_amortization_tag"] = f"{DEPRECIATION_TAG} + {AMORTIZATION_TAG}"
            lineage.append(_line(
                record, "depreciation_and_amortization", record["depreciation_and_amortization_tag"],
                record["depreciation_and_amortization"], revenue_fact,
                "Sum of the depreciation and intangible-amortization tags. No combined tag was reported.",
            ))
        elif record["depreciation"] is not None:
            record["depreciation_and_amortization"] = record["depreciation"]
            record["depreciation_and_amortization_tag"] = DEPRECIATION_TAG
        else:
            record["depreciation_and_amortization"] = None
            record["depreciation_and_amortization_tag"] = None

        if record["gross_profit_reported"] is not None:
            record["gross_profit"] = record["gross_profit_reported"]
            record["gross_profit_tag"] = record["gross_profit_reported_tag"]
        elif record["cost_of_revenue"] is not None and revenue is not None:
            record["gross_profit"] = revenue - record["cost_of_revenue"]
            record["gross_profit_tag"] = f"{revenue_tag} - {record['cost_of_revenue_tag']}"
            lineage.append(_line(
                record, "gross_profit", record["gross_profit_tag"], record["gross_profit"], revenue_fact,
                "Calculated as revenue minus cost of revenue. GrossProfit was not tagged for this period.",
            ))
        else:
            record["gross_profit"] = None
            record["gross_profit_tag"] = None

        for stock_metric, stock_tags in (
            ("cash", ("CashAndCashEquivalentsAtCarryingValue",)),
            ("short_term_investments", ("ShortTermInvestments",)),
            ("current_assets", ("AssetsCurrent",)),
            ("current_liabilities", ("LiabilitiesCurrent",)),
            ("inventory", ("InventoryNet",)),
            ("equity", ("StockholdersEquity",)),
        ):
            tag, fact, note = _first_tag(indexes, stock_tags, end)
            amount, _sign = _amount(fact)
            record[stock_metric] = amount
            record[f"{stock_metric}_tag"] = tag
            if fact is not None:
                lineage.append(_line(record, stock_metric, tag, amount, fact, note))

        debt = _debt_components(indexes, end)
        record.update(debt)
        note_by_metric = {
            "short_term_borrowings": [
                note for note in debt["debt_notes"]
                if "Short-term" in note or "CommercialPaper" in note or "DebtCurrent" in note
            ],
            "current_portion_long_term_debt": [
                note for note in debt["debt_notes"]
                if "current" in note.lower() or "DebtCurrent" in note
            ],
            "long_term_debt": [
                note for note in debt["debt_notes"]
                if "Long-term" in note or "LongTermDebt" in note or "incomplete" in note or "capital-lease" in note
            ],
            "finance_lease_liability": [
                note for note in debt["debt_notes"] if "capital" in note.lower() or "Finance" in note
            ],
        }
        for metric in (
            "short_term_borrowings",
            "current_portion_long_term_debt",
            "long_term_debt",
            "finance_lease_liability",
            "operating_lease_liability",
        ):
            tag = debt["debt_tags"].get(metric, "")
            fact = None
            raw_tag = tag if tag in indexes else None
            if raw_tag:
                fact, _pick_note = _pick(indexes.get(raw_tag, {}), end)
            else:
                _pick_note = ""
            if record.get(metric) is not None:
                lineage.append(_line(
                    record, metric, tag or metric, record.get(metric),
                    fact or {"filed": record.get("filed"), "accn": record.get("accession"), "form": "10-K", "frame": None},
                    " ".join(note_by_metric.get(metric, [])) or _pick_note,
                ))
        rows.append(record)
    return rows, lineage


def _line(record: dict, metric: str, tag, value, fact: dict, note: str) -> dict:
    return {
        "ticker": record["ticker"],
        "fiscal_year": record["fiscal_year"],
        "period_end": record["period_end"],
        "metric": metric,
        "tag": tag,
        "value": value,
        "filed": fact.get("filed") if fact else None,
        "accession": fact.get("accn") if fact else record.get("accession"),
        "form": "10-K",
        "frame": fact.get("frame") if fact else None,
        "filing_url": record.get("filing_url"),
        "note": note,
    }


def original_filings(submissions_payload: dict, cik: str) -> list[dict]:
    """Form 10-K documents whose report date is the fiscal year end."""
    rows = []
    for accession, meta in _submission_index(submissions_payload).items():
        rows.append({
            "accession": accession,
            "form": meta["form"],
            "report_date": meta["report_date"],
            "filed": meta["filed"],
            "filing_url": filing_url(cik, accession, meta["primary_document"]),
        })
    rows.sort(key=lambda item: item["report_date"])
    return rows
