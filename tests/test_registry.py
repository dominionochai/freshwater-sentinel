from pathlib import Path

from app.registry import DEMO_SEED_RECORDS, WaterPoint, load_registry


DATASET = Path(__file__).parents[1] / "data" / "malawi_boreholes.csv"


def test_checked_in_extract_loads_khaoleya_and_only_available_measurements():
    records = load_registry(DATASET)

    assert len(records) == 8
    khaoleya = next(record for record in records if record.id == "Khaoleya borehole 4")
    assert khaoleya.lat == -15.92187567
    assert khaoleya.lon == 35.31535983
    assert khaoleya.source_type == "Borehole or tubewell"
    assert khaoleya.status is None
    assert khaoleya.measurements == {
        "date_sample_collected": "2/12/2019",
        "turbidity_ntu": 0.1,
    }


def test_wpdx_aliases_are_typed_and_missing_values_stay_none(tmp_path):
    path = tmp_path / "points.csv"
    path.write_text(
        "id,lat,lon,status,source_type,turbidity_ntu,ph\n"
        "wpdx-1,-15.1,35.2,Functional,Protected spring,0.4,\n",
        encoding="utf-8",
    )

    records = load_registry(path)

    assert records == [
        WaterPoint(
            id="wpdx-1",
            lat=-15.1,
            lon=35.2,
            status="Functional",
            source_type="Protected spring",
            measurements={"turbidity_ntu": 0.4, "ph": None},
        )
    ]


def test_environment_path_is_configuration_and_no_network_is_used(tmp_path, monkeypatch):
    path = tmp_path / "configured.csv"
    path.write_text("water_point_id,latitude,longitude\nconfigured-1,-14,34\n", encoding="utf-8")
    monkeypatch.setenv("WATER_POINT_REGISTRY_CSV", str(path))

    records = load_registry()

    assert records[0].id == "configured-1"
    assert records[0].lat == -14.0
    assert records[0].lon == 34.0


def test_missing_configuration_returns_only_explicit_demo_seeds(tmp_path):
    records = load_registry(tmp_path / "does-not-exist.csv")

    assert records == list(DEMO_SEED_RECORDS)
    assert records
    assert all(record.id.startswith("demo-") for record in records)
    assert records[0].measurements == {"turbidity_ntu": 0.1}
