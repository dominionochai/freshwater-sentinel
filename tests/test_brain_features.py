import numpy as np
import pytest

from app.pipeline import fuse_environmental_signals
from app.rainfall import rainfall_features
from app.spectral_features import compute_spectral_features


def test_spectral_features_are_deterministic_and_shaped():
    bands = {name: np.ones((2, 2)) for name in ("B03", "B04", "B05", "B08")}
    features = compute_spectral_features(bands)
    assert set(features) == {"ndwi", "ndvi", "ndci", "fai_proxy"}
    assert all(value.shape == (2, 2) for value in features.values())
    assert np.allclose(features["ndvi"], 0.0)


def test_rainfall_does_not_fabricate_empty_input():
    result = rainfall_features(None)
    assert result["observations"] == 0
    assert result["total_mm"] == 0
    assert result["rainfall_pressure"] == 0


def test_pipeline_fuses_supplied_rainfall():
    bands = {name: np.ones((2, 2)) for name in ("B03", "B04", "B05", "B08")}
    result = fuse_environmental_signals(bands, [10, 20, 30])
    assert result["data_status"] == "observed"
    assert result["rainfall"]["total_mm"] == 60
    assert 0 <= result["fusion_score"] <= 1


def test_invalid_rainfall_is_rejected():
    with pytest.raises(ValueError):
        rainfall_features([-1])
