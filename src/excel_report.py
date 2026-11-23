"""Workbook. Every numeric row carries a basis: reported, assumption, forecast, or simulated."""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

NAVY = "1F4E79"
HEADER_FILL = PatternFill("solid", fgColor=NAVY)
HEADER_FONT = Font(color="FFFFFF", bold=True, name="Calibri", size=10)
BODY = Font(name="Calibri", size=10, color="1F1F1F")
TITLE = Font(name="Calibri", size=16, bold=True, color=NAVY)
SECTION = Font(name="Calibri", size=12, bold=True, color=NAVY)
THIN = Border(
    left=Side(style="thin", color="D9D9D9"),
    right=Side(style="thin", color="D9D9D9"),
    top=Side(style="thin", color="D9D9D9"),
    bottom=Side(style="thin", color="D9D9D9"),
)
FILL_ZEBRA = PatternFill("solid", fgColor="F7F9FB")
WRAP = Alignment(wrap_text=True, vertical="center")


def _header(ws, row, labels):
    for col, label in enumerate(labels, start=1):
        cell = ws.cell(row, col, label)
        cell.fill = HEADER_FILL
        cell.font = HEADER_FONT
        cell.alignment = Alignment(wrap_text=True, vertical="center")
        cell.border = THIN
    ws.auto_filter.ref = None
    ws.freeze_panes = "A2" if row == 1 else ws.freeze_panes
    ws.row_dimensions[row].height = 30


def _write(ws, row, values, zebra=False):
    for col, value in enumerate(values, start=1):
        if isinstance(value, Decimal):
            value = float(value)
        cell = ws.cell(row, col, value)
        cell.font = BODY
        cell.border = THIN
        cell.alignment = Alignment(vertical="center", wrap_text=True)
        if zebra:
            cell.fill = FILL_ZEBRA
        if isinstance(value, float):
            cell.number_format = '#,##0.00'
    return row + 1


def _widths(ws, widths):
    for index, width in enumerate(widths, start=1):
        ws.column_dimensions[get_column_letter(index)].width = width


def _millions(value):
    if value is None:
        return None
    return value / 1_000_000


def build(history: list[dict], scored_latest: list[dict], underwriting: dict, path: Path) -> Path:
    wb = Workbook()
    _cover(wb.active)
    _scorecard(wb.create_sheet("Scorecard"), scored_latest)
    _contributions(wb.create_sheet("Contributions"), scored_latest)
    for scored in scored_latest:
        ticker = scored["ticker"]
        rows = [row for row in history if row["ticker"] == ticker]
        _company(wb.create_sheet(ticker), rows, scored)
    _underwriting(wb.create_sheet("Underwriting"), underwriting)
    _sensitivity(wb.create_sheet("Sensitivity"), underwriting)
    path.parent.mkdir(parents=True, exist_ok=True)
    wb.save(path)
    return path


def _cover(ws):
    ws.title = "Cover"
    ws["A1"] = "Corporate credit analysis"
    ws["A1"].font = TITLE
    ws["A2"] = "Vanuja Ekanayake, BBA Finance candidate, Baruch College Zicklin School of Business"
    ws["A2"].font = BODY
    lines = [
        "Dollar figures on the company sheets are millions of USD. The underwriting sheets are actual dollars.",
        "Basis = reported: a Form 10-K amount, or a ratio calculated only from Form 10-K amounts.",
        "Basis = assumption: a scorecard weight or threshold, or an input of the FICTIONAL borrower.",
        "Basis = forecast: a draw, interest amount, principal payment, or balance on the term-loan schedule.",
        "Basis = simulated: a downside case. EBITDA shocks hold capex and cash taxes at the base assumption. Rate shocks hold EBITDA at the base.",
        "EBITDA = operating income + depreciation and amortization. Total debt excludes operating leases and finance leases.",
        "Net debt = total debt - cash and cash equivalents. Short-term investments are not deducted.",
        "The borrower on the Underwriting sheet is FICTIONAL. It is not a real company and not an SEC registrant.",
        "This workbook is not a rating and not a commitment to lend.",
    ]
    for index, line in enumerate(lines, start=4):
        ws.cell(index, 1, line).font = BODY
        ws.cell(index, 1).alignment = WRAP
        ws.row_dimensions[index].height = 32
    _widths(ws, [120])
    ws.freeze_panes = "A4"
    ws.page_setup.orientation = "landscape"
    ws.page_setup.fitToPage = True
    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = 1
    ws.sheet_properties.pageSetUpPr.fitToPage = True
    ws.oddHeader.left.text = "Corporate credit analysis"
    ws.oddFooter.left.text = "Reported figures are Form 10-K. The term loan is FICTIONAL."
    ws.print_title_rows = "1:1"


