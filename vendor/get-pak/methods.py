"""Original Sentinel-2 water-quality estimators inspired by published get-pak work.

Algorithmic inspiration: https://github.com/SNO-HYBAM/get-pak (MIT).
This module is an original compact reimplementation of the published approach,
not copied upstream source.  It uses Sentinel-2 surface reflectance and keeps
calibration coefficients explicit so a regional field campaign can replace
them without changing the surrounding pipeline.

The turbidity proxy follows the published red/NIR-ratio idea: suspended
material generally raises red reflectance relative to the near infrared.  The
chlorophyll-a screening proxy uses the green/red-edge ratio, where pigment
absorption and red-edge scattering provide a useful, but non-specific, signal.
Both outputs include a per-pixel uncertainty array.  These are screening
estimates, not laboratory measurements.

Atmospheric correction notes
----------------------------
Use atmospherically corrected bottom-of-atmosphere (BOA) reflectance whenever
possible, with the same processing level and spatial resampling for all bands.
TOA values, thin cloud, haze, adjacency effects, sun glint, bottom reflectance,
and mixed shoreline pixels can bias both ratios.  A cloud/shadow/water mask
must be applied before summarising the arrays.  Local calibration against
co-located turbidity and chlorophyll-a samples is required for operational use.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

import numpy as np

# Sentinel-2 band names used by the estimators.
B3 = "B03"  # green, approximately 560 nm
B4 = "B04"  # red, approximately 665 nm
B5 = "B05"  # red-edge 1, approximately 705 nm
B8 = "B08"  # NIR, approximately 842 nm

# Transparent defaults, intentionally easy to replace during field calibration.
TURBIDITY_SLOPE = 130.0
TURBIDITY_INTERCEPT = -5.0
CHLOROPHYLL_SLOPE = 45.0
CHLOROPHYLL_INTERCEPT = -5.0
_EPSILON = 1.0e-6


@dataclass(frozen=True)
class Estimate:
    """A per-pixel screening estimate and its one-sigma-style uncertainty.

    ``value`` and ``uncertainty`` have identical shapes and use the input
    pixels' units.  Invalid pixels are NaN in both arrays.  The uncertainty is
    a transparent propagation proxy, not a confidence interval from a fitted
    regional model.
    """

    value: np.ndarray
    uncertainty: np.ndarray
    ratio: np.ndarray
    method: str

    def as_dict(self) -> dict[str, object]:
        """Return JSON-friendly metadata while retaining arrays for callers."""
        return {
            "value": self.value,
            "uncertainty": self.uncertainty,
            "ratio": self.ratio,
            "method": self.method,
        }


def _array(value: np.ndarray | float) -> np.ndarray:
    """Convert reflectance input to a floating array without mutating it."""
    return np.asarray(value, dtype=float)


def _paired(numerator: np.ndarray | float, denominator: np.ndarray | float) -> tuple[np.ndarray, np.ndarray]:
    """Validate and return two same-shaped floating arrays."""
    top = _array(numerator)
    bottom = _array(denominator)
    if top.shape != bottom.shape:
        raise ValueError("reflectance bands must have identical shapes")
    if top.ndim == 0:
        top = top.reshape(1)
        bottom = bottom.reshape(1)
    return top, bottom


def _ratio(numerator: np.ndarray, denominator: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Compute a safe ratio and the finite, positive-input validity mask."""
    valid = (
        np.isfinite(numerator)
        & np.isfinite(denominator)
        & (numerator >= 0.0)
        & (denominator > _EPSILON)
    )
    with np.errstate(divide="ignore", invalid="ignore", over="ignore"):
        result = np.divide(numerator, denominator, out=np.full_like(numerator, np.nan), where=valid)
    return result, valid


def _bounded_linear(
    ratio: np.ndarray,
    valid: np.ndarray,
    slope: float,
    intercept: float,
    maximum: float,
) -> np.ndarray:
    """Apply a transparent linear calibration and retain invalid pixels as NaN."""
    with np.errstate(invalid="ignore"):
        values = slope * ratio + intercept
    values = np.clip(values, 0.0, maximum)
    return np.where(valid, values, np.nan)


def _uncertainty(
    value: np.ndarray,
    ratio: np.ndarray,
    valid: np.ndarray,
    relative: float,
    floor: float,
    ratio_noise: float,
) -> np.ndarray:
    """Combine a relative calibration term, a floor, and ratio noise."""
    with np.errstate(invalid="ignore"):
        spread = floor + relative * np.abs(value) + ratio_noise * np.abs(ratio)
    return np.where(valid, spread, np.nan)


