"""Join synthetic clinic reports to checked-in community profiles."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

from app.community_data import load_community_profiles
from app.models import (
    CommunityProfile,
    HealthLinkage,
    HealthLinkageResponse,
    HealthReport,
    HealthRisk,
)

_REPORTS_PATH = Path(__file__).resolve().parents[1] / "data" / "clinic_reports.json"


def load_health_reports() -> list[HealthReport]:
    """Load and validate the repository's synthetic clinic-report seed."""
    with _REPORTS_PATH.open(encoding="utf-8") as report_file:
        records = json.load(report_file)
    if not isinstance(records, list):
        raise ValueError("clinic report seed data must be a list")
    return [HealthReport.model_validate(record) for record in records]


def _risk_for_case_total(case_total: int) -> HealthRisk:
    score = min(case_total / 10.0, 1.0)
    if score >= 0.75:
        label = "red"
    elif score >= 0.4:
        label = "yellow"
    else:
        label = "green"
    return HealthRisk(
        score=round(score, 2),
        label=label,
        rationale=(
            f"{case_total} synthetic reported cases are linked to this water point; "
            "this is a screening signal, not a clinical or causal finding."
        ),
    )


def build_health_linkage() -> HealthLinkageResponse:
    """Return report-to-water-point linkages with a privacy-preserving profile join."""
    profiles = {
        profile.community: profile
        for profile in (
            CommunityProfile.model_validate(record)
            for record in load_community_profiles()
        )
    }
    reports = load_health_reports()
    cases_by_water_point: defaultdict[str, int] = defaultdict(int)
    for report in reports:
        cases_by_water_point[report.water_point_id] += report.case_count

    linkages = [
        HealthLinkage(
            report_id=report.report_id,
            disease=report.disease,
            report_date=report.report_date,
            cases=report.case_count,
            water_point_id=report.water_point_id,
            community=report.community,
            community_profile=profiles.get(report.community),
            risk=_risk_for_case_total(cases_by_water_point[report.water_point_id]),
            plain_language=(
                f"{report.case_count} {report.disease} cases trace to this water point "
                f"in {report.community}."
            ),
        )
        for report in reports
    ]
    return HealthLinkageResponse(
        source_note=(
            "All clinic reports in this response are synthetic/demo records. "
            "The linkage is an exploratory screening aid, not proof of transmission."
        ),
        total_reports=len(linkages),
        total_cases=sum(report.case_count for report in reports),
        linkages=linkages,
    )