def _scorecard(ws, scored_latest):
    ws.page_setup.orientation = "landscape"
    ws.page_setup.fitToPage = True
    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = 1
    ws.sheet_properties.pageSetUpPr.fitToPage = True
    ws.oddHeader.left.text = "Scorecard"
    ws.oddFooter.left.text = "Weights and cutoffs are assumptions. Ratios are reported."
    labels = [
        "Company", "Fiscal year", "Period end", "Debt/EBITDA", "Net debt/EBITDA",
        "EBITDA/Interest", "(EBITDA-capex)/Interest", "CFO/Debt", "FCF/Debt",
        "Debt/capitalization", "Current ratio", "Composite", "Result", "Basis of ratios", "Basis of weights",
    ]
    _header(ws, 1, labels)
    for index, scored in enumerate(scored_latest):
        statement = scored["statement"]
        result = scored["result"]
        values = [
            scored["ticker"], scored["fiscal_year"], scored["period_end"],
            statement.get("debt_to_ebitda"), statement.get("net_debt_to_ebitda"),
            statement.get("ebitda_to_interest"), statement.get("ebitda_minus_capex_to_interest"),
            statement.get("cfo_to_debt"), statement.get("fcf_to_debt"),
            statement.get("debt_to_capitalization"), statement.get("current_ratio"),
            result.composite, result.category, "reported", "assumption",
        ]
        _write(ws, index + 2, values, zebra=index % 2 == 1)
        for col in (4, 5, 6, 7, 11):
            ws.cell(index + 2, col).number_format = '0.00'
        for col in (8, 9, 10):
            ws.cell(index + 2, col).number_format = '0.0%'
        ws.cell(index + 2, 12).number_format = '0.00'
    ws.cell(8, 1, "Category cutoffs, assumption: Strong at or above 3.40, Acceptable at or above 2.60, Elevated Risk at or above 1.80, otherwise Weak.").font = BODY
    _widths(ws, [14, 12, 14, 14, 16, 16, 22, 12, 12, 18, 14, 12, 16, 18, 18])
    ws.auto_filter.ref = f"A1:O{1 + len(scored_latest)}"
    ws.freeze_panes = "A2"
    ws.print_title_rows = "1:1"
    ws.page_setup.orientation = "landscape"
    ws.page_setup.fitToPage = True
    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = 1
    ws.page_setup.paperSize = ws.PAPERSIZE_TABLOID
    ws.sheet_properties.pageSetUpPr.fitToPage = True
    ws.oddHeader.left.text = "Scorecard — latest fiscal year"
    ws.oddFooter.right.text = "Page &P of &N"
    ws.oddFooter.left.text = "Ratios are reported. Weights and category cutoffs are assumptions."
    ws.page_setup.horizontalCentered = True
    ws.sheet_view.showGridLines = False
    ws.sheet_view.zoomScale = 110
    ws.page_margins.left = 0.5
    ws.page_margins.right = 0.5
    ws.page_margins.top = 0.75
    ws.page_margins.bottom = 0.6
    ws.page_margins.header = 0.3
    ws.page_margins.footer = 0.3
    ws.oddHeader.center.text = ""
    ws.sheet_format.defaultRowHeight = 18
    ws.row_dimensions[1].height = 32


