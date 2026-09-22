"""Validated API request, response, and provenance models."""
from __future__ import annotations

from datetime import date
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.water_quality import QualityMetrics


class ScenePayload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    acquisition_date: date | None = None
    bands: dict[str, list[list[float]]] = Field(min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_rectangular_arrays(self) -> "ScenePayload":
        shapes = {(len(rows), len(rows[0])) if rows else (0, 0) for rows in self.bands.values()}
        if not shapes or (0, 0) in shapes or len(shapes) != 1:
            raise ValueError("all scene bands must be non-empty rectangular arrays of equal shape")
        return self


class IngestRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    water_body_id: str = Field(min_length=1, max_length=120, pattern=r"^[A-Za-z0-9_.\-/]+$")
    scene: ScenePayload | None = None
    scene_path: str | None = None
    stac_item_url: str | None = None
    acquisition_date: date | None = None

    @model_validator(mode="after")
    def require_one_source(self) -> "IngestRequest":
        sources = sum(source is not None for source in (self.scene, self.scene_path, self.stac_item_url))
        if sources != 1:
            raise ValueError("provide exactly one of scene, scene_path, or stac_item_url")
        return self


class IngestResponse(BaseModel):
    scene_id: str
    water_body_id: str
    source: str
    acquisition_date: date
    metadata: dict[str, Any] = Field(default_factory=dict)


class HABObservation(BaseModel):
    source: str = Field(min_length=1, max_length=120)
    observed_on: date
    severity: float = Field(ge=0.0, le=1.0)
    note: str | None = Field(default=None, max_length=500)


class CommunityProfile(BaseModel):
    """Small, privacy-preserving profile used to localize an alert or linkage."""
    names: list[str] = Field(default_factory=list)
    community: str = Field(default="the community", min_length=1, max_length=120)
    children: list[Any] = Field(default_factory=list)
    school: Any | None = None
    pets: list[Any] = Field(default_factory=list)
    name: str = Field(default="the community", min_length=1, max_length=120)
    language: Literal["en", "sw"] = "en"
    preferred_channel: Literal["dashboard", "sms", "whatsapp"] = "dashboard"


class HumanAlert(BaseModel):
    severity: Literal["green", "yellow", "red"]
    language: Literal["en", "sw"]
    title: str
    message: str
    action: str


class HumanAlertRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    risk: dict[str, Any]
    community_profile: CommunityProfile | None = None


class AnalyzeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    scene_id: str = Field(min_length=1)
    hab_observations: list[HABObservation] = Field(default_factory=list, max_length=50)
    community_profile: CommunityProfile | None = None


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
    ndci_mean: float = 0.0
    ndci_chlorophyll_a_ug_l: float = 0.0
    chlorophyll_a_threshold_exceeded: bool = False


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
    scene_metadata: dict[str, Any] = Field(default_factory=dict)
    human_alert: HumanAlert | None = None


class HealthResponse(BaseModel):
    status: str
    scenes_loaded: int
    results_available: int
    version: str


class HealthReport(BaseModel):
    """Synthetic clinic signal used only for a demo linkage."""
    model_config = ConfigDict(extra="forbid")
    report_id: str = Field(min_length=1, max_length=120)
    disease: Literal["cholera", "typhoid"]
    report_date: date
    case_count: int = Field(ge=0)
    water_point_id: str = Field(min_length=1, max_length=120)
    community: str = Field(min_length=1, max_length=120)
    source: Literal["synthetic_demo"] = "synthetic_demo"


class HealthRisk(BaseModel):
    score: float = Field(ge=0.0, le=1.0)
    label: Literal["green", "yellow", "red"]
    rationale: str


class HealthLinkage(BaseModel):
    report_id: str
    disease: Literal["cholera", "typhoid"]
    report_date: date
    cases: int
    water_point_id: str
    community: str
    community_profile: CommunityProfile | None = None
    risk: HealthRisk
    plain_language: str


class HealthLinkageResponse(BaseModel):
    synthetic: bool = True
    source_note: str
    total_reports: int
    total_cases: int
    linkages: list[HealthLinkage]
