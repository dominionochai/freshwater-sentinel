from fastapi.testclient import TestClient

from app.field_task_routes import router
from app.main import app

client = TestClient(app)


def test_field_task_lifecycle_and_reroute():
    created = client.post("/field-tasks", json={"water_body_id": "lake-1", "title": "Inspect", "action": "Collect a field sample", "priority": "high"})
    assert created.status_code == 201
    task_id = created.json()["task_id"]
    rerouted = client.post("/field-tasks/reroute", json={"task_id": task_id, "alternative_water_point_id": "point-2", "reason": "Original point unsafe"})
    assert rerouted.status_code == 200
    assert rerouted.json()["status"] == "rerouted"
    assert rerouted.json()["target_water_point_id"] == "point-2"


def test_network_reroute_hook_creates_only_safe_alternatives():
    result = client.post("/field-tasks/reroute-hook", json={"water_body_id": "lake-2", "alternatives": [{"node_id": "safe-1", "safety_state": "SAFE"}, {"node_id": "unsafe-1", "safety_state": "UNSAFE"}]})
    assert result.status_code == 200
    assert len(result.json()) == 1
    assert result.json()[0]["target_water_point_id"] == "safe-1"
