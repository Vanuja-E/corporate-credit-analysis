"""Charts for the credit file. Historical ratios only. Simulated cases are not plotted."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

COLORS = {
    "MSFT": "#1f4e79",
    "PEP": "#2e75b6",
    "HON": "#548235",
    "KHC": "#c65911",
    "CCL": "#833c0c",
}


def _style(ax, title: str, ylabel: str):
    ax.set_title(title, loc="left", fontsize=12, color="#1f1f1f", pad=10)
    ax.set_ylabel(ylabel)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis="y", color="#d9d9d9", linewidth=0.6)
    ax.set_axisbelow(True)


def _series(rows: list[dict], ticker: str, field: str):
    points = [
        (row["fiscal_year"], row[field])
        for row in rows
        if row["ticker"] == ticker and row.get(field) is not None and (row.get("ebitda") or 0) > 0
    ]
    return points


def leverage_trend(rows: list[dict], path: Path) -> None:
    fig, ax = plt.subplots(figsize=(9.2, 5.2))
    for ticker in COLORS:
        debt = _series(rows, ticker, "debt_to_ebitda")
        net = _series(rows, ticker, "net_debt_to_ebitda")
        if debt:
            years, values = zip(*debt)
            ax.plot(years, values, color=COLORS[ticker], marker="o", linewidth=1.8, label=f"{ticker} debt")
        if net:
            years, values = zip(*net)
            ax.plot(years, values, color=COLORS[ticker], marker="o", linewidth=1.1, linestyle="--", label=f"{ticker} net")
    _style(ax, "Leverage: Debt/EBITDA and net debt/EBITDA", "Turns")
    ax.legend(ncol=2, fontsize=8, frameon=False)
    fig.text(
        0.01, 0.01,
        "Source: SEC EDGAR companyfacts, Form 10-K. Solid is total debt. Dashed is net debt. Years with EBITDA not positive are omitted. Kraft Heinz 2024 is high because impairments sit in operating income.",
        fontsize=7, color="#595959",
    )
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    fig.savefig(path, dpi=140)
    plt.close(fig)


def coverage_trend(rows: list[dict], path: Path) -> None:
    fig, ax = plt.subplots(figsize=(9.2, 5.2))
    for ticker in COLORS:
        points = _series(rows, ticker, "ebitda_to_interest")
        if not points:
            continue
        years, values = zip(*points)
        ax.plot(years, values, color=COLORS[ticker], marker="o", linewidth=1.8, label=ticker)
    ax.set_yscale("log")
    _style(ax, "Interest coverage: EBITDA / interest burden", "Turns, log scale")
    ax.legend(frameon=False)
    fig.text(
        0.01, 0.01,
        "Source: SEC EDGAR companyfacts, Form 10-K. Interest burden is the income-statement tag, or cash interest paid when that rule applies. Years with EBITDA not positive are omitted.",
        fontsize=7, color="#595959",
    )
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    fig.savefig(path, dpi=140)
    plt.close(fig)


def scorecard_comparison(results: list[dict], path: Path) -> None:
    fig, ax = plt.subplots(figsize=(8.4, 4.8))
    labels = [f"{row['ticker']}\nFY{row['fiscal_year']}" for row in results]
    values = [row["result"].composite for row in results]
    colors = [COLORS.get(row["ticker"], "#595959") for row in results]
    bars = ax.bar(labels, values, color=colors, width=0.72)
    ax.axhline(3.40, color="#548235", linewidth=0.8, linestyle=":")
    ax.axhline(2.60, color="#bf8f00", linewidth=0.8, linestyle=":")
    ax.axhline(1.80, color="#c65911", linewidth=0.8, linestyle=":")
    ax.set_ylim(0, 4.2)
    _style(ax, "Scorecard composite, latest fiscal year", "Weighted score (1 to 4)")
    for bar, row in zip(bars, results):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            max(bar.get_height() - 0.18, 0.12),
            row["result"].category,
            ha="center", va="top", fontsize=8, color="white",
        )
    fig.text(
        0.01, 0.01,
        "Dotted lines are the published cutoffs: 3.40 Strong, 2.60 Acceptable, 1.80 Elevated Risk. Below 1.80 is Weak.",
        fontsize=7, color="#595959",
    )
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    fig.savefig(path, dpi=140)
    plt.close(fig)