def _contributions(ws, scored_latest):
    labels = [
        "Company", "Fiscal year", "Ratio", "Value", "Published weight", "Effective weight",
        "Points", "Bucket", "Weighted points", "Basis of value", "Basis of weight", "Note",
    ]
    _header(ws, 1, labels)
    row_index = 2
    for scored in scored_latest:
        for item in scored["result"].rows:
            values = [
                scored["ticker"], scored["fiscal_year"], item.label, item.value,
                item.published_weight, item.effective_weight, item.points, item.bucket,
                item.weighted_points, "reported", "assumption", item.note,
            ]
            _write(ws, row_index, values, zebra=row_index % 2 == 0)
            ws.cell(row_index, 4).number_format = '0.00'
            ws.cell(row_index, 5).number_format = '0.0%'
            ws.cell(row_index, 6).number_format = '0.0%'
            ws.cell(row_index, 9).number_format = '0.00'
            row_index += 1
    _widths(ws, [12, 12, 32, 12, 16, 16, 10, 14, 16, 16, 16, 78])
    ws.auto_filter.ref = f"A1:L{row_index - 1}"
    ws.freeze_panes = "A2"
    ws.print_title_rows = "1:1"
    ws.page_setup.orientation = "landscape"
    ws.page_setup.fitToPage = True
    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = 1
    ws.sheet_properties.pageSetUpPr.fitToPage = True
    ws.page_setup.paperSize = ws.PAPERSIZE_TABLOID
    ws.oddHeader.left.text = "Scorecard contribution"
    ws.oddFooter.left.text = "Each recommendation traces to these rows."
    ws.page_margins.left = 0.5
    ws.page_margins.right = 0.5
    ws.sheet_view.showGridLines = False


def _company(ws, rows, scored):
    ws.page_setup.orientation = "landscape"
    ws.page_setup.fitToPage = True
    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = 1
    ws.sheet_properties.pageSetUpPr.fitToPage = True
    ws.page_setup.paperSize = ws.PAPERSIZE_TABLOID
    ws.oddHeader.left.text = f"{scored['ticker']} — Form 10-K"
    ws.oddFooter.left.text = "Amounts in millions of USD. Basis reported means the figure comes from a Form 10-K or is calculated from one."
    ws.oddFooter.right.text = "Page &P of &N"
    ws.page_margins.left = 0.5
    ws.page_margins.right = 0.5
    ws.sheet_view.showGridLines = False
    labels = ["Fiscal year", "Period end", "Line", "USD millions", "Basis", "Tag or formula", "Filing", "Note"]
    _header(ws, 1, labels)
    fields = [
        ("Revenue", "revenue", "revenue_tag", ""),
        ("Gross profit", "gross_profit", "gross_profit_tag", ""),
        ("Operating income", "operating_income", "operating_income_tag", ""),
        ("Depreciation and amortization", "depreciation_and_amortization", "depreciation_and_amortization_tag", ""),
        ("EBITDA", "ebitda", None, "Operating income + D&A"),
        ("Income-statement interest", "interest_is", "interest_is_tag", ""),
        ("Cash interest paid", "interest_paid", "interest_paid_tag", ""),
        ("Interest used in coverage", "interest", "interest_tag", ""),
        ("Short-term borrowings", "short_term_borrowings", None, ""),
        ("Current portion of long-term debt", "current_portion_long_term_debt", None, ""),
        ("Long-term debt", "long_term_debt", None, ""),
        ("Total debt", "total_debt", None, "Leases excluded"),
        ("Cash", "cash", "cash_tag", ""),
        ("Short-term investments", "short_term_investments", "short_term_investments_tag", "Not deducted in net debt"),
        ("Net debt", "net_debt", None, "Total debt - cash"),
        ("Capital expenditure", "capex", "capex_tag", ""),
        ("Cash from operations", "cfo", "cfo_tag", ""),
        ("Free cash flow", "fcf", None, "CFO - capex"),
        ("Cash taxes paid", "cash_taxes", "cash_taxes_tag", ""),
        ("Impairment losses", "impairment", "impairment_tag", "Not added back to EBITDA"),
        ("Current assets", "current_assets", "current_assets_tag", ""),
        ("Current liabilities", "current_liabilities", "current_liabilities_tag", ""),
        ("Inventory", "inventory", "inventory_tag", ""),
        ("Stockholders' equity", "equity", "equity_tag", ""),
        ("Gross margin", "gross_margin", None, "Gross profit / revenue"),
        ("EBITDA margin", "ebitda_margin", None, "EBITDA / revenue"),
        ("Debt / EBITDA", "debt_to_ebitda", None, "Not meaningful if EBITDA is not positive"),
        ("Net debt / EBITDA", "net_debt_to_ebitda", None, ""),
        ("EBITDA / Interest", "ebitda_to_interest", None, ""),
        ("(EBITDA - capex) / Interest", "ebitda_minus_capex_to_interest", None, ""),
        ("CFO / Debt", "cfo_to_debt", None, ""),
        ("FCF / Debt", "fcf_to_debt", None, ""),
        ("Current ratio", "current_ratio", None, ""),
        ("Quick ratio", "quick_ratio", None, "(Current assets - inventory) / current liabilities"),
        ("Debt / capitalization", "debt_to_capitalization", None, ""),
        ("Free cash flow, USD millions duplicate check", "fcf", None, ""),
    ]
    # The last duplicate was a mistake. Drop it by slicing.
    fields = fields[:-1]
    ratio_keys = {
        "gross_margin", "ebitda_margin", "debt_to_ebitda", "net_debt_to_ebitda",
        "ebitda_to_interest", "ebitda_minus_capex_to_interest", "cfo_to_debt",
        "fcf_to_debt", "current_ratio", "quick_ratio", "debt_to_capitalization",
    }
    percent_keys = {"gross_margin", "ebitda_margin", "cfo_to_debt", "fcf_to_debt", "debt_to_capitalization"}
    row_index = 2
    for statement in rows:
        for label, key, tag_key, note in fields:
            raw = statement.get(key)
            if key in ratio_keys:
                shown = raw
            else:
                shown = _millions(raw) if raw is not None else None
            debt_tags = statement.get("debt_tags") or {}
            tag = statement.get(tag_key) if tag_key else "calculated from reported figures"
            if key in debt_tags and debt_tags[key]:
                tag = debt_tags[key]
            if key == "ebitda":
                tag = "operating income + depreciation and amortization"
            extra = statement.get("interest_note") if key == "interest" else ""
            if key == "total_debt":
                extra = statement.get("total_debt_note") or ""
            _write(ws, row_index, [
                statement["fiscal_year"], statement["period_end"], label, shown, "reported",
                tag or "", statement.get("filing_url"), note or extra,
            ], zebra=row_index % 2 == 0)
            if key in percent_keys:
                ws.cell(row_index, 4).number_format = '0.0%'
            elif key in ratio_keys:
                ws.cell(row_index, 4).number_format = '0.00'
            else:
                ws.cell(row_index, 4).number_format = '#,##0.0'
            row_index += 1
    _widths(ws, [14, 14, 36, 16, 14, 55, 78, 55])
    ws.freeze_panes = "A2"
    ws.print_title_rows = "1:1"
    ws.auto_filter.ref = f"A1:H{row_index - 1}"
    ws.oddHeader.center.text = scored["result"].category
    ws.page_setup.horizontalCentered = True


