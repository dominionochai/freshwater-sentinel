"""Grade alert outcomes against district-level cholera observations."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any, Iterable, Mapping

from app.verification import _date


def _row_date(row: Mapping[str, Any]) -> date | None:
    """Return the first parseable date-like value from a cholera row."""
    for field in ("week", "date", "case_week", "week_start"):
        if field in row:
            parsed = _date(row.get(field))
            if parsed is not None:
                return parsed
    return None


def _row_cases(row: Mapping[str, Any]) -> float:
    """Read a row's case count, treating an event row without a count as one."""
    value = row.get("cases", row.get("case_count", row.get("cholera_cases", 1)))
    if value is None:
        return 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def verify_alert(
    alert_week: Any,
    district: str,
    cholera_rows: Iterable[Mapping[str, Any]],
    horizon_weeks: int = 6,
) -> dict[str, Any]:
    """Grade one alert against cholera cases in the following weeks.

    Dates are parsed using the same tolerant ISO/date semantics as
    :func:`app.verification.grade_alerts`.  Only rows for ``district`` with a
    parseable date strictly after the alert week and no later than the horizon
    are considered.  ``cases_observed`` is the sum of their case counts.
    """
    parsed_alert_week = _date(alert_week)
    output_alert_week = (
        parsed_alert_week.isoformat()
        if parsed_alert_week is not None
        else str(alert_week)
    )
    try:
        horizon = int(horizon_weeks)
    except (TypeError, ValueError):
        horizon = 6

    result = {
        "status": "MISS",
        "lead_time_weeks": None,
        "alert_week": output_alert_week,
        "district": district,
        "first_case_week": None,
        "cases_observed": 0,
        "horizon_weeks": horizon,
    }
    if parsed_alert_week is None or horizon < 0:
        return result

    end_week = parsed_alert_week + timedelta(weeks=horizon)
    first_case_week: date | None = None
    cases_observed = 0.0

    for row in cholera_rows:
        if row.get("district") != district:
            continue
        case_week = _row_date(row)
        if case_week is None or not (parsed_alert_week < case_week <= end_week):
            continue
        cases = _row_cases(row)
        cases_observed += cases
        if cases > 0 and (first_case_week is None or case_week < first_case_week):
            first_case_week = case_week

    if first_case_week is not None:
        result["status"] = "HIT"
        result["lead_time_weeks"] = (first_case_week - parsed_alert_week).days / 7.0
        result["first_case_week"] = first_case_week.isoformat()

    result["cases_observed"] = (
        int(cases_observed) if cases_observed.is_integer() else cases_observed
    )
    return result
