import numpy as np

from app.alerts import build_network_alert
from app.network_routes import router as network_router
from app.pipeline import Scene, analyze


def test_pipeline_without_network_preserves_existing_response_shape():
    bands = {
        "B02": np.full((20, 20), 0.10, dtype=float),
        "B03": np.full((20, 20), 0.20, dtype=float),
        "B04": np.full((20, 20), 0.08, dtype=float),
        "B05": np.full((20, 20), 0.10, dtype=float),
        "B08": np.full((20, 20), 0.12, dtype=float),
        "B11": np.full((20, 20), 0.05, dtype=float),
    }
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
    paths = {route.path for route in network_router.routes}
    assert "/network/build" in paths
    assert "/network/analyze" in paths
