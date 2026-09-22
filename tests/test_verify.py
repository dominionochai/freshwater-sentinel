from datetime import date

from app.verify import verify_alert


def test_verify_alert_hit_uses_first_following_case_and_district_filter():
    result = verify_alert(
        date(2024, 1, 1),
        "Central",
        [
            {"week": "2023-12-25", "district": "Central", "cases": 9},
            {"week": "2024-01-08T00:00:00Z", "district": "Central", "cases": 2},
            {"week": date(2024, 1, 15), "district": "Central", "cases": 1},
            {"week": "2024-01-08", "district": "North", "cases": 20},
        ],
    )

    assert result == {
        "status": "HIT",
        "lead_time_weeks": 1.0,
        "alert_week": "2024-01-01",
        "district": "Central",
        "first_case_week": "2024-01-08",
        "cases_observed": 3,
        "horizon_weeks": 6,
    }


def test_verify_alert_miss_ignores_same_week_out_of_horizon_and_other_district():
    result = verify_alert(
        "2024-01-01T12:30:00Z",
        "Central",
        [
            {"week": "2024-01-01", "district": "Central", "cases": 4},
            {"week": "2024-02-19", "district": "Central", "cases": 3},
            {"week": "2024-01-08", "district": "North", "cases": 8},
        ],
        horizon_weeks=6,
    )

    assert result == {
        "status": "MISS",
        "lead_time_weeks": None,
        "alert_week": "2024-01-01",
        "district": "Central",
        "first_case_week": None,
        "cases_observed": 0,
        "horizon_weeks": 6,
    }