def _underwriting(ws, package):
    ws["A1"] = "FICTIONAL BORROWER. Northbridge Precision Components, LLC is not a real company. No figure on this sheet is a reported SEC amount."
    ws["A1"].font = Font(name="Calibri", size=12, bold=True, color="833C0C")
    ws.merge_cells("A1:G1")
    ws.row_dimensions[1].height = 32
    labels = ["Line", "Amount (USD)", "Basis", "Note"]
    _header(ws, 3, labels)
    sized = package["sizing"]
    financials_rows = [
        ("EBITDA", sized["ebitda"], "assumption", "Operating income + D&A, both assumptions"),
        ("Maintenance capex", sized["capex"], "assumption", ""),
        ("Cash taxes", sized["cash_taxes"], "assumption", "Cash tax assumption, not a tax provision"),
        ("Cash flow available for debt service", sized["cfads"], "assumption", "EBITDA - capex - cash taxes"),
        ("Amount requested", sized["requested"], "assumption", "The ask. It does not clear the DSCR test."),
        ("DSCR capacity, unrounded", sized["dscr_cap"], "forecast", "CFADS / (minimum sizing DSCR x (coupon + 1/tenor))"),
        ("Leverage capacity, unrounded", sized["leverage_cap"], "forecast", "Maximum sizing leverage x EBITDA"),
        ("Recommended commitment", sized["commitment"], "forecast", sized["binding_constraint"]),
        ("Refinance shareholder note", package["sources_and_uses"]["use_refinance_shareholder_note"], "assumption", "Repaid at close from the new loan"),
        ("General corporate proceeds", package["sources_and_uses"]["use_general_corporate"], "forecast", "Commitment minus the refinanced note"),
    ]
    row_index = 4
    for item in financials_rows:
        _write(ws, row_index, item, zebra=row_index % 2 == 0)
        ws.cell(row_index, 2).number_format = '"$"#,##0'
        row_index += 1
    row_index += 1
    ws.cell(row_index, 1, "Amortization. Opening + draws - principal = closing.").font = SECTION
    row_index += 1
    sched_header = row_index
    for col, label in enumerate(["Period", "Opening", "Draws", "Interest", "Principal", "Closing", "Basis"], start=1):
        cell = ws.cell(row_index, col, label)
        cell.fill = HEADER_FILL
        cell.font = HEADER_FONT
        cell.border = THIN
    row_index += 1
    for schedule_row in package["schedule"]:
        _write(ws, row_index, [
            schedule_row["label"], schedule_row["opening"], schedule_row["draws"],
            schedule_row["interest"], schedule_row["principal"], schedule_row["closing"],
            schedule_row["basis"],
        ], zebra=row_index % 2 == 0)
        for col in range(2, 7):
            ws.cell(row_index, col).number_format = '"$"#,##0'
        row_index += 1
    _widths(ws, [48, 22, 18, 55, 16, 18, 14])
    ws.freeze_panes = "A4"
    ws.print_title_rows = "1:3"
    ws.page_setup.orientation = "landscape"
    ws.page_setup.fitToPage = True
    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = 1
    ws.sheet_properties.pageSetUpPr.fitToPage = True
    ws.page_setup.paperSize = ws.PAPERSIZE_TABLOID
    ws.oddHeader.left.text = "FICTIONAL term loan"
    ws.oddFooter.left.text = "FICTIONAL borrower. Not an SEC filing."
    ws.page_margins.left = 0.5
    ws.page_margins.right = 0.5
    ws.sheet_view.showGridLines = False
    ws.auto_filter.ref = f"A{sched_header}:G{row_index - 1}"


