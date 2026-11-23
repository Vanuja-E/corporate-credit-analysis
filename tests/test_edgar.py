"""EDGAR selection rules and the Form 10-K tie-out. Cache only."""

import json
from pathlib import Path

from src.edgar import choose_fact, extract_company, index_tag, load_universe
from src.ratios import compute
from src.validation import compare

ROOT = Path(__file__).resolve().parents[1]


def test_latest_filing_replaces_an_older_comparative():
    chosen, _note = choose_fact([
        {"end": "2024-12-31", "val": 100, "filed": "2025-02-01", "frame": "CY2024", "accn": "a"},
        {"end": "2024-12-31", "val": 110, "filed": "2026-02-01", "frame": "CY2024", "accn": "b"},
    ])
    assert chosen["val"] == 110


def test_annual_frame_wins_when_the_filing_date_is_the_same():
    chosen, note = choose_fact([
        {"end": "2024-12-31", "val": 100, "filed": "2025-02-01", "frame": "CY2024Q4", "accn": "a"},
        {"end": "2024-12-31", "val": 110, "filed": "2025-02-01", "frame": "CY2024", "accn": "b"},
    ])
    assert chosen["val"] == 110
    assert "more than one value" in note


def test_index_keeps_only_annual_10k_facts():
    node = {"units": {"USD": [
        {"form": "10-Q", "fp": "Q3", "end": "2024-09-30", "start": "2024-01-01", "val": 1, "filed": "2024-10-01"},
        {"form": "10-K", "fp": "FY", "end": "2024-12-31", "start": "2024-10-01", "val": 2, "filed": "2025-02-01"},
        {"form": "10-K", "fp": "FY", "end": "2024-12-31", "start": "2024-01-01", "val": 3, "filed": "2025-02-01"},
        {"form": "10-K/A", "fp": "FY", "end": "2024-12-31", "start": "2024-01-01", "val": 4, "filed": "2025-03-01"},
    ]}}
    indexed = index_tag(node, flow=True)
    assert list(indexed) == ["2024-12-31"]
    assert indexed["2024-12-31"][0]["val"] == 3


def test_cached_10k_figures_match_the_face_statements():
    universe = load_universe(ROOT / "config" / "universe.yaml")
    history = []
    for company in universe["companies"]:
        cik = str(company["cik"]).zfill(10)
        facts = json.loads((ROOT / "data" / "raw" / f"CIK{cik}.json").read_text())
        submissions = json.loads((ROOT / "data" / "raw" / f"CIK{cik}_submissions.json").read_text())
        rows, lineage = extract_company(facts, submissions, company, universe)
        assert lineage, company["ticker"]
        assert {line["form"] for line in lineage} == {"10-K"}
        history.extend(compute(row) for row in rows)
    _results, failures = compare(history)
    assert failures == []
