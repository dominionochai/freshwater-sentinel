from app.forecast import ForecastConfig, backtest_forecast, forecast_district_risk


def test_forecast_emits_pre_case_warning_and_requires_a_recent_lab_sample():
    result = forecast_district_risk(
        "Lake District",
        satellite={"mndwi": 0.8, "turbidity": 0.9, "chlorophyll_a": 0.8, "ndci": 0.7},
        rainfall={"rainfall_pressure": 0.8},
        cholera_rows=[],
        as_of="2024-06-15",
    )
    assert result["alert"] == "PRE-CASE WARNING"
    assert result["pre_case_warning"] is True
    assert result["action"] == "FIELD SAMPLE REQUIRED"
    assert sum(result["weights"].values()) == 1.0


def test_backtest_uses_dates_and_returns_lead_time_in_weeks():
    forecasts = [{"district": "Lake District", "as_of": "2024-06-01", "pre_case_warning": True}]
    cases = [{"district": "Lake District", "date": "2024-06-15", "cases": 2}]
    result = backtest_forecast(forecasts, cases)
    assert result == [{
        "district": "Lake District",
        "forecast_date": "2024-06-01",
        "outcome": "HIT",
        "grade": "HIT",
        "event_date": "2024-06-15",
        "lead_time_weeks": 2.0,
    }]


def test_configurable_sample_age_is_respected():
    result = forecast_district_risk(
        "A", satellite={}, rainfall=None,
        cholera_rows=[{"district": "A", "date": "2024-06-15", "lab_sample_date": "2024-06-01", "cases": 0}],
        as_of="2024-06-15", config=ForecastConfig(sample_max_age_days=14),
    )
    assert result["field_sample_required"] is True
