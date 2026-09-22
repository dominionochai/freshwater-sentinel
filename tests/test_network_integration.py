import numpy as np

from app.alerts import build_network_alert
from app.main import app
from app.models import HABObservation
from app.network_models import NetworkNode, WaterNetwork
from app.pipeline import Scene, analyze


def test_pipeline_without_network_preserves_existing_response_shape():
    bands = {name: np.ones((20, 20), dtype=float) for name in ("B02", "B03", "B04", "B05", "B08", "B11")}
    result = analyze(Scene("lake-1", __import__("datetime").date.today(), bands, "test"), [])
    assert result.network_analysis is None


def test_network_alert_reroutes_only_to_verified_safe_alternative():
    payload = build_network_alert({"alternatives": [{"node_id": "safe-1", "name": "Safe 1", "safety_state": "SAFE"}]})
    assert payload["alternative_node_id"] == "safe-1"
    assert "Reroute" in payload["message"]

    required = build_network_alert({"alternatives": [{"node_id": "unknown", "safety_state": "FIELD SAMPLE REQUIRED"}]})
    assert "FIELD SAMPLE REQUIRED" in required["message"]
    assert "alternative_node_id" not in required


def test_network_routes_are_registered():
    paths = {route.path for route in app.routes}
    assert "/network/build" in paths
    assert "/network/analyze" in paths
