"""Credit ratios.

Each metric is defined here and nowhere else in the code. Other modules call
these functions. They do not restate the formulas.

EBITDA
    Operating income + depreciation and amortization.
    Depreciation and amortization is the annual Form 10-K amount selected in
    this order: DepreciationDepletionAndAmortization, then
    DepreciationAndAmortization, then the sum of Depreciation and
    AmortizationOfIntangibleAssets. The cash-flow line "depreciation,
    amortization, and other" is not used when it contains amounts beyond
    depreciation and amortization.

Gross margin
    Gross profit / revenue.
    Gross profit is the reported GrossProfit fact when that annual fact
    exists. Otherwise it is revenue minus cost of revenue.

EBITDA margin
    EBITDA / revenue.

Total debt
    Short-term borrowings + current portion of long-term debt + long-term debt.
    Operating lease liabilities are excluded. They are never added.
    Finance lease liabilities are excluded. When the long-term debt tags are
    the combined debt-and-capital-lease concepts, the finance lease liability
    is subtracted. When the debt tags do not contain finance leases, nothing
    is subtracted and the exclusion is noted.

Net debt
    Total debt minus cash and cash equivalents.
    Short-term investments and other marketable securities are not deducted.

Debt / EBITDA
    Total debt / EBITDA.
    Not meaningful when EBITDA is not positive.

Net debt / EBITDA
    Net debt / EBITDA.
    Not meaningful when EBITDA is not positive. A negative result is a net cash position.

EBITDA / Interest
    EBITDA / interest burden.

(EBITDA - capex) / Interest
    (EBITDA - capital expenditure) / interest burden.

Interest burden
    The income-statement interest fact, in this order:
    InterestExpenseNonoperating, InterestAndDebtExpense, InterestExpense,
    InterestExpenseDebt.
    If the fact used is the generic InterestExpense tag and cash interest paid
    exceeds it by more than 25 percent, cash interest paid is the burden.
    That rule exists because some issuers tag a net interest-and-other line as
    InterestExpense. Cash interest paid is InterestPaid, or InterestPaidNet
    when InterestPaid is absent.

Capital expenditure
    PaymentsToAcquirePropertyPlantAndEquipment, or
    PaymentsToAcquireProductiveAssets when the first tag is absent.
    The amount is a cash outflow. A payments tag reported with a negative sign
    is stored as a positive outflow, and the sign is noted.

CFO / Debt
    Net cash from operating activities / total debt.

Current ratio
    Current assets / current liabilities.

Quick ratio
    (Current assets - inventory) / current liabilities.
    Prepaid expenses and other current assets remain in the numerator.
    This is not a cash-only ratio.

Debt / capitalization
    Total debt / (total debt + stockholders' equity).
    Equity is the parent's stockholders' equity. Noncontrolling interest is
    not added.

Free cash flow
    Net cash from operating activities minus capital expenditure.

Debt service coverage, used only in the underwriting module
    Defined in src/underwriting.py. It is not a historical ratio for the
    SEC issuers, because scheduled principal is not a single 10-K line.
"""

from __future__ import annotations

INTEREST_TAGS = (
    "InterestExpenseNonoperating",
    "InterestAndDebtExpense",
    "InterestExpense",
    "InterestExpenseDebt",
)

GENERIC_INTEREST_TAG = "InterestExpense"
CASH_INTEREST_SWITCH = 1.25


def ebitda(operating_income: float | None, depreciation_and_amortization: float | None) -> float | None:
    """See the module docstring."""
    if operating_income is None or depreciation_and_amortization is None:
        return None
    return operating_income + depreciation_and_amortization


def total_debt(
    short_term_borrowings: float | None,
    current_portion_long_term_debt: float | None,
    long_term_debt: float | None,
    finance_lease_liability: float | None = None,
    finance_leases_included: bool = False,
) -> tuple[float | None, str]:
    """See the module docstring. Returns the total and a one-line note."""
    parts = (short_term_borrowings, current_portion_long_term_debt, long_term_debt)
    if any(part is None for part in parts):
        return None, "A debt component is missing, so total debt is not computed."
    gross = short_term_borrowings + current_portion_long_term_debt + long_term_debt
    if not finance_leases_included:
        return gross, "Operating and finance lease liabilities are excluded. The debt tags used do not contain them."
    if finance_lease_liability is None:
        return (
            gross,
            "The debt tags include capital leases, and no finance lease liability was tagged to subtract.",
        )
    return (
        gross - finance_lease_liability,
        "Finance lease liability subtracted. Operating lease liabilities were not added.",
    )


