"""Sizing, amortization, and the FICTIONAL label."""

from decimal import Decimal
from pathlib import Path

from src.underwriting import (
    amortization_schedule,
    dscr,
    load_borrower,
    memo,
    schedule_ties,
    size_commitment,
    underwrite,
)

ROOT = Path(__file__).resolve().parents[1]
BORROWER_FILE = ROOT / "data" / "fictional_northbridge_precision_FICTIONAL.yaml"


def _mini():
    return {
        "status": "FICTIONAL",
        "legal_name": "FICTIONAL Test Components, LLC",
        "business": "FICTIONAL test case.",
        "financials": {
            "operating_income": 8_000_000,
            "depreciation_and_amortization": 2_000_000,
            "maintenance_capex": 1_000_000,
            "cash_taxes": 1_000_000,
        },
        "request": {
            "facility": "Term loan",
            "amount_requested": 25_000_000,
            "tenor_years": 4,
            "coupon_rate": 0.10,
        },
        "sizing": {"min_dscr": 1.25, "max_total_leverage": 3.0, "round_down_to": 100_000},
        "existing_debt_after_close": 0,
        "covenants": {"max_total_leverage": 3.5, "min_interest_coverage": 2.0, "min_dscr": 1.20},
        "sensitivity": {"ebitda_shocks": [-0.10], "rate_shocks_bps": [100]},
        "use_of_proceeds": {"refinance_existing_shareholder_note": 0},
    }


def test_dscr_sizing_matches_the_hand_calculation():
    # CFADS = 10,000,000 - 1,000,000 - 1,000,000 = 8,000,000
    # Debt-service factor = 10% + 1/4 = 0.35
    # Unrounded DSCR cap = 8,000,000 / (1.25 x 0.35) = 18,285,714.29
    # Largest $100,000 that still clears 1.25x is $18,200,000.
    sized = size_commitment(_mini())
    assert sized["cfads"] == Decimal("8000000")
    assert sized["binding_constraint"] == "minimum DSCR"
    assert sized["commitment"] == Decimal("18200000")
    coverage = dscr(sized["cfads"], sized["commitment"], sized["coupon"], sized["tenor_years"])
    assert coverage >= Decimal("1.25")
    one_step_up = dscr(sized["cfads"], Decimal("18300000"), sized["coupon"], sized["tenor_years"])
    assert one_step_up < Decimal("1.25")


def test_amortization_reconciles_and_pays_off():
    schedule = amortization_schedule(Decimal("18200000"), Decimal("0.10"), 4)
    assert schedule_ties(schedule)
    assert schedule[0]["opening"] == 0
    assert schedule[0]["draws"] == Decimal("18200000")
    assert schedule[0]["closing"] == Decimal("18200000")
    assert schedule[-1]["closing"] == 0
    assert sum(row["principal"] for row in schedule) == Decimal("18200000")
    for row in schedule:
        assert row["opening"] + row["draws"] - row["principal"] == row["closing"]


def test_real_fictional_file_is_sized_inside_the_constraints_and_the_ask_is_not():
    borrower = load_borrower(BORROWER_FILE)
    package = underwrite(borrower)
    assert package["status"] == "FICTIONAL"
    assert package["schedule_reconciles"]
    assert package["sizing"]["commitment"] == Decimal("25900000")
    assert package["recommended"]["dscr"] >= Decimal("1.35")
    assert package["recommended"]["leverage"] <= Decimal("3.00")
    assert package["requested_case"]["dscr"] < Decimal("1.25")
    downside = next(row for row in package["sensitivity"] if row["case"] == "EBITDA -10%")
    assert downside["basis"] == "simulated"
    assert downside["dscr_headroom"] < 0
    text = memo(package)
    assert text.startswith("# FICTIONAL")
    assert "not a real company" in text.lower() or "not real" in text.lower()
