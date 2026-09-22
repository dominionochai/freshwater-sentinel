from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.field_ops import create_field_task, get_field_task, list_field_tasks, reroute_field_task, reroute_task_hook
from app.field_task_models import FieldTask, FieldTaskCreate, RerouteHookRequest, RerouteTaskRequest

router = APIRouter(prefix="/field-tasks", tags=["field-tasks"])


@router.post("", response_model=FieldTask, status_code=201)
def create_task(request: FieldTaskCreate) -> FieldTask:
    return create_field_task(request)


@router.get("", response_model=list[FieldTask])
def tasks(status: str | None = None) -> list[FieldTask]:
    return list_field_tasks(status)


@router.get("/{task_id}", response_model=FieldTask)
def task(task_id: str) -> FieldTask:
    result = get_field_task(task_id)
    if result is None:
        raise HTTPException(status_code=404, detail=f"field task not found: {task_id}")
    return result


@router.post("/reroute", response_model=FieldTask)
def reroute(request: RerouteTaskRequest) -> FieldTask:
    try:
        return reroute_field_task(request)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"field task not found: {exc.args[0]}") from exc


@router.post("/reroute-hook", response_model=list[FieldTask])
def reroute_hook(request: RerouteHookRequest) -> list[FieldTask]:
    return reroute_task_hook(request.model_dump())
