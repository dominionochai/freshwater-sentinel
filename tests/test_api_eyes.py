from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_eyes_returns_scene_summary() -> None:
    summary = {
        "scene_date": "2024-01-15",
        "ndwi_min": -0.2,
        "ndwi_mean": 0.1,
        "ndwi_max": 0.4,
        "water_pixel_share": 0.7,
        "anomaly_flag": True,
    }

    with patch("app.main.analyze_scene", return_value=summary) as mocked:
        response = client.get("/api/eyes/36LVM/2024-01-15")

    assert response.status_code == 200
    assert response.json() == summary
    mocked.assert_called_once_with("36LVM", "2024-01-15")


def test_eyes_returns_json_404_when_scene_is_unavailable() -> None:
    with patch(
        "app.main.analyze_scene",
        side_effect=FileNotFoundError("scene unavailable"),
    ) as mocked:
        response = client.get("/api/eyes/36LVM/2024-01-15")

    assert response.status_code == 404
    assert response.json() == {"detail": "scene unavailable"}
    mocked.assert_called_once_with("36LVM", "2024-01-15")
