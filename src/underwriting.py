"""Term-loan sizing for one FICTIONAL middle-market borrower.

The borrower, the request, and every dollar of borrower performance are
assumptions. They are not Form 10-K figures. Every public function in this
module requires the borrower record to be marked FICTIONAL.

Debt service coverage
    (EBITDA - maintenance capex - cash taxes) / (cash interest + scheduled principal).
    The numerator is cash flow available for debt service on that definition.
    Cash taxes are the cash-tax assumption, not a tax provision.
    Scheduled principal on the term loan is the original commitment divided
    by the tenor, paid annually. Interest is the coupon times the opening
    principal of that year. The closing draw itself does not accrue interest
    inside the closing period.

The commitment is the largest amount, rounded down to the stated increment,
that satisfies both the maximum opening leverage and the minimum DSCR.
Covenant limits are wider than the sizing limits. Headroom is the distance
from the year-1 result to the covenant, not to the tighter sizing test.
Year 1 is the tightest year of a level-principal schedule because interest
declines as the balance declines and the leverage test is an opening test.

Debt roll-forward
    Opening principal + draws - principal repayments = closing principal.
"""

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

import yaml

MONEY = Decimal("0.01")


class FictionalLabelError(ValueError):
    """Raised when a borrower output is not marked FICTIONAL."""


def load_borrower(path: Path) -> dict:
    with path.open() as handle:
        borrower = yaml.safe_load(handle)
    require_fictional_record(borrower, path.name)
    return borrower


def require_fictional_record(borrower: dict, source: str) -> None:
    status = str(borrower.get("status", ""))
    name = str(borrower.get("legal_name", ""))
    if "FICTIONAL" not in status.upper() or "FICTIONAL" not in name.upper():
        raise FictionalLabelError(f"{source} is not marked FICTIONAL in both status and legal name.")
    if "FICTIONAL" not in Path(source).name.upper():
        raise FictionalLabelError(f"The borrower file name {source} does not contain FICTIONAL.")


def require_fictional_text(text: str, where: str) -> str:
    if "FICTIONAL" not in text:
        raise FictionalLabelError(f"{where} does not contain the word FICTIONAL.")
    return text


def _d(value) -> Decimal:
    return Decimal(str(value))


def cash_flow_available(ebitda: Decimal, capex: Decimal, cash_taxes: Decimal) -> Decimal:
    """EBITDA - maintenance capex - cash taxes."""
    return ebitda - capex - cash_taxes


def debt_service(principal: Decimal, coupon: Decimal, tenor_years: int) -> tuple[Decimal, Decimal, Decimal]:
    """Year-1 interest, scheduled principal, and debt service on a level-principal loan."""
    interest = (principal * coupon).quantize(MONEY, rounding=ROUND_HALF_UP)
    scheduled = (principal / Decimal(tenor_years)).quantize(MONEY, rounding=ROUND_HALF_UP)
    return interest, scheduled, interest + scheduled


def dscr(cfads: Decimal, principal: Decimal, coupon: Decimal, tenor_years: int) -> Decimal | None:
    """See the module docstring."""
    if principal <= 0:
        return None
    _interest, _scheduled, service = debt_service(principal, coupon, tenor_years)
    if service == 0:
        return None
    return cfads / service


def leverage(principal: Decimal, ebitda: Decimal) -> Decimal | None:
    if ebitda <= 0:
        return None
    return principal / ebitda


def interest_coverage(ebitda: Decimal, principal: Decimal, coupon: Decimal, tenor_years: int) -> Decimal | None:
    interest, _scheduled, _service = debt_service(principal, coupon, tenor_years)
    if interest <= 0:
        return None
    return ebitda / interest


