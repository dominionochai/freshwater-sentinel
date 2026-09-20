"""Validated API request and response models."""

from __future__ import annotations

from datetime import date
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ScenePayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    acquisition_date: date | None = None
    bands: dict[str, list[list[float]]] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_rectangular_arrays(self) -> "ScenePayload":
        shapes = {(len(rows), len(rows[0]) if rows else 0) for rows in self.bands.values()}
        if not shapes or (0, 0) in shapes or len(shapes) != 1:
            raise ValueError("all scene bands must be non-empty rectangular arrays of equal shape")
        if any(any(len(row) == 0 for row in rows) for rows in self.bands.values()):
            raise ValueError("scene bands cannot contain empty rows")
        return self


class IngestRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    water_body_id: str = Field(min_length=1, max_length=120, pattern=r"^[A-Za-z0-9_.:-]+$")
    scene: ScenePayload | None = None
    scene_path: str | None = None
    acquisition_date: date | None = None

    @model_validator(mode="after")
    def require_one_source(self) -> "IngestRequest":
        if (self.scene is None) == (self.scene_path is None):
            raise ValueError("provide exactly one of scene or scene_path")
        return self


class IngestResponse(BaseModel):
    scene_id: str
    water_body_id: str
    source: str
    acquisition_date: date


class HABObservation(BaseModel):
    source: str = Field(min_length=1, max_length=120)
    observed_on: date
    severity: float = Field(ge=0.0, le=1.0)
    note: str | None = Field(default=None, max_length=500)


class AnalyzeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    scene_id: str = Field(min_length=1)
    hab_observations: list[HABObservation] = Field(default_factory=list, max_length=50)


class ActivityRisk(BaseModel):
    score: float = Field(ge=0.0, le=1.0)
    label: str
    rationale: str


class QualitySummary(BaseModel):
    pixels_analyzed: int
    water_coverage: float
    turbidity_ntu: float
    chlorophyll_a_ug_l: float
    turbidity_p90_ntu: float
    chlorophyll_a_p90_ug_l: float
    quality_uncertainty: float


class Explanation(BaseModel):
    summary: str
    pixels_analyzed: int
    band_signals: list[str]
    alert_date: date
    uncertainty: float
    limitations: list[str]


class AnalyzeResponse(BaseModel):
    scene_id: str
    water_body_id: str
    acquisition_date: date
    risk: dict[str, ActivityRisk]
    quality: QualitySummary
    explanation: Explanation
    water_mask: dict[str, Any]


class HealthResponse(BaseModel):
    status: str
    scenes_loaded: int
    results_available: int
    version: str
