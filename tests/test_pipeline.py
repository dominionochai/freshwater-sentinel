"""Small offline tests for water-only quality and API validation."""

import numpy as np
import pytest

from app.models import ScenePayload
from app.water_masking import create_water_mask
from app.water_quality import estimate_quality


def test_water_mask_excludes_land_from_quality():
    shape = (4, 4)
    bands = {
        name: np.full(shape, 0.1, dtype=float)
        for name in ("B02", "B03", "B04", "B05", "B08", "B11")
    }
    bands["B03"][:2] = 0.20
    bands["B11"][:2] = 0.04
    bands["B08"][:2] = 0.12
    bands["B04"][:2] = 0.08
    mask, _ = create_water_mask(bands)
    assert int(mask.sum()) == 8
    metrics = estimate_quality(bands, mask)
    assert metrics.pixels_analyzed == 8


def test_scene_payload_rejects_mismatched_shapes():
    with pytest.raises(ValueError):
        ScenePayload(bands={"B02": [[0.1, 0.2]], "B03": [[0.1]]})
