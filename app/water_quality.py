"""Original reflectance-based water-quality proxy calculations."""

from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np

from config import CHLOROPHYLL_RED_UG_L, TURBIDITY_RED_NTU


@dataclass(frozen=True)
class QualityMetrics:
    pixels_analyzed: int
    water_coverage: float
    turbidity_ntu: float
    chlorophyll_a_ug_l: float
    turbidity_p90_ntu: float
    chlorophyll_a_p90_ug_l: float
    quality_uncertainty: float

    def as_dict(self) -> dict[str, float | int]:
        return asdict(self)


def _bounded(values: np.ndarray, low: float = 0.0, high: float = 1000.0) -> np.ndarray:
    return np.clip(np.nan_to_num(values, nan=0.0, posinf=high, neginf=low), low, high)


def estimate_quality(bands: dict[str, np.ndarray], water_mask: np.ndarray) -> QualityMetrics:
    """Estimate quality only from pixels selected by ``water_mask``.

    The red/green turbidity and blue/green/red chlorophyll forms are simple,
    original screening proxies. They need regional field calibration before use
    as operational or regulatory measurements. No land pixel enters statistics.
    """
    required = ("B02", "B03", "B04")
    missing = [key for key in required if key not in bands]
    if missing:
        raise ValueError(f"missing required quality bands: {', '.join(missing)}")
    blue, green, red = (np.asarray(bands[key], dtype=float) for key in required)
    if water_mask.shape != blue.shape or len({array.shape for array in (blue, green, red)}) != 1:
        raise ValueError("quality bands and water mask must have identical shapes")
    selected = water_mask & np.isfinite(blue) & np.isfinite(green) & np.isfinite(red)
    count = int(selected.sum())
    if count == 0:
        raise ValueError("no valid water pixels available for quality analysis")

    b, g, r = blue[selected], green[selected], red[selected]
    turbidity = _bounded(120.0 * np.maximum(r / np.maximum(g, 1e-6) - 0.10, 0.0))
    chlorophyll = _bounded(65.0 * np.maximum(g / np.maximum(b, 1e-6) - 1.0, 0.0) + 35.0 * r)
    coverage = count / max(int(water_mask.size), 1)
    spread = float(np.clip(np.std(turbidity) / max(TURBIDITY_RED_NTU, 1.0), 0.0, 1.0))
    chl_spread = float(np.clip(np.std(chlorophyll) / max(CHLOROPHYLL_RED_UG_L, 1.0), 0.0, 1.0))
    uncertainty = float(np.clip(0.10 + 0.35 * (1.0 - coverage) + 0.20 * (spread + chl_spread) / 2.0, 0.0, 1.0))
    return QualityMetrics(
        pixels_analyzed=count,
        water_coverage=float(coverage),
        turbidity_ntu=float(np.median(turbidity)),
        chlorophyll_a_ug_l=float(np.median(chlorophyll)),
        turbidity_p90_ntu=float(np.percentile(turbidity, 90)),
        chlorophyll_a_p90_ug_l=float(np.percentile(chlorophyll, 90)),
        quality_uncertainty=uncertainty,
    )
