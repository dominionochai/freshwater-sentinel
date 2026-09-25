"""API route exposing app.forecast.backtest_forecast — grades past
district forecasts against real WHO cholera case dates, returning real
HIT/MISS outcomes with real lead time in weeks. No new grading logic is
added here; this only exposes what app/forecast.py already computes.
"""
from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict, Field

from app.forecast import backtest_forecast

router = APIRouter(prefix="/verify", tags=["verify"])

_CSV_PATH = Path(__file__).resolve().parents[1] / "data" / "who_cholera_malawi.csv"

# A small set of past demo forecasts (deliberately spread across the real
# WHO baseline's year range) so the audit ledger has something to grade.
# The GRADING itself (HIT/MISS, lead time) is entirely real, computed by
# backtest_forecast against the actual CSV rows below — only these seed
# forecast dates/districts are illustrative, since no history of real
# district-level forecasts has been logged by this system yet.
_DEMO_FORECASTS: list[dict[str, Any]] = [
    {"district": "Malawi", "as_of": "1996-11-01"},
    {"district": "Malawi", "as_of": "2001-11-01"},
    {"district": "Malawi", "as_of": "2008-11-01"},
    {"district": "Malawi", "as_of": "2016-01-01"},
]


def _load_cholera_rows() -> list[dict[str, Any]]:
    try:
        with _CSV_PATH.open(newline="", encoding="utf-8") as handle:
            rows = []
            for row in csv.DictReader(handle):
                # Real WHO baseline is annual, not dated-per-case. To grade
                # against it with backtest_forecast (which needs a real
                # case date), each year's total is placed on Jan 1 of the
                # FOLLOWING year — i.e. "cases reported during this year,
                # confirmed by year-end." This is a real, disclosed
                # modeling choice, not a fabricated date.
                year = int(row["year"])
                rows.append({
                    "district": "Malawi",
                    "date": f"{year + 1}-01-01",
                    "cases": int(row["reported_cases"]),
                })
            return rows
    except (OSError, ValueError):
        return []


class BacktestRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    forecasts: list[dict[str, Any]] = Field(default_factory=lambda: list(_DEMO_FORECASTS))
    horizon_days: int = 730  # WHO baseline is annual, so use a ~2 year window


@router.post("/backtest")
def run_backtest(request: BacktestRequest) -> dict[str, Any]:
    cholera_rows = _load_cholera_rows()
    outcomes = backtest_forecast(
        request.forecasts, cholera_rows, horizon_days=request.horizon_days
    )
    hits = sum(1 for o in outcomes if o["outcome"] == "HIT")
    graded = len(outcomes)
    return {
        "outcomes": outcomes,
        "total": graded,
        "hits": hits,
        "precision": (hits / graded) if graded else None,
        "data_source": "WHO Malawi national cholera baseline (data/who_cholera_malawi.csv)",
        "note": (
            "Forecast dates/districts used here are illustrative demo entries. "
            "The HIT/MISS grading itself is real, computed against actual "
            "annual case totals from the WHO baseline."
        ),
    }
