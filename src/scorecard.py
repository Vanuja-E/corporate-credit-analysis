"""Transparent credit scorecard.

Weights, bucket bounds, points, and category cutoffs are read from
config/scorecard.yaml. This module does not contain a second set of
thresholds. A result names the ratio, the value, the bucket, the points,
and the weight, so a recommendation can be traced to the lines that produced it.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

LEVERAGE_IDS = {"debt_to_ebitda", "net_debt_to_ebitda"}
COVERAGE_IDS = {"ebitda_to_interest", "ebitda_minus_capex_to_interest"}
CASH_DEBT_IDS = {"cfo_to_debt", "fcf_to_debt"}


@dataclass
class RatioScore:
    ratio_id: str
    label: str
    value: float | None
    published_weight: float
    effective_weight: float
    points: int | None
    bucket: str | None
    note: str
    missing: bool

    @property
    def weighted_points(self) -> float | None:
        if self.missing or self.points is None:
            return None
        return self.effective_weight * self.points


@dataclass
class ScorecardResult:
    composite: float | None
    category: str
    rows: list[RatioScore]

    def drivers(self) -> list[RatioScore]:
        scored = [row for row in self.rows if not row.missing and row.points is not None]
        return sorted(scored, key=lambda row: (row.points, -(row.weighted_points or 0)))


def load_scorecard(path: Path) -> dict:
    with path.open() as handle:
        config = yaml.safe_load(handle)
    weights = [item["weight"] for item in config["ratios"]]
    if abs(sum(weights) - 1.0) > 1e-9:
        raise ValueError(f"Scorecard weights sum to {sum(weights)}, not 1.")
    return config


def _bucket(value: float, spec: dict) -> dict:
    for band in spec["buckets"]:
        if spec["direction"] == "lower":
            bound = band["max"]
            if bound is None or value <= bound:
                return band
        else:
            bound = band["min"]
            if bound is None or value >= bound:
                return band
    raise ValueError(f"No bucket matched {spec['id']} value {value}.")


def _special_case(ratio_id: str, inputs: dict) -> RatioScore | None:
    """Return a scored row when the ordinary multiple would mislead, else None."""
    ebitda = inputs.get("ebitda")
    interest = inputs.get("interest")
    label = inputs["_label"]
    weight = inputs["_weight"]

    if ratio_id in LEVERAGE_IDS and ebitda is not None and ebitda <= 0:
        return RatioScore(
            ratio_id, label, None, weight, weight, 1, "Weak",
            "EBITDA is not positive. The leverage multiple is not meaningful.",
            False,
        )
    if ratio_id in COVERAGE_IDS and interest is None:
        return None
    if ratio_id in COVERAGE_IDS and interest <= 0:
        if ebitda is not None and ebitda > 0:
            return RatioScore(
                ratio_id, label, None, weight, weight, 4, "Strong",
                "Interest is zero or negative and EBITDA is positive. Coverage is not a constraint.",
                False,
            )
        return RatioScore(
            ratio_id, label, None, weight, weight, 1, "Weak",
            "Interest is zero or negative and EBITDA is not positive.",
            False,
        )
    if ratio_id in COVERAGE_IDS and ebitda is not None and ebitda <= 0:
        return RatioScore(
            ratio_id, label, inputs.get(ratio_id), weight, weight, 1, "Weak",
            "EBITDA is not positive, so coverage does not support the interest burden.",
            False,
        )
    if ratio_id in CASH_DEBT_IDS:
        debt = inputs.get("total_debt")
        numerator = inputs.get("cfo") if ratio_id == "cfo_to_debt" else inputs.get("fcf")
        if debt is None or debt <= 0:
            if numerator is not None and numerator > 0:
                return RatioScore(
                    ratio_id, label, None, weight, weight, 4, "Strong",
                    "Total debt is zero and cash flow is positive.",
                    False,
                )
            return RatioScore(
                ratio_id, label, None, weight, weight, 1, "Weak",
                "Total debt is zero and cash flow is not positive.",
                False,
            )
    if ratio_id == "debt_to_capitalization":
        debt = inputs.get("total_debt")
        equity = inputs.get("equity")
        if debt is None or equity is None or debt + equity <= 0:
            return RatioScore(
                ratio_id, label, None, weight, weight, 1, "Weak",
                "Debt plus equity is not positive, so capitalization is not meaningful.",
                False,
            )
    return None


def score_inputs(inputs: dict, config: dict) -> ScorecardResult:
    """Score one company-year. ``inputs`` is a ratios.compute result."""
    preliminary: list[RatioScore] = []
    for spec in config["ratios"]:
        ratio_id = spec["id"]
        context = dict(inputs)
        context["_label"] = spec["label"]
        context["_weight"] = spec["weight"]
        special = _special_case(ratio_id, context)
        if special is not None:
            preliminary.append(special)
            continue
        value = inputs.get(ratio_id)
        if value is None:
            preliminary.append(RatioScore(
                ratio_id, spec["label"], None, spec["weight"], spec["weight"],
                None, None, "Input was not available. The weight is redistributed.", True,
            ))
            continue
        band = _bucket(value, spec)
        preliminary.append(RatioScore(
            ratio_id, spec["label"], value, spec["weight"], spec["weight"],
            int(band["points"]), band["name"], "Scored on the published scale.", False,
        ))

    available = [row for row in preliminary if not row.missing]
    weight_sum = sum(row.published_weight for row in available)
    rows: list[RatioScore] = []
    for row in preliminary:
        if row.missing or weight_sum == 0:
            rows.append(row)
            continue
        rows.append(RatioScore(
            row.ratio_id, row.label, row.value, row.published_weight,
            row.published_weight / weight_sum, row.points, row.bucket, row.note, False,
        ))
    if not available or weight_sum == 0:
        return ScorecardResult(None, "Weak", rows)
    composite = sum((row.effective_weight or 0) * (row.points or 0) for row in rows if not row.missing)
    category = "Weak"
    for band in config["categories"]:
        minimum = band["minimum_composite"]
        if minimum is None or composite >= minimum:
            category = band["name"]
            break
    return ScorecardResult(composite, category, rows)
