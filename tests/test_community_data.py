from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_community_profiles_endpoint_returns_seed_profiles():
    response = client.get("/community-profiles")

    assert response.status_code == 200
    profiles = response.json()
    assert len(profiles) == 8
    assert profiles[0]["names"] == ["Khaoleya borehole 4"]
    assert profiles[0]["community"] == "Khaoleya"
    assert set(profiles[0]) == {"names", "community", "children", "school", "pets"}
