"""Human-in-the-loop field task operations."""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import datetime, timezone
from threading import RLock
from uuid import uuid4

from app.field_task_models import FieldTask, FieldTaskCreate, RerouteTaskRequest

_TASKS: dict[str, FieldTask] = {}
_LOCK = RLock()


def create_field_task(request: FieldTaskCreate, *, source: str = "manual") -> FieldTask:
    task = FieldTask(task_id=uuid4().hex, source=source, created_at=datetime.now(timezone.utc), **request.model_dump())
    with _LOCK:
        _TASKS[task.task_id] = task
    return task


def list_field_tasks(status: str | None = None) -> list[FieldTask]:
    with _LOCK:
        tasks = list(_TASKS.values())
    return [task for task in tasks if status is None or task.status == status]


def get_field_task(task_id: str) -> FieldTask | None:
    with _LOCK:
        return _TASKS.get(task_id)


def reroute_field_task(request: RerouteTaskRequest) -> FieldTask:
    with _LOCK:
        task = _TASKS.get(request.task_id)
        if task is None:
            raise KeyError(request.task_id)
        updated = task.model_copy(update={"status": "rerouted", "target_water_point_id": request.alternative_water_point_id, "reroute_reason": request.reason})
        _TASKS[task.task_id] = updated
    return updated


def reroute_task_hook(event: Mapping[str, object]) -> list[FieldTask]:
    """Create reviewable tasks from a network reroute event.

    The hook accepts already-computed network output; it never calls an
    external service and only creates tasks for explicit alternatives.
    """
    water_body_id = str(event.get("water_body_id", event.get("network_id", "unknown-water-body")))
    alternatives = event.get("alternatives", [])
    if not isinstance(alternatives, Sequence) or isinstance(alternatives, (str, bytes)):
        return []
    created: list[FieldTask] = []
    for alternative in alternatives:
        if not isinstance(alternative, Mapping):
            continue
        point_id = str(alternative.get("node_id", ""))
        if not point_id or str(alternative.get("safety_state", "SAFE")) != "SAFE":
            continue
        created.append(create_field_task(FieldTaskCreate(water_body_id=water_body_id, title="Verify reroute alternative", action=f"Verify safe water point {point_id} before use", priority="high", target_water_point_id=point_id), source="network-reroute"))
    return created