def _sensitivity(ws, package):
    ws["A1"] = "FICTIONAL downside cases. Simulated, except the base case, which is the forecast on the recommended commitment."
    ws["A1"].font = Font(name="Calibri", size=12, bold=True, color="833C0C")
    ws.merge_cells("A1:L1")
    labels = [
        "Case", "Basis", "EBITDA", "Coupon", "Interest", "Principal", "Debt service",
        "DSCR", "DSCR headroom", "Leverage", "Leverage headroom", "Interest coverage",
    ]
    _header(ws, 3, labels)
    for index, row in enumerate(package["sensitivity"]):
        _write(ws, index + 4, [
            row["case"], row["basis"], float(row["ebitda"]), float(row["coupon"]),
            float(row["interest"]), float(row["principal"]), float(row["debt_service"]),
            None if row["dscr"] is None else float(row["dscr"]),
            None if row["dscr_headroom"] is None else float(row["dscr_headroom"]),
            None if row["leverage"] is None else float(row["leverage"]),
            None if row["leverage_headroom"] is None else float(row["leverage_headroom"]),
            None if row["interest_coverage"] is None else float(row["interest_coverage"]),
        ], zebra=index % 2 == 1)
        for col in (3, 5, 6, 7):
            ws.cell(index + 4, col).number_format = '"$"#,##0'
        ws.cell(index + 4, 4).number_format = '0.00%'
        for col in range(8, 13):
            ws.cell(index + 4, col).number_format = '0.00'
    note_row = 4 + len(package["sensitivity"]) + 1
    ws.cell(note_row, 1, "Headroom is the distance to the covenant, not to the tighter sizing test. Negative headroom is a breach. Capex and cash taxes are held at the base assumption in every EBITDA case.").font = BODY
    ws.merge_cells(start_row=note_row, start_column=1, end_row=note_row, end_column=8)
    _widths(ws, [18, 14, 16, 12, 16, 16, 16, 12, 16, 12, 18, 18])
    ws.freeze_panes = "A4"
    ws.print_title_rows = "3:3"
    ws.page_setup.orientation = "landscape"
    ws.page_setup.fitToPage = True
    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = 1
    ws.sheet_properties.pageSetUpPr.fitToPage = True
    ws.oddHeader.left.text = "FICTIONAL sensitivity"
    ws.oddFooter.left.text = "FICTIONAL. Simulated cases are not forecasts of a real borrower."
    ws.page_margins.left = 0.5
    ws.page_margins.right = 0.5
    ws.sheet_view.showGridLines = False
    ws.auto_filter.ref = f"A3:L{3 + len(package['sensitivity'])}"
