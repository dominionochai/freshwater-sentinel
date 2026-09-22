"""Scene loading and orchestration for the analysis pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path

import numpy as np
import rasterio

from app.explain import build_explanation
from app.hab_risk import score_risk
from app.models import AnalyzeResponse, HABObservation, ScenePayload
from app.water_masking import create_water_mask
from app.water_quality import QualityMetrics, estimate_quality
from config import MIN_ANALYZED_PIXELS

REQUIRED_BANDS = ("B02", "B03", "B04", "B05", "B08", "B11")
DEFAULT_GEOTIFF_BANDS = ("B02", "B03", "B04", "B05", "B08", "B11")


@dataclass(frozen=True)
class Scene:
    water_body_id: str
    acquisition_date: date
    bands: dict[str, np.ndarray]
    source: str


def scene_from_payload(water_body_id: str, payload: ScenePayload, requested_date: date | None) -> Scene:
    bands = {
        name.upper(): np.asarray(values, dtype=float)
        for name, values in payload.bands.items()
    }
    _validate_bands(bands)
    return Scene(
        water_body_id,
        requested_date or payload.acquisition_date or date.today(),
        bands,
        "inline-scene",
    )


def scene_from_geotiff(water_body_id: str, path: str, requested_date: date | None) -> Scene:
    file_path = Path(path)
    if not file_path.is_file():
        raise FileNotFoundError(f"GeoTIFF path does not exist: {path}")
    with rasterio.open(file_path) as dataset:
        if dataset.count < len(REQUIRED_BANDS):
            raise ValueError(f"GeoTIFF must contain at least {len(REQUIRED_BANDS)} bands")
        names = [description.upper() if description else DEFAULT_GEOTIFF_BANDS[index] for index, description in enumerate(dataset.descriptions)]
        bands = {name: dataset.read(index + 1).astype(float) for index, name in enumerate(names)}
        acquisition = requested_date or date.fromisoformat(dataset.tags().get("ACQUISITION_DATE", date.today().isoformat()))
    _validate_bands(bands)
    return Scene(water_body_id, acquisition, bands, f"geotiff:{file_path}")


def _validate_bands(bands: dict[str, np.ndarray]) -> None:
    missing = [band for band in REQUIRED_BANDS if band not in bands]
    if missing:
        raise ValueError(f"scene missing required bands: {', '.join(missing)}")
    shapes = {array.shape for array in bands.values()}
    if len(shapes) != 1 or next(iter(shapes), ()) == ():
        raise ValueError("all scene bands must have the same non-empty 2D shape")
    if any(array.ndim != 2 for array in bands.values()):
        raise ValueError("scene bands must be two-dimensional")


def analyze(scene: Scene, observations: list[HABObservation]) -> AnalyzeResponse:
    mask, diagnostics = create_water_mask(scene.bands)
    metrics: QualityMetrics = estimate_quality(scene.bands, mask)
    if metrics.pixels_analyzed < MIN_ANALYZED_PIXELS:
        raise ValueError(f"only {metrics.pixels_analyzed} valid water pixels; need at least {MIN_ANALYZED_PIXELS}")
    risk = score_risk(metrics, observations)
    explanation = build_explanation(metrics, risk, scene.acquisition_date, diagnostics, observations)
    return AnalyzeResponse(
        scene_id="",
        water_body_id=scene.water_body_id,
        acquisition_date=scene.acquisition_date,
        risk=risk,
        quality=metrics.as_dict(),
        explanation=explanation,
        water_mask={**diagnostics, "pixels_in_mask": int(mask.sum()), "scene_pixels": int(mask.size)},
    )
