from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_human_alert_endpoint_preserves_bilingual_profile():
    response = client.post(
        "/alerts/human",
        json={
            "risk": {
                "drinking": {"score": 0.8, "label": "red", "rationale": "screening"}
            },
            "community_profile": {
                "name": "Kisumu shore",
                "language": "sw",
                "preferred_channel": "sms",
            },
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["severity"] == "red"
    assert payload["language"] == "sw"
    assert "Kisumu shore" in payload["message"]


def test_health_contract_is_unchanged():
    response = client.get("/health")
    assert response.status_code == 200
    assert set(response.json()) == {
        "status",
        "scenes_loaded",
        "results_available",
        "version",
    }