def net_debt(debt: float | None, cash: float | None) -> float | None:
    """See the module docstring."""
    if debt is None or cash is None:
        return None
    return debt - cash


def interest_burden(
    interest_is: float | None,
    interest_tag: str | None,
    interest_paid: float | None,
) -> tuple[float | None, str, str | None]:
    """See the module docstring. Returns the burden, the reason, and the tag used."""
    if interest_is is None and interest_paid is None:
        return None, "Interest was not tagged.", None
    if interest_is is None:
        return interest_paid, "Income-statement interest was not tagged. Cash interest paid is used.", "InterestPaid"
    if (
        interest_tag == GENERIC_INTEREST_TAG
        and interest_paid is not None
        and interest_is > 0
        and interest_paid > interest_is * CASH_INTEREST_SWITCH
    ):
        return (
            interest_paid,
            "Cash interest paid is used. It exceeds the generic InterestExpense tag by more than 25 percent.",
            "InterestPaid",
        )
    return interest_is, f"Income-statement tag {interest_tag} is used.", interest_tag


def _div(numerator: float | None, denominator: float | None) -> float | None:
    if numerator is None or denominator is None or denominator == 0:
        return None
    return numerator / denominator


def compute(row: dict) -> dict:
    """Add EBITDA, debt totals, and every ratio to a statement row.

    Inputs are dollar amounts already selected from a filing, plus the debt
    flags ``finance_leases_included`` and ``interest_tag``. Missing inputs
    stay missing. This function does not fill them with zero.
    """
    out = dict(row)
    out["ebitda"] = ebitda(row.get("operating_income"), row.get("depreciation_and_amortization"))
    debt, debt_note = total_debt(
        row.get("short_term_borrowings"),
        row.get("current_portion_long_term_debt"),
        row.get("long_term_debt"),
        row.get("finance_lease_liability"),
        bool(row.get("finance_leases_included")),
    )
    out["total_debt"] = debt
    out["total_debt_note"] = debt_note
    out["net_debt"] = net_debt(debt, row.get("cash"))
    burden, burden_note, burden_tag = interest_burden(
        row.get("interest_is"),
        row.get("interest_tag"),
        row.get("interest_paid"),
    )
    out["interest"] = burden
    out["interest_note"] = burden_note
    out["interest_is_tag"] = row.get("interest_tag")
    if burden_tag == "InterestPaid":
        out["interest_tag"] = row.get("interest_paid_tag") or burden_tag
    else:
        out["interest_tag"] = burden_tag or row.get("interest_tag")
    capex = row.get("capex")
    cfo = row.get("cfo")
    out["fcf"] = None if cfo is None or capex is None else cfo - capex
    revenue = row.get("revenue")
    out["gross_margin"] = _div(row.get("gross_profit"), revenue)
    out["ebitda_margin"] = _div(out["ebitda"], revenue)
    ebitda_value = out["ebitda"]
    out["debt_to_ebitda"] = None if ebitda_value is None or ebitda_value <= 0 else _div(debt, ebitda_value)
    out["net_debt_to_ebitda"] = None if ebitda_value is None or ebitda_value <= 0 else _div(out["net_debt"], ebitda_value)
    usable_interest = burden if burden is not None and burden > 0 else None
    coverage_base = ebitda_value if ebitda_value is not None and ebitda_value > 0 else None
    out["ebitda_to_interest"] = _div(coverage_base, usable_interest)
    ebitda_minus_capex = None if ebitda_value is None or capex is None else ebitda_value - capex
    out["ebitda_minus_capex"] = ebitda_minus_capex
    coverage_after_capex = ebitda_minus_capex if ebitda_value is not None and ebitda_value > 0 else None
    out["ebitda_minus_capex_to_interest"] = _div(coverage_after_capex, usable_interest)
    out["cfo_to_debt"] = _div(cfo, debt)
    out["fcf_to_debt"] = _div(out["fcf"], debt)
    out["current_ratio"] = _div(row.get("current_assets"), row.get("current_liabilities"))
    inventory = row.get("inventory")
    current_assets = row.get("current_assets")
    quick_numerator = None if current_assets is None or inventory is None else current_assets - inventory
    out["quick_ratio"] = _div(quick_numerator, row.get("current_liabilities"))
    equity = row.get("equity")
    capitalization = None if debt is None or equity is None else debt + equity
    out["debt_to_capitalization"] = None if capitalization is None or capitalization <= 0 else _div(debt, capitalization)
    return out
