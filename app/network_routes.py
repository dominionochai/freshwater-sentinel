from __future__ import annotations
from pathlib import Path
from fastapi import APIRouter, HTTPException
from app.network import build_water_network, analyze_water_network
from app.network_models import NetworkBuildRequest, NetworkAnalyzeRequest
from app.network_sources import load_default_records

router = APIRouter(prefix='/network', tags=['network'])
NETWORKS = {}


def _rows(rows):
    if rows:
        return rows
    try:
        return load_default_records(Path.cwd())
    except FileNotFoundError as e:
        raise HTTPException(422, detail=f'network records are required; optional fixture unavailable: {e}')


@router.get('/defaults')
def get_default_records():
    """Return the bundled default water-point records as-is, so a caller
    can merge in additional real records (e.g. a lab-confirmed SAFE point)
    without losing the rest of the fixture. Added for the frontend demo,
    which needs at least one genuinely SAFE node to show a recommended
    alternative — the bundled fixture has none on its own.
    """
    try:
        return {"records": load_default_records(Path.cwd())}
    except FileNotFoundError as e:
        raise HTTPException(422, detail=f'default fixture unavailable: {e}')


@router.post('/build')
def build_network(request: NetworkBuildRequest):
    n = build_water_network(_rows(request.records), request.max_distance_km)
    NETWORKS[n.network_id] = n
    return n.to_dict()


@router.post('/analyze')
def analyze_network(request: NetworkAnalyzeRequest):
    n = NETWORKS.get(request.network_id)
    if n is None:
        n = build_water_network(_rows(request.records), request.max_distance_km)
        NETWORKS[n.network_id] = n
    return analyze_water_network(
        n, request.alert_node_ids, request.max_hops, request.decay, request.alternatives_limit
    ).to_dict()
