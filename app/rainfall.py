"""Offline rainfall feature extraction for environmental signal fusion."""
from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

import numpy as np


def rainfall_features(observations: Iterable[float] | Mapping[str, Any] | None) -> dict[str, float]:
    """Summarize supplied rainfall millimetres without inventing observations.

    A mapping may contain ``values`` or ``mm``. Missing/empty input is an
    explicit neutral signal, not synthetic weather data.
    """
    if observations is None:
        values: list[float] = []
    elif isinstance(observations, Mapping):
        raw = observations.get("values", observations.get("mm", []))
        values = [float(value) for value in raw]
    else:
        values = [float(value) for value in observations]
    if any(not np.isfinite(value) or value < 0 for value in values):
        raise ValueError("rainfall observations must be finite non-negative millimetres")
    array = np.asarray(values, dtype=float)
    total = float(array.sum()) if array.size else 0.0
    recent = float(array[-3:].sum()) if array.size else 0.0
    intensity = float(array.max()) if array.size else 0.0
    return {
        "observations": float(array.size),
        "total_mm": total,
        "recent_3_total_mm": recent,
        "max_daily_mm": intensity,
        "rainfall_pressure": float(np.clip(recent / 60.0, 0.0, 1.0)),
    }


summarize_rainfall = rainfall_features
