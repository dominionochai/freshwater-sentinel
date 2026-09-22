from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_community_profiles_endpoint_returns_seed_profiles():
    response = client.get("/community-profiles")

    assert response.status_code == 200
    profiles = response.json()
    assert len(profiles) == 9
    assert profiles[0]["names"] == ["Khaoleya borehole 4"]
    assert profiles[0]["community"] == "Khaoleya"
    assert set(profiles[0]) == {"names", "community", "children", "school", "pets"}

    demo = next(profile for profile in profiles if profile["name"] == "Demo Lake community")
    assert demo == {
        "names": ["Demo Lake community"],
        "community": "Demo Lake community",
        "children": [{"age_group": "under_10", "count": 14}],
        "school": "Demo Lake Primary School",
        "pets": [{"households_with_pets": 3}],
        "name": "Demo Lake community",
        "language": "en",
        "preferred_channel": "dashboard",
    }
