"""Every output that names the sample borrower has to say FICTIONAL."""

from pathlib import Path

from openpyxl import load_workbook

from src.excel_report import build
from src.scorecard import load_scorecard, score_inputs
from src.underwriting import load_borrower, memo, underwrite

ROOT = Path(__file__).resolve().parents[1]
NAME = "Northbridge"


def test_borrower_file_and_generated_text_are_labeled(tmp_path):
    path = ROOT / "data" / "fictional_northbridge_precision_FICTIONAL.yaml"
    assert "FICTIONAL" in path.name
    borrower = load_borrower(path)
    assert borrower["status"] == "FICTIONAL"
    assert "FICTIONAL" in borrower["legal_name"]
    package = underwrite(borrower)
    text = memo(package)
    assert "FICTIONAL" in text
    assert NAME in text

    # A one-row reported history is enough to build the workbook around the loan.
    statement = {
        "ticker": "MSFT", "fiscal_year": 2025, "period_end": "2025-06-30",
        "revenue": 100, "filing_url": "https://www.sec.gov/example",
        "debt_tags": {},
    }
    config = load_scorecard(ROOT / "config" / "scorecard.yaml")
    statement["result"] = score_inputs({
        "ebitda": 100, "interest": 10, "total_debt": 20, "cfo": 50, "fcf": 30, "equity": 80,
        "debt_to_ebitda": 0.2, "net_debt_to_ebitda": 0.1, "ebitda_to_interest": 10,
        "ebitda_minus_capex_to_interest": 8, "cfo_to_debt": 2, "fcf_to_debt": 1,
        "debt_to_capitalization": 0.2, "current_ratio": 2,
    }, config)
    scored = [{
        "ticker": "MSFT", "fiscal_year": 2025, "period_end": "2025-06-30",
        "statement": statement, "result": statement["result"],
    }]
    workbook_path = tmp_path / "credit_analysis.xlsx"
    build([statement], scored, package, workbook_path)
    workbook = load_workbook(workbook_path)
    underwriting = workbook["Underwriting"]["A1"].value
    sensitivity = workbook["Sensitivity"]["A1"].value
    assert "FICTIONAL" in underwriting
    assert NAME in underwriting
    assert "FICTIONAL" in sensitivity
    for sheet in workbook.worksheets:
        for row in sheet.iter_rows(values_only=True):
            for value in row:
                if isinstance(value, str) and NAME in value:
                    assert "FICTIONAL" in value


def test_repository_text_that_names_the_borrower_also_says_fictional():
    skipped = {".png", ".xlsx", ".json"}
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        if any(part in {".git", "__pycache__", ".pytest_cache", "data/raw"} for part in path.parts):
            continue
        if "data" in path.parts and "raw" in path.parts:
            continue
        if path.suffix.lower() in skipped:
            continue
        text = path.read_text(errors="ignore")
        if NAME in text or NAME in path.name:
            assert "FICTIONAL" in text or "FICTIONAL" in path.name, path
