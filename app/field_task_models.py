from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

TaskPriority = Literal["low", "medium", "high", "urgent"]
TaskType = Literal["verify_source", "collect_sample", "confirm_alternative"]
TaskStatus = Literal["pending", "in-progress", "done"]


class FieldTaskCreate(BaseModel):
    model_config = ConfigDict(extra="ignore")

    water_body_id: str = Field(min_length=1, max_length=120)
    title: str = Field(default="", max_length=160)
    action: str = Field(default="", max_length=500)
    priority: TaskPriority = "medium"
    task_type: TaskType | None = None
    target_water_point_id: str | None = Field(default=None, max_length=120)
    evidence_note: str | None = Field(default=None, max_length=2000)

    @field_validator("task_type", mode="before")
    @classmethod
    def normalize_task_type(cls, value: object) -> object:
        return value.replace("-", "_") if isinstance(value, str) else value


class FieldTask(FieldTaskCreate):
    task_id: str
    source: str
    created_at: datetime
    status: TaskStatus = "pending"
    reroute_reason: str | None = None


class FieldTaskStatusUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: TaskStatus | None = None
    evidence_note: str | None = Field(default=None, max_length=2000)


class RerouteTaskRequest(BaseModel):
    task_id: str = Field(min_length=1)
    alternative_water_point_id: str = Field(min_length=1, max_length=120)
    reason: str = Field(min_length=1, max_length=500)


class RerouteHookRequest(BaseModel):
    water_body_id: str = Field(min_length=1, max_length=120)
    alternatives: list[dict[str, object]] = Field(default_factory=list)


class NetworkDecisionTaskRequest(BaseModel):
    model_config = ConfigDict(extra="allow")

    water_body_id: str = Field(min_length=1, max_length=120)
    source: str | None = Field(default=None, max_length=120)
    source_id: str | None = Field(default=None, max_length=120)
    sample_location: str | None = Field(default=None, max_length=120)
    sample_location_id: str | None = Field(default=None, max_length=120)
    alternative: str | None = Field(default=None, max_length=120)
    alternative_id: str | None = Field(default=None, max_length=120)
    alternatives: list[dict[str, object]] = Field(default_factory=list)
