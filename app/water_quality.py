"""Original water-quality metrics backed by vendored screening estimators."""

from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np

from config import CHLOROPHYLL_RED_UG_L, TURBIDITY_RED_NTU

try:
    # The shim keeps the application import stable while the implementation
    # remains under vendor/get-pak as an original, attribution-aware module.
    from vendor.get_pak_methods import estimate_chlorophyll_a, estimate_turbidity
except Exception:  # pragma: no cover - only used in incomplete deployments
    @dataclass(frozen=True)
    class _FallbackEstimate:
        value: np.ndarray
        uncertainty: np.ndarray

    def estimate_turbidity(red: np.ndarray, nir: np.ndarray) -> _FallbackEstimate:
        """Boot-safe fallback if optional vendor files cannot be imported."""
        with np.errstate(divide="ignore", invalid="ignore"):
            ratio = np.divide(red, nir, out=np.full_like(red, np.nan), where=nir > 1e-6)
        value = np.clip(130.0 * ratio - 5.0, 0.0, 1000.0)
        return _FallbackEstimate(value, 2.0 + 0.20 * np.abs(value))

    def estimate_chlorophyll_a(green: np.ndarray, red_edge: np.ndarray) -> _FallbackEstimate:
        """Boot-safe fallback if optional vendor files cannot be imported."""
        with np.errstate(divide="ignore", invalid="ignore"):
            ratio = np.divide(green, red_edge, out=np.full_like(green, np.nan), where=red_edge > 1e-6)
        value = np.clip(45.0 * ratio - 5.0, 0.0, 500.0)
        return _FallbackEstimate(value, 1.0 + 0.25 * np.abs(value))


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


def _finite(values: np.ndarray) -> np.ndarray:
    return np.asarray(values, dtype=float)


def _coverage(mask: np.ndarray, total: int) -> float:
    return float(np.clip(mask.sum() / max(total, 1), 0.0, 1.0))


def estimate_quality(bands: dict[str, np.ndarray], water_mask: np.ndarray) -> QualityMetrics:
    """Estimate quality only from pixels selected by ``water_mask``.

    B4/B8 feed the red/NIR turbidity estimator and B3/B5 feed the
    green/red-edge chlorophyll-a estimator.  The risk thresholds imported from
    ``config.py`` are intentionally unchanged.  Returned uncertainty combines
    estimator uncertainty with spatial spread and reduced water coverage.
    """
    required = ("B03", "B04", "B05", "B08")
    missing = [key for key in required if key not in bands]
    if missing:
        raise ValueError(f"missing required quality bands: {', '.join(missing)}")

    arrays = {key: _finite(bands[key]) for key in required}
    mask = np.asarray(water_mask, dtype=bool)
    if any(array.shape != mask.shape for array in arrays.values()):
        raise ValueError("quality bands and water mask must have identical shapes")
    selected = mask.copy()
    for array in arrays.values():
        selected &= np.isfinite(array)
    count = int(selected.sum())
    if count == 0:
        raise ValueError("no valid water pixels available for quality analysis")

    red = arrays["B04"][selected]
    nir = arrays["B08"][selected]
    green = arrays["B03"][selected]
    red_edge = arrays["B05"][selected]
    turbidity = estimate_turbidity(red, nir)
    chlorophyll = estimate_chlorophyll_a(green, red_edge)
    turbidity_values = np.asarray(turbidity.value, dtype=float)
    chlorophyll_values = np.asarray(chlorophyll.value, dtype=float)
    turbidity_uncertainty = np.asarray(turbidity.uncertainty, dtype=float)
    chlorophyll_uncertainty = np.asarray(chlorophyll.uncertainty, dtype=float)
    if not np.isfinite(turbidity_values).any() or not np.isfinite(chlorophyll_values).any():
        raise ValueError("estimators returned no finite quality values")

    turbidity_spread = float(np.nanstd(turbidity_values) / max(TURBIDITY_RED_NTU, 1.0))
    chlorophyll_spread = float(np.nanstd(chlorophyll_values) / max(CHLOROPHYLL_RED_UG_L, 1.0))
    estimator_spread = float(
        np.nanmedian(turbidity_uncertainty) / max(TURBIDITY_RED_NTU, 1.0)
        + np.nanmedian(chlorophyll_uncertainty) / max(CHLOROPHYLL_RED_UG_L, 1.0)
    ) / 2.0
    coverage = _coverage(selected, mask.size)
    quality_uncertainty = float(
        np.clip(0.10 + 0.35 * (1.0 - coverage) + 0.20 * estimator_spread
                + 0.15 * min(turbidity_spread + chlorophyll_spread, 1.0), 0.0, 1.0)
    )
    return QualityMetrics(
        pixels_analyzed=count,
        water_coverage=coverage,
        turbidity_ntu=float(np.nanmedian(turbidity_values)),
        chlorophyll_a_ug_l=float(np.nanmedian(chlorophyll_values)),
        turbidity_p90_ntu=float(np.nanpercentile(turbidity_values, 90)),
        chlorophyll_a_p90_ug_l=float(np.nanpercentile(chlorophyll_values, 90)),
        quality_uncertainty=quality_uncertainty,
    )
