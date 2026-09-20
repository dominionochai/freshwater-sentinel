"""Configurable activity risk scoring for harmful-algal-bloom screening."""

from __future__ import annotations

from collections.abc import Iterable

from config import ACTIVITY_WEIGHTS, CHLOROPHYLL_RED_UG_L, CHLOROPHYLL_YELLOW_UG_L, RISK_THRESHOLDS, TURBIDITY_RED_NTU, TURBIDITY_YELLOW_NTU
from app.models import ActivityRisk, HABObservation
from app.water_quality import QualityMetrics


def _ramp(value: float, yellow: float, red: float) -> float:
    if value <= yellow:
        return 0.0
    if value >= red:
        return 1.0
    return (value - yellow) / (red - yellow)


def _label(score: float, activity: str) -> str:
    thresholds = RISK_THRESHOLDS[activity]
    if score >= thresholds["red"]:
        return "red"
    if score >= thresholds["yellow"]:
        return "yellow"
    return "green"


def score_risk(metrics: QualityMetrics, observations: Iterable[HABObservation] = ()) -> dict[str, ActivityRisk]:
    """Combine quality layers and optional field observations into activity risk."""
    turbidity_signal = _ramp(metrics.turbidity_p90_ntu, TURBIDITY_YELLOW_NTU, TURBIDITY_RED_NTU)
    chlorophyll_signal = _ramp(metrics.chlorophyll_a_p90_ug_l, CHLOROPHYLL_YELLOW_UG_L, CHLOROPHYLL_RED_UG_L)
    observation_signal = max((observation.severity for observation in observations), default=0.0)
    output: dict[str, ActivityRisk] = {}
    for activity, weights in ACTIVITY_WEIGHTS.items():
        score = sum(signal * weights[name] for name, signal in (("turbidity", turbidity_signal), ("chlorophyll", chlorophyll_signal), ("observations", observation_signal)))
        score = round(min(max(score, 0.0), 1.0), 4)
        label = _label(score, activity)
        rationale = f"{label} screening signal for {activity}: turbidity={turbidity_signal:.2f}, chlorophyll={chlorophyll_signal:.2f}, field-observation={observation_signal:.2f}."
        output[activity] = ActivityRisk(score=score, label=label, rationale=rationale)
    return output
