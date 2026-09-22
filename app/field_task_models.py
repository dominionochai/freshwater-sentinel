from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


TaskPriority = Literal["low", "medium", "high", "urgent"]
TaskStatus = Literal["open", "in_progress", "completed", "rerouted"]


class FieldTaskCreate(BaseModel):
    water_body_id: str = Field(min_length=1, max_length=120)
    title: str = Field(min_length=1, max_length=160)
    action: str = Field(min_length=1, max_length=500)
    priority: TaskPriority = "medium"
    target_water_point_id: str | None = Field(default=None, max_length=120)


class FieldTask(FieldTaskCreate):
    task_id: str
    source: str
    created_at: datetime
    status: TaskStatus = "open"
    reroute_reason: str | None = None


class RerouteTaskRequest(BaseModel):
    task_id: str = Field(min_length=1)
    alternative_water_point_id: str = Field(min_length=1, max_length=120)
    reason: str = Field(min_length=1, max_length=500)


class RerouteHookRequest(BaseModel):
    water_body_id: str = Field(min_length=1, max_length=120)
    alternatives: list[dict[str, object]] = Field(default_factory=list)
