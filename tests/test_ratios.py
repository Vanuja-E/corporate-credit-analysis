"""Hand-computed ratio checks. Inputs are a fixture, not a filing."""

from src.ratios import compute, interest_burden, total_debt


def base_row():
    return {
        "revenue": 1000.0,
        "gross_profit": 400.0,
        "operating_income": 150.0,
        "depreciation_and_amortization": 50.0,
        "short_term_borrowings": 20.0,
        "current_portion_long_term_debt": 30.0,
        "long_term_debt": 100.0,
        "finance_leases_included": False,
        "finance_lease_liability": 15.0,
        "cash": 40.0,
        "interest_is": 25.0,
        "interest_tag": "InterestExpenseNonoperating",
        "interest_paid": 24.0,
        "interest_paid_tag": "InterestPaid",
        "capex": 40.0,
        "cfo": 90.0,
        "current_assets": 200.0,
        "current_liabilities": 100.0,
        "inventory": 50.0,
        "equity": 250.0,
    }


def test_statement_ratios_match_hand_calculation():
    result = compute(base_row())
    assert result["ebitda"] == 200
    assert result["total_debt"] == 150
    assert result["net_debt"] == 110
    assert result["interest"] == 25
    assert result["fcf"] == 50
    assert result["gross_margin"] == 0.40
    assert result["ebitda_margin"] == 0.20
    assert result["debt_to_ebitda"] == 150 / 200
    assert result["net_debt_to_ebitda"] == 110 / 200
    assert result["ebitda_to_interest"] == 8
    assert result["ebitda_minus_capex_to_interest"] == 160 / 25
    assert result["cfo_to_debt"] == 90 / 150
    assert result["fcf_to_debt"] == 50 / 150
    assert result["current_ratio"] == 2
    assert result["quick_ratio"] == 1.5
    assert result["debt_to_capitalization"] == 150 / 400


def test_finance_leases_are_subtracted_only_when_the_debt_tags_include_them():
    excluded, note = total_debt(20, 30, 100, finance_lease_liability=15, finance_leases_included=False)
    included, included_note = total_debt(20, 30, 100, finance_lease_liability=15, finance_leases_included=True)
    assert excluded == 150
    assert "excluded" in note.lower()
    assert included == 135
    assert "subtracted" in included_note.lower()


def test_generic_interest_tag_yields_to_cash_interest_when_cash_is_materially_higher():
    amount, note, tag = interest_burden(100, "InterestExpense", 130)
    assert amount == 130
    assert tag == "InterestPaid"
    assert "25 percent" in note
    # A named gross tag is kept even if cash interest is higher.
    amount, note, tag = interest_burden(100, "InterestExpenseNonoperating", 130)
    assert amount == 100
    assert tag == "InterestExpenseNonoperating"


def test_nonpositive_ebitda_does_not_produce_a_leverage_multiple():
    row = base_row()
    row["operating_income"] = -80
    row["depreciation_and_amortization"] = 30
    result = compute(row)
    assert result["ebitda"] == -50
    assert result["debt_to_ebitda"] is None
    assert result["net_debt_to_ebitda"] is None
    assert result["ebitda_to_interest"] is None


def test_zero_interest_does_not_divide():
    row = base_row()
    row["interest_is"] = 0
    row["interest_paid"] = 0
    result = compute(row)
    assert result["interest"] == 0
    assert result["ebitda_to_interest"] is None
