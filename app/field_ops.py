"""Human-in-the-loop field task operations."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import datetime, timezone
from threading import RLock
from typing import Any
from uuid import uuid4

from app.field_task_models import (
    FieldTask,
    FieldTaskCreate,
    FieldTaskStatusUpdate,
    RerouteTaskRequest,
    TaskStatus,
    TaskType,
)

_TASKS: dict[str, FieldTask] = {}
_LOCK = RLock()
_ALLOWED_STATUS_TRANSITIONS: dict[TaskStatus, frozenset[TaskStatus]] = {
    "pending": frozenset({"pending", "in-progress"}),
    "in-progress": frozenset({"in-progress", "done"}),
    "done": frozenset({"done"}),
}


def _default_title_and_action(task_type: TaskType, target: str) -> tuple[str, str]:
    values = {
        "verify_source": (f"Verify source {target}", f"Verify source {target} in the field"),
        "collect_sample": (f"Collect sample at {target}", f"Collect a field sample at {target}"),
        "confirm_alternative": (f"Confirm alternative {target}", f"Confirm safe alternative {target} before use"),
    }
    return values[task_type]


def create_field_task(request: FieldTaskCreate, *, source: str = "manual") -> FieldTask:
    task_type = request.task_type or "collect_sample"
    target = request.target_water_point_id or request.water_body_id
    default_title, default_action = _default_title_and_action(task_type, target)
    task = FieldTask(
        task_id=uuid4().hex,
        source=source,
        created_at=datetime.now(timezone.utc),
        water_body_id=request.water_body_id,
        title=request.title or default_title,
        action=request.action or default_action,
        priority=request.priority,
        task_type=task_type,
        target_water_point_id=request.target_water_point_id,
        evidence_note=request.evidence_note,
        status="pending",
    )
    with _LOCK:
        _TASKS[task.task_id] = task
    return task


def list_field_tasks(status: TaskStatus | None = None) -> list[FieldTask]:
    with _LOCK:
        tasks = list(_TASKS.values())
    return sorted(
        (task for task in tasks if status is None or task.status == status),
        key=lambda task: (task.created_at, task.task_id),
    )


def get_field_task(task_id: str) -> FieldTask | None:
    with _LOCK:
        return _TASKS.get(task_id)


def update_field_task(task_id: str, request: FieldTaskStatusUpdate) -> FieldTask:
    with _LOCK:
        task = _TASKS.get(task_id)
        if task is None:
            raise KeyError(task_id)
        updates: dict[str, Any] = {}
        if request.status is not None:
            if request.status not in _ALLOWED_STATUS_TRANSITIONS[task.status]:
                raise ValueError(f"invalid status transition: {task.status} -> {request.status}")
            updates["status"] = request.status
        if request.evidence_note is not None:
            updates["evidence_note"] = request.evidence_note
        if not updates:
            return task
        updated = task.model_copy(update=updates)
        _TASKS[task_id] = updated
        return updated


def reroute_field_task(request: RerouteTaskRequest) -> FieldTask:
    with _LOCK:
        task = _TASKS.get(request.task_id)
        if task is None:
            raise KeyError(request.task_id)
        updated = task.model_copy(update={
            "task_type": "confirm_alternative",
            "target_water_point_id": request.alternative_water_point_id,
            "reroute_reason": request.reason,
            "title": f"Confirm alternative {request.alternative_water_point_id}",
            "action": f"Confirm safe alternative {request.alternative_water_point_id} before use",
        })
        _TASKS[task.task_id] = updated
        return updated


def _identifier(value: object) -> str | None:
    if isinstance(value, Mapping):
        for key in ("node_id", "id", "source_id", "alternative_id", "name"):
            if value.get(key) is not None and str(value[key]).strip():
                return str(value[key])
        return None
    return str(value) if value is not None and str(value).strip() else None


def _decision_value(decision: Mapping[str, Any], keys: Sequence[str]) -> str | None:
    for key in keys:
        value = decision.get(key)
        if isinstance(value, (list, tuple)):
            for item in value:
                found = _identifier(item)
                if found:
                    return found
        else:
            found = _identifier(value)
            if found:
                return found
    return None


def create_tasks_from_network_decision(decision: Mapping[str, Any], *, source: str = "network-decision") -> list[FieldTask]:
    water_body_id = _identifier(decision.get("water_body_id")) or _identifier(decision.get("network_id"))
    if not water_body_id:
        raise ValueError("network decision requires water_body_id or network_id")
    source_id = _decision_value(decision, ("source", "source_id", "source_node_id", "source_water_point_id", "alert_node_id", "alert_node_ids")) or water_body_id
    sample = _decision_value(decision, ("sample_location", "sample_location_id", "sample_site", "sample_site_id", "collect_sample_at", "field_sample_location", "field_sample_nodes", "target_water_point_id")) or water_body_id
    alternative = _decision_value(decision, ("alternative", "alternative_id", "recommended_alternative", "recommended_alternative_id", "alternatives", "target_water_point_id")) or water_body_id
    specs = (
        ("verify_source", source_id, f"Verify source {source_id}", f"Verify source {source_id}"),
        ("collect_sample", sample, f"Collect sample at {sample}", f"Collect a field sample at {sample}"),
        ("confirm_alternative", alternative, f"Confirm alternative {alternative}", f"Confirm safe alternative {alternative} before use"),
    )
    return [
        create_field_task(
            FieldTaskCreate(
                water_body_id=water_body_id,
                title=title,
                action=action,
                task_type=task_type,
                priority="high",
                target_water_point_id=target,
            ),
            source=source,
        )
        for task_type, target, title, action in specs
    ]


def reroute_task_hook(event: Mapping[str, object]) -> list[FieldTask]:
    water_body_id = str(event.get("water_body_id", event.get("network_id", "unknown-water-body")))
    alternatives = event.get("alternatives", [])
    if not isinstance(alternatives, Sequence) or isinstance(alternatives, (str, bytes)):
        return []
    created: list[FieldTask] = []
    for alternative in alternatives:
        if not isinstance(alternative, Mapping):
            continue
        point_id = _identifier(alternative.get("node_id"))
        if not point_id or str(alternative.get("safety_state", "SAFE")) != "SAFE":
            continue
        created.append(create_field_task(
            FieldTaskCreate(
                water_body_id=water_body_id,
                title=f"Confirm alternative {point_id}",
                action=f"Confirm safe alternative {point_id} before use",
                priority="high",
                task_type="confirm_alternative",
                target_water_point_id=point_id,
            ),
            source="network-reroute",
        ))
    return created