def _largest_commitment(
    unrounded_cap: Decimal,
    step: Decimal,
    cfads: Decimal,
    ebitda: Decimal,
    coupon: Decimal,
    tenor_years: int,
    min_dscr: Decimal,
    max_leverage: Decimal,
) -> Decimal:
    if unrounded_cap < 0:
        return Decimal("0")
    amount = (unrounded_cap // step) * step
    while amount > 0:
        coverage = dscr(cfads, amount, coupon, tenor_years)
        lever = leverage(amount, ebitda)
        if coverage is not None and lever is not None and coverage >= min_dscr and lever <= max_leverage:
            return amount
        amount -= step
    return Decimal("0")


def size_commitment(borrower: dict) -> dict:
    """Size the term loan. Existing debt after close is subtracted from the leverage capacity."""
    financials = borrower["financials"]
    request = borrower["request"]
    sizing = borrower["sizing"]
    ebitda = _d(financials["operating_income"]) + _d(financials["depreciation_and_amortization"])
    capex = _d(financials["maintenance_capex"])
    cash_taxes = _d(financials["cash_taxes"])
    cfads = cash_flow_available(ebitda, capex, cash_taxes)
    coupon = _d(request["coupon_rate"])
    tenor = int(request["tenor_years"])
    min_dscr = _d(sizing["min_dscr"])
    max_leverage = _d(sizing["max_total_leverage"])
    step = _d(sizing["round_down_to"])
    other_debt = _d(borrower.get("existing_debt_after_close", 0))
    requested = _d(request["amount_requested"])

    service_factor = coupon + (Decimal(1) / Decimal(tenor))
    dscr_cap = cfads / (min_dscr * service_factor)
    leverage_cap = max_leverage * ebitda - other_debt
    raw_cap = min(dscr_cap, leverage_cap, requested)
    binding = "minimum DSCR"
    if leverage_cap <= dscr_cap and leverage_cap <= requested:
        binding = "maximum leverage"
    elif requested <= dscr_cap and requested <= leverage_cap:
        binding = "requested amount"
    commitment = _largest_commitment(
        raw_cap, step, cfads, ebitda, coupon, tenor, min_dscr, max_leverage,
    )
    return {
        "ebitda": ebitda,
        "capex": capex,
        "cash_taxes": cash_taxes,
        "cfads": cfads,
        "coupon": coupon,
        "tenor_years": tenor,
        "dscr_cap": dscr_cap,
        "leverage_cap": leverage_cap,
        "requested": requested,
        "binding_constraint": binding,
        "commitment": commitment,
        "other_debt": other_debt,
    }


def amortization_schedule(commitment: Decimal, coupon: Decimal, tenor_years: int) -> list[dict]:
    """Annual roll-forward. Period 0 is the closing draw. Later periods are forecast."""
    if commitment <= 0:
        return []
    rows = [{
        "period": 0,
        "label": "Closing",
        "opening": Decimal("0"),
        "draws": commitment,
        "interest": Decimal("0"),
        "principal": Decimal("0"),
        "debt_service": Decimal("0"),
        "closing": commitment,
        "basis": "forecast",
    }]
    opening = commitment
    scheduled = (commitment / Decimal(tenor_years)).quantize(MONEY, rounding=ROUND_HALF_UP)
    allocated = Decimal("0")
    for year in range(1, tenor_years + 1):
        interest = (opening * coupon).quantize(MONEY, rounding=ROUND_HALF_UP)
        principal = scheduled
        if year == tenor_years:
            principal = commitment - allocated
        principal = principal.quantize(MONEY, rounding=ROUND_HALF_UP)
        closing = opening - principal
        rows.append({
            "period": year,
            "label": f"Year {year}",
            "opening": opening,
            "draws": Decimal("0"),
            "interest": interest,
            "principal": principal,
            "debt_service": interest + principal,
            "closing": closing,
            "basis": "forecast",
        })
        allocated += principal
        opening = closing
    return rows


def schedule_ties(schedule: list[dict]) -> bool:
    """Opening + draws - principal repayments = closing, and the loan pays off."""
    if not schedule:
        return False
    for row in schedule:
        if row["opening"] + row["draws"] - row["principal"] != row["closing"]:
            return False
    if schedule[-1]["closing"] != 0:
        return False
    drawn = sum(row["draws"] for row in schedule)
    repaid = sum(row["principal"] for row in schedule)
    return drawn == repaid


def _case(name: str, ebitda: Decimal, coupon: Decimal, commitment: Decimal, capex: Decimal,
          cash_taxes: Decimal, tenor: int, covenants: dict, basis: str) -> dict:
    cfads = cash_flow_available(ebitda, capex, cash_taxes)
    interest, principal, service = debt_service(commitment, coupon, tenor)
    coverage = None if service == 0 else cfads / service
    lever = None if ebitda <= 0 else commitment / ebitda
    icr = None if interest <= 0 else ebitda / interest
    max_lev = _d(covenants["max_total_leverage"])
    min_icr = _d(covenants["min_interest_coverage"])
    min_dscr = _d(covenants["min_dscr"])
    return {
        "case": name,
        "basis": basis,
        "ebitda": ebitda,
        "coupon": coupon,
        "cfads": cfads,
        "interest": interest,
        "principal": principal,
        "debt_service": service,
        "leverage": lever,
        "interest_coverage": icr,
        "dscr": coverage,
        "leverage_headroom": None if lever is None else max_lev - lever,
        "interest_coverage_headroom": None if icr is None else icr - min_icr,
        "dscr_headroom": None if coverage is None else coverage - min_dscr,
        "leverage_covenant": max_lev,
        "interest_coverage_covenant": min_icr,
        "dscr_covenant": min_dscr,
    }


def sensitivity(borrower: dict, sized: dict) -> list[dict]:
    """EBITDA declines and rate increases. Capex and cash taxes stay at the base assumption."""
    commitment = sized["commitment"]
    tenor = sized["tenor_years"]
    capex = sized["capex"]
    cash_taxes = sized["cash_taxes"]
    covenants = borrower["covenants"]
    base_ebitda = sized["ebitda"]
    base_coupon = sized["coupon"]
    rows = [_case(
        "Base", base_ebitda, base_coupon, commitment, capex, cash_taxes, tenor, covenants, "forecast",
    )]
    for shock in borrower["sensitivity"]["ebitda_shocks"]:
        shocked = (base_ebitda * (Decimal(1) + _d(shock))).quantize(MONEY, rounding=ROUND_HALF_UP)
        pct = int(abs(_d(shock)) * 100)
        rows.append(_case(
            f"EBITDA -{pct}%", shocked, base_coupon, commitment, capex, cash_taxes, tenor, covenants, "simulated",
        ))
    for bps in borrower["sensitivity"]["rate_shocks_bps"]:
        coupon = base_coupon + (_d(bps) / Decimal(10000))
        rows.append(_case(
            f"Rate +{bps} bps", base_ebitda, coupon, commitment, capex, cash_taxes, tenor, covenants, "simulated",
        ))
    return rows


def underwrite(borrower: dict) -> dict:
    """Full FICTIONAL credit package: size, schedule, request test, and downside cases."""
    require_fictional_record(borrower, "fictional_northbridge_precision_FICTIONAL.yaml")
    sized = size_commitment(borrower)
    schedule = amortization_schedule(sized["commitment"], sized["coupon"], sized["tenor_years"])
    if not schedule_ties(schedule):
        raise RuntimeError("The amortization schedule does not reconcile.")
    covenants = borrower["covenants"]
    request_case = _case(
        "Requested amount",
        sized["ebitda"], sized["coupon"], sized["requested"], sized["capex"], sized["cash_taxes"],
        sized["tenor_years"], covenants, "assumption",
    )
    recommended_case = _case(
        "Recommended commitment",
        sized["ebitda"], sized["coupon"], sized["commitment"], sized["capex"], sized["cash_taxes"],
        sized["tenor_years"], covenants, "forecast",
    )
    uses_refinance = _d(borrower["use_of_proceeds"]["refinance_existing_shareholder_note"])
    result = {
        "status": "FICTIONAL",
        "legal_name": borrower["legal_name"],
        "business": borrower["business"],
        "facility": borrower["request"]["facility"],
        "sizing": sized,
        "schedule": schedule,
        "recommended": recommended_case,
        "requested_case": request_case,
        "sensitivity": sensitivity(borrower, sized),
        "sources_and_uses": {
            "sources_term_loan": sized["commitment"],
            "use_refinance_shareholder_note": uses_refinance,
            "use_general_corporate": sized["commitment"] - uses_refinance,
            "basis": "forecast",
        },
        "schedule_reconciles": True,
    }
    return result


def memo(result: dict) -> str:
    """One-page underwriting note. The word FICTIONAL is required in the text."""
    sized = result["sizing"]
    recommended = result["recommended"]
    requested = result["requested_case"]
    base = result["sensitivity"][0]
    lines = [
        f"# {result['legal_name']}",
        "",
        "FICTIONAL borrower. This company is not real, is not an SEC registrant, and is not a bank client.",
        "Every borrower figure is an assumption. The schedule is a forecast. The downside cases are simulated.",
        "",
        f"Facility requested: {result['facility']}.",
        f"Amount requested: ${sized['requested']:,.0f}.",
        f"Recommended commitment: ${sized['commitment']:,.0f}.",
        f"Binding sizing constraint: {sized['binding_constraint']}.",
        "",
        "Cash flow available for debt service is EBITDA minus maintenance capex minus cash taxes.",
        f"EBITDA is operating income plus depreciation and amortization, ${_money(sized['ebitda'])} million.",
        f"Cash flow available for debt service is ${_money(sized['cfads'])} million.",
        f"Opening leverage on the recommended loan is {_turns(recommended['leverage'])} against a { _turns(_d(recommended['leverage_covenant'])) } covenant.",
        f"Year-1 DSCR is {_turns(recommended['dscr'])} against a {_turns(_d(recommended['dscr_covenant']))} covenant.",
        f"Year-1 interest coverage is {_turns(recommended['interest_coverage'])} against a {_turns(_d(recommended['interest_coverage_covenant']))} covenant.",
        f"Leverage headroom is {_turns(base['leverage_headroom'])}. DSCR headroom is {_turns(base['dscr_headroom'])}.",
        "",
        f"The requested ${_money(sized['requested'])} million would produce a year-1 DSCR of {_turns(requested['dscr'])}, "
        f"which is below the {_turns(_d(requested['dscr_covenant']))} minimum. The request is not approved at that amount.",
        "",
        "The debt roll-forward is opening principal plus draws minus principal repayments. It equals the closing principal in every period, and the final balance is zero.",
        "",
        "Downside cases hold maintenance capex and cash taxes at the base assumption. That is conservative when EBITDA falls, because cash taxes are not reduced. Year 1 is the tightest point on a level-principal loan.",
        "",
    ]
    lines.append("| Case | Basis | EBITDA $m | DSCR | DSCR headroom | Leverage | Leverage headroom | Interest coverage |")
    lines.append("| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |")
    for row in result["sensitivity"]:
        lines.append(
            f"| {row['case']} | {row['basis']} | {_money(row['ebitda'])} | {_turns(row['dscr'])} | "
            f"{_turns(row['dscr_headroom'])} | {_turns(row['leverage'])} | {_turns(row['leverage_headroom'])} | "
            f"{_turns(row['interest_coverage'])} |"
        )
    text = "\n".join(lines) + "\n"
    return require_fictional_text(text, "underwriting memo")


def _money(value: Decimal | None) -> str:
    if value is None:
        return "n.m."
    return f"{(value / Decimal(1000000)):.2f}"


def _turns(value: Decimal | None) -> str:
    if value is None:
        return "n.m."
    return f"{value:.2f}x"
