"""Scorecard thresholds, boundaries, and the cases that make a multiple meaningless."""

from pathlib import Path

from src.scorecard import load_scorecard, score_inputs

CONFIG = load_scorecard(Path("config/scorecard.yaml"))


def _inputs(**overrides):
    base = {
        "ebitda": 100.0,
        "interest": 10.0,
        "total_debt": 100.0,
        "cfo": 40.0,
        "fcf": 20.0,
        "equity": 100.0,
        "debt_to_ebitda": 1.0,
        "net_debt_to_ebitda": 0.2,
        "ebitda_to_interest": 10.0,
        "ebitda_minus_capex_to_interest": 8.0,
        "cfo_to_debt": 0.50,
        "fcf_to_debt": 0.30,
        "debt_to_capitalization": 0.20,
        "current_ratio": 2.0,
    }
    base.update(overrides)
    return base


def _points(result, ratio_id):
    return next(row for row in result.rows if row.ratio_id == ratio_id)


def test_weights_sum_to_one_and_categories_are_the_published_names():
    assert abs(sum(item["weight"] for item in CONFIG["ratios"]) - 1) < 1e-9
    assert [item["name"] for item in CONFIG["categories"]] == [
        "Strong", "Acceptable", "Elevated Risk", "Weak",
    ]


def test_boundary_values_fall_in_the_better_bucket():
    result = score_inputs(_inputs(
        debt_to_ebitda=1.5,
        net_debt_to_ebitda=0.5,
        ebitda_to_interest=8.0,
        ebitda_minus_capex_to_interest=6.0,
        cfo_to_debt=0.40,
        fcf_to_debt=0.20,
        debt_to_capitalization=0.25,
        current_ratio=1.50,
    ), CONFIG)
    assert all(row.points == 4 for row in result.rows)
    assert result.composite == 4
    assert result.category == "Strong"


def test_value_just_outside_a_bucket_steps_down():
    inside = _points(score_inputs(_inputs(debt_to_ebitda=1.5), CONFIG), "debt_to_ebitda")
    outside = _points(score_inputs(_inputs(debt_to_ebitda=1.51), CONFIG), "debt_to_ebitda")
    assert inside.points == 4
    assert outside.points == 3
    assert outside.bucket == "Acceptable"


def test_composite_cutoffs_are_inclusive():
    strong = score_inputs(_inputs(debt_to_ebitda=4.0, net_debt_to_ebitda=0.2), CONFIG)
    # Debt/EBITDA above 3.5x is 1 point. 0.20 x 1 + 0.80 x 4 = 3.40.
    assert strong.composite == 3.40
    assert strong.category == "Strong"
    acceptable = score_inputs(_inputs(debt_to_ebitda=4.0, net_debt_to_ebitda=4.0), CONFIG)
    # 0.20 x 1 + 0.15 x 1 + 0.65 x 4 = 2.95.
    assert round(acceptable.composite, 2) == 2.95
    assert acceptable.category == "Acceptable"


def test_zero_or_negative_ebitda_and_zero_interest():
    negative = score_inputs(_inputs(ebitda=-5, debt_to_ebitda=None, net_debt_to_ebitda=None), CONFIG)
    assert _points(negative, "debt_to_ebitda").points == 1
    assert "not meaningful" in _points(negative, "debt_to_ebitda").note
    assert _points(negative, "ebitda_to_interest").points == 1

    zero_ebitda = score_inputs(_inputs(ebitda=0), CONFIG)
    assert _points(zero_ebitda, "net_debt_to_ebitda").points == 1

    no_interest = score_inputs(_inputs(
        interest=0,
        ebitda_to_interest=None,
        ebitda_minus_capex_to_interest=None,
    ), CONFIG)
    assert _points(no_interest, "ebitda_to_interest").points == 4
    assert "not a constraint" in _points(no_interest, "ebitda_to_interest").note

    no_interest_and_no_ebitda = score_inputs(_inputs(interest=0, ebitda=-1), CONFIG)
    assert _points(no_interest_and_no_ebitda, "ebitda_to_interest").points == 1


def test_zero_debt_with_positive_cash_flow_is_not_a_weak_coverage_ratio():
    result = score_inputs(_inputs(total_debt=0, cfo=10, fcf=5, cfo_to_debt=None, fcf_to_debt=None), CONFIG)
    assert _points(result, "cfo_to_debt").points == 4
    assert _points(result, "fcf_to_debt").points == 4


def test_missing_ratio_renormalizes_weights():
    result = score_inputs(_inputs(current_ratio=None), CONFIG)
    missing = _points(result, "current_ratio")
    assert missing.missing
    scored = [row for row in result.rows if not row.missing]
    assert abs(sum(row.effective_weight for row in scored) - 1) < 1e-9
    assert result.composite == 4
    assert result.category == "Strong"