def estimate_turbidity(
    red: np.ndarray | float,
    nir: np.ndarray | float,
    *,
    slope: float = TURBIDITY_SLOPE,
    intercept: float = TURBIDITY_INTERCEPT,
    maximum: float = 1000.0,
) -> Estimate:
    """Estimate turbidity in NTU using a red/NIR reflectance ratio.

    This is the get-pak-inspired published approach expressed as an explicit
    screening calibration: ``NTU = clip(slope * (B4 / B8) + intercept)``.
    Defaults are deliberately generic and must be replaced or validated with
    local samples before operational or regulatory use.

    Args:
        red: Sentinel-2 B4 BOA reflectance, scaled to a common unit.
        nir: Sentinel-2 B8 BOA reflectance, scaled to the same unit as ``red``.
        slope: Regional conversion slope in NTU per unit ratio.
        intercept: Regional conversion intercept in NTU.
        maximum: Physical/reporting upper bound for the screening output.
    """
    red_array, nir_array = _paired(red, nir)
    ratio, valid = _ratio(red_array, nir_array)
    value = _bounded_linear(ratio, valid, slope, intercept, maximum)
    uncertainty = _uncertainty(value, ratio, valid, relative=0.20, floor=2.0, ratio_noise=8.0)
    return Estimate(value, uncertainty, ratio, "red/NIR ratio turbidity (get-pak-inspired)")


def estimate_chlorophyll_a(
    green: np.ndarray | float,
    red_edge: np.ndarray | float,
    *,
    slope: float = CHLOROPHYLL_SLOPE,
    intercept: float = CHLOROPHYLL_INTERCEPT,
    maximum: float = 500.0,
) -> Estimate:
    """Estimate chlorophyll-a in micrograms per litre from B3/B5.

    The green/red-edge ratio is used as a compact pigment-screening proxy:
    ``ug/L = clip(slope * (B3 / B5) + intercept)``.  It is sensitive to
    illumination, suspended sediment, species composition, and shallow-water
    effects.  Validate coefficients against local laboratory observations.
    """
    green_array, edge_array = _paired(green, red_edge)
    ratio, valid = _ratio(green_array, edge_array)
    value = _bounded_linear(ratio, valid, slope, intercept, maximum)
    uncertainty = _uncertainty(value, ratio, valid, relative=0.25, floor=1.0, ratio_noise=5.0)
    return Estimate(value, uncertainty, ratio, "green/red-edge chlorophyll-a ratio")


def estimate_from_bands(
    bands: Mapping[str, np.ndarray | float],
    *,
    turbidity_slope: float = TURBIDITY_SLOPE,
    turbidity_intercept: float = TURBIDITY_INTERCEPT,
    chlorophyll_slope: float = CHLOROPHYLL_SLOPE,
    chlorophyll_intercept: float = CHLOROPHYLL_INTERCEPT,
) -> dict[str, Estimate]:
    """Estimate both indicators from a Sentinel-2 band mapping.

    The mapping must provide B3, B4, B5, and B8 under either canonical names
    (``B03`` etc.) or the short aliases accepted by ``_band``.  This helper is
    intentionally small so callers can use the lower-level functions when
    their ingestion layer already knows each band.
    """
    green = _band(bands, B3, "B3")
    red = _band(bands, B4, "B4")
    edge = _band(bands, B5, "B5")
    nir = _band(bands, B8, "B8")
    return {
        "turbidity": estimate_turbidity(red, nir, slope=turbidity_slope, intercept=turbidity_intercept),
        "chlorophyll_a": estimate_chlorophyll_a(
            green,
            edge,
            slope=chlorophyll_slope,
            intercept=chlorophyll_intercept,
        ),
    }


def _band(bands: Mapping[str, np.ndarray | float], canonical: str, short: str) -> np.ndarray | float:
    """Find a canonical or short band key and raise a useful error if absent."""
    if canonical in bands:
        return bands[canonical]
    if short in bands:
        return bands[short]
    raise KeyError(f"missing required Sentinel-2 band: {canonical}")


def finite_summary(estimate: Estimate) -> dict[str, float | int]:
    """Summarise finite estimate pixels without hiding missing-data cases."""
    valid = np.isfinite(estimate.value)
    if not valid.any():
        return {"pixels": 0, "median": float("nan"), "p90": float("nan"), "uncertainty": float("nan")}
    return {
        "pixels": int(valid.sum()),
        "median": float(np.nanmedian(estimate.value)),
        "p90": float(np.nanpercentile(estimate.value, 90)),
        "uncertainty": float(np.nanmedian(estimate.uncertainty)),
    }


__all__ = [
    "B3",
    "B4",
    "B5",
    "B8",
    "Estimate",
    "estimate_chlorophyll_a",
    "estimate_from_bands",
    "estimate_turbidity",
    "finite_summary",
]
