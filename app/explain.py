"""Plain-language, evidence-oriented explanations."""

from __future__ import annotations

from datetime import date

from app.hab_risk import _ramp
from app.models import ActivityRisk, Explanation, HABObservation
from app.water_quality import QualityMetrics
from config import CHLOROPHYLL_RED_UG_L, CHLOROPHYLL_YELLOW_UG_L, TURBIDITY_RED_NTU, TURBIDITY_YELLOW_NTU


def build_explanation(metrics: QualityMetrics, risk: dict[str, ActivityRisk], alert_date: date, water_diagnostics: dict[str, float], observations: list[HABObservation]) -> Explanation:
    turbidity_signal = _ramp(metrics.turbidity_p90_ntu, TURBIDITY_YELLOW_NTU, TURBIDITY_RED_NTU)
    chlorophyll_signal = _ramp(metrics.chlorophyll_a_p90_ug_l, CHLOROPHYLL_YELLOW_UG_L, CHLOROPHYLL_RED_UG_L)
    highest = max(risk.items(), key=lambda item: item[1].score)
    observed_text = " Optional field observations were included." if observations else " No external HAB observation was supplied."
    summary = f"On {alert_date.isoformat()}, {metrics.pixels_analyzed} water pixels were analyzed. The highest activity signal is {highest[0]} ({highest[1].label}, {highest[1].score:.2f}).{observed_text}"
    band_signals = [
        f"B03 green and B11 SWIR1 produced the water mask (candidate MNDWI mean {water_diagnostics['mndwi_mean_candidate']:.3f}).",
        f"B04 red relative to B03 green produced a turbidity proxy: median {metrics.turbidity_ntu:.1f} NTU, p90 {metrics.turbidity_p90_ntu:.1f} (signal {turbidity_signal:.2f}).",
        f"B02 blue, B03 green, and B04 red produced a chlorophyll-a proxy: median {metrics.chlorophyll_a_ug_l:.1f} µg/L, p90 {metrics.chlorophyll_a_p90_ug_l:.1f} (signal {chlorophyll_signal:.2f}).",
        f"Water masking retained {metrics.water_coverage:.1%} of scene pixels; land/vegetation pixels were excluded from quality statistics.",
    ]
    uncertainty = min(1.0, metrics.quality_uncertainty + (0.05 if not observations else 0.0))
    limitations = [
        "These are reflectance proxies, not laboratory measurements or a regulatory advisory.",
        "Cloud, atmospheric correction, shallow bottoms, mixed pixels, and regional ecology can bias results.",
        "Thresholds are configurable in config.py and require field validation before operational alerts.",
    ]
    return Explanation(summary=summary, pixels_analyzed=metrics.pixels_analyzed, band_signals=band_signals, alert_date=alert_date, uncertainty=round(uncertainty, 4), limitations=limitations)
