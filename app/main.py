"""FastAPI entrypoint for Freshwater Sentinel."""
from __future__ import annotations

from uuid import uuid4

from fastapi import FastAPI, HTTPException

from app import __version__
from app.alerts import build_human_alert
from app.community_data import load_community_profiles
from app.earth_search import scene_from_stac_item_url
from app.field_task_routes import router as field_task_router
from app.health_linkage import build_health_linkage
from app.models import (
    AnalyzeRequest,
    AnalyzeResponse,
    HealthLinkageResponse,
    HealthResponse,
    HumanAlert,
    HumanAlertRequest,
    IngestRequest,
    IngestResponse,
)
from app.network_routes import router as network_router
from app.pipeline import Scene, analyze, scene_from_geotiff, scene_from_payload
from app.satellite import analyze_scene

app = FastAPI(
    title="Urban Freshwater Sentinel",
    version=__version__,
    description="Water-only multispectral screening with explainable activity risk.",
)
app.include_router(network_router)
app.include_router(field_task_router)
SCENES: dict[str, Scene] = {}
LATEST_BY_WATER_BODY: dict[str, AnalyzeResponse] = {}


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        scenes_loaded=len(SCENES),
        results_available=len(LATEST_BY_WATER_BODY),
        version=__version__,
    )


@app.get("/community-profiles")
def community_profiles() -> list[dict[str, object]]:
    return load_community_profiles()


@app.get("/health-linkage", response_model=HealthLinkageResponse)
def health_linkage() -> HealthLinkageResponse:
    return build_health_linkage()


@app.post("/ingest", response_model=IngestResponse, status_code=201)
def ingest(request: IngestRequest) -> IngestResponse:
    try:
        if request.scene is not None:
            scene = scene_from_payload(request.water_body_id, request.scene, request.acquisition_date)
        elif request.scene_path is not None:
            scene = scene_from_geotiff(request.water_body_id, request.scene_path, request.acquisition_date)
        else:
            assert request.stac_item_url is not None
            scene = scene_from_stac_item_url(
                request.stac_item_url,
                water_body_id=request.water_body_id,
                requested_date=request.acquisition_date,
            )
    except (AssertionError, FileNotFoundError, OSError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    scene_id = f"scene-{uuid4().hex}"
    SCENES[scene_id] = scene
    return IngestResponse(
        scene_id=scene_id,
        water_body_id=scene.water_body_id,
        source=scene.source,
        acquisition_date=scene.acquisition_date,
        metadata=scene.metadata,
    )


@app.post("/analyze", response_model=AnalyzeResponse)
def run_analysis(request: AnalyzeRequest) -> AnalyzeResponse:
    scene = SCENES.get(request.scene_id)
    if scene is None:
        raise HTTPException(status_code=404, detail=f"scene not found: {request.scene_id}")
    try:
        result = analyze(scene, request.hab_observations)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    result = result.model_copy(update={"scene_id": request.scene_id})
    if request.community_profile is not None:
        result = result.model_copy(
            update={"human_alert": build_human_alert(result.risk, request.community_profile)}
        )
    LATEST_BY_WATER_BODY[scene.water_body_id] = result
    return result


@app.post("/alerts/human", response_model=HumanAlert)
def human_alert(request: HumanAlertRequest) -> HumanAlert:
    return build_human_alert(request.risk, request.community_profile)


@app.get("/risk/{water_body_id}", response_model=AnalyzeResponse)
def latest_risk(water_body_id: str) -> AnalyzeResponse:
    result = LATEST_BY_WATER_BODY.get(water_body_id)
    if result is None:
        raise HTTPException(status_code=404, detail=f"no analysis found for water body: {water_body_id}")
    return result


@app.get("/api/eyes/{tile}/{date}")
def eyes(tile: str, date: str) -> dict[str, object]:
    try:
        return analyze_scene(tile, date)
    except (FileNotFoundError, OSError, ValueError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
