from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_linkage_joins_reports_profiles_and_risk():
    response = client.get("/health-linkage")

    assert response.status_code == 200
    payload = response.json()
    assert payload["synthetic"] is True
    assert payload["total_reports"] == 4
    assert payload["total_cases"] == 14

    khaoleya = next(
        item
        for item in payload["linkages"]
        if item["water_point_id"] == "Khaoleya borehole 4"
        and item["disease"] == "cholera"
    )
    assert khaoleya["community_profile"]["community"] == "Khaoleya"
    assert khaoleya["risk"]["label"] == "red"
    assert "5 cholera cases trace to this water point" in khaoleya["plain_language"]
