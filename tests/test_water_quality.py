import numpy as np

from app.hab_risk import score_risk
from app.water_quality import (
    calculate_ndci,
    detect_chlorophyll_a_threshold,
    estimate_chlorophyll_a_from_ndci,
    estimate_quality,
)


def test_ndci_formula_and_chlorophyll_threshold_detection():
    ndci = calculate_ndci(np.array([0.1]), np.array([0.3]))
    assert np.isclose(ndci[0], 0.5)
    chlorophyll = estimate_chlorophyll_a_from_ndci(ndci)
    assert chlorophyll[0] > 50.0
    assert detect_chlorophyll_a_threshold(chlorophyll)
    assert not detect_chlorophyll_a_threshold(np.array([1.0]))


def test_ndci_screening_is_exposed_to_quality_and_risk():
    bands = {
        "B03": np.full((2, 2), 0.20),
        "B04": np.full((2, 2), 0.10),
        "B05": np.full((2, 2), 0.30),
        "B08": np.full((2, 2), 0.12),
    }
    metrics = estimate_quality(bands, np.ones((2, 2), dtype=bool))

    assert metrics.ndci_mean == 0.5
    assert metrics.chlorophyll_a_threshold_exceeded is True
    assert score_risk(metrics)["swimming"].label == "red"
