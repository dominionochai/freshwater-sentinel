"""Scene loading and orchestration for the analysis pipeline."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any

import numpy as np
import rasterio

from app.explain import build_explanation
from app.hab_risk import score_risk
from app.models import AnalyzeResponse, HABObservation, ScenePayload
from app.network import analyze_water_network
from app.network_models import WaterNetwork
from app.water_masking import create_water_mask
from app.water_quality import QualityMetrics, estimate_quality
from config import MIN_ANALYZED_PIXELS

REQUIRED_BANDS = ("B02", "B03", "B04", "B05", "B08", "B11")
DEFAULT_GEOTIFF_BANDS = REQUIRED_BANDS


@dataclass(frozen=True)
class Scene:
    water_body_id: str
    acquisition_date: date
    bands: dict[str, np.ndarray]
    source: str
    metadata: dict[str, Any] = field(default_factory=dict)


def scene_from_payload(
    water_body_id: str,
    payload: ScenePayload,
    requested_date: date | None = None,
) -> Scene:
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
        {"source_type": "inline_payload", **payload.metadata},
    )


def scene_from_geotiff(
    water_body_id: str,
    path: str,
    requested_date: date | None = None,
) -> Scene:
    file_path = Path(path)
    if not file_path.is_file():
        raise FileNotFoundError(f"GeoTIFF path does not exist: {path}")
    with rasterio.open(file_path) as dataset:
        if dataset.count < len(REQUIRED_BANDS):
            raise ValueError(
                f"GeoTIFF must contain at least {len(REQUIRED_BANDS)} bands "
                f"in {REQUIRED_BANDS} order"
            )
        bands = {
            name: dataset.read(index + 1).astype(float)
            for index, name in enumerate(DEFAULT_GEOTIFF_BANDS)
        }
        tags = {str(key): str(value) for key, value in dataset.tags().items()}
        metadata: dict[str, Any] = {
            "source_type": "local_geotiff",
            "path": str(file_path),
            "driver": dataset.driver,
            "width": dataset.width,
            "height": dataset.height,
            "count": dataset.count,
            "crs": str(dataset.crs) if dataset.crs else None,
            "transform": str(dataset.transform),
            "band_descriptions": list(dataset.descriptions),
            "tags": tags,
        }
    metadata = {key: value for key, value in metadata.items() if value is not None}
    raw_date = tags.get("ACQUISITION_DATE")
    acquisition = requested_date
    if acquisition is None and raw_date:
        try:
            acquisition = date.fromisoformat(raw_date[:10])
        except ValueError:
            acquisition = None
    _validate_bands(bands)
    return Scene(
        water_body_id,
        acquisition or date.today(),
        bands,
        f"geotiff:{file_path}",
        metadata,
    )


def _validate_bands(bands: dict[str, np.ndarray]) -> None:
    missing = [band for band in REQUIRED_BANDS if band not in bands]
    if missing:
        raise ValueError(f"scene missing required bands: {', '.join(missing)}")
    shapes = {array.shape for array in bands.values()}
    if len(shapes) != 1 or (0, 0) in shapes or any(array.ndim != 2 for array in bands.values()):
        raise ValueError("all scene bands must have the same non-empty 2D shape")


def analyze(
    scene: Scene,
    observations: list[HABObservation],
    network: WaterNetwork | None = None,
) -> AnalyzeResponse:
    mask, diagnostics = create_water_mask(scene.bands)
    metrics: QualityMetrics = estimate_quality(scene.bands, mask)
    if metrics.pixels_analyzed < MIN_ANALYZED_PIXELS:
        raise ValueError(
            f"only {metrics.pixels_analyzed} valid water pixels analyzed; "
            f"need at least {MIN_ANALYZED_PIXELS}"
        )
    risk = score_risk(metrics, observations)
    explanation = build_explanation(
        metrics,
        risk,
        scene.acquisition_date,
        diagnostics,
        observations,
    )
    network_analysis = analyze_water_network(network).to_dict() if network is not None else None
    return AnalyzeResponse(
        scene_id="",
        water_body_id=scene.water_body_id,
        acquisition_date=scene.acquisition_date,
        risk=risk,
        quality=metrics.as_dict(),
        explanation=explanation,
        water_mask={
            **diagnostics,
            "pixels_in_mask": int(mask.sum()),
            "scene_pixels": int(mask.size),
        },
        scene_metadata=scene.metadata,
        network_analysis=network_analysis,
    )
