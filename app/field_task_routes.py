from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.field_ops import (
    create_field_task,
    create_tasks_from_network_decision,
    get_field_task,
    list_field_tasks,
    reroute_field_task,
    reroute_task_hook,
    update_field_task,
)
from app.field_task_models import (
    FieldTask,
    FieldTaskCreate,
    FieldTaskStatusUpdate,
    NetworkDecisionTaskRequest,
    RerouteHookRequest,
    RerouteTaskRequest,
    TaskStatus,
)

router = APIRouter(prefix="/field-tasks", tags=["field-tasks"])
queue_router = APIRouter(prefix="/field", tags=["field-tasks"])


@router.post("", response_model=FieldTask, status_code=201)
@queue_router.post("/tasks", response_model=FieldTask, status_code=201)
def create_task(request: FieldTaskCreate) -> FieldTask:
    return create_field_task(request)


@router.get("", response_model=list[FieldTask])
@queue_router.get("/tasks", response_model=list[FieldTask])
def tasks(status: TaskStatus | None = None) -> list[FieldTask]:
    return list_field_tasks(status)


@router.get("/{task_id}", response_model=FieldTask)
@queue_router.get("/tasks/{task_id}", response_model=FieldTask)
def task(task_id: str) -> FieldTask:
    result = get_field_task(task_id)
    if result is None:
        raise HTTPException(status_code=404, detail=f"field task not found: {task_id}")
    return result


@router.patch("/{task_id}", response_model=FieldTask)
@queue_router.patch("/tasks/{task_id}", response_model=FieldTask)
def update_task(task_id: str, request: FieldTaskStatusUpdate) -> FieldTask:
    try:
        return update_field_task(task_id, request)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"field task not found: {exc.args[0]}") from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/reroute", response_model=FieldTask)
@queue_router.post("/tasks/reroute", response_model=FieldTask)
def reroute(request: RerouteTaskRequest) -> FieldTask:
    try:
        return reroute_field_task(request)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"field task not found: {exc.args[0]}") from exc


@router.post("/reroute-hook", response_model=list[FieldTask])
@queue_router.post("/tasks/reroute-hook", response_model=list[FieldTask])
def reroute_hook(request: RerouteHookRequest) -> list[FieldTask]:
    return reroute_task_hook(request.model_dump())


@router.post("/from-network", response_model=list[FieldTask], status_code=201)
@queue_router.post("/tasks/from-network", response_model=list[FieldTask], status_code=201)
def tasks_from_network(request: NetworkDecisionTaskRequest) -> list[FieldTask]:
    try:
        return create_tasks_from_network_decision(request.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/reroute-recommendation", response_model=list[FieldTask], status_code=201)
@queue_router.post("/tasks/reroute-recommendation", response_model=list[FieldTask], status_code=201)
def reroute_recommendation(request: NetworkDecisionTaskRequest) -> list[FieldTask]:
    return tasks_from_network(request)
