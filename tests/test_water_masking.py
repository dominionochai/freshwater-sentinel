import numpy as np

from app.water_masking import create_water_mask


def test_default_mask_uses_mndwi_ndvi_and_optional_backend_falls_back():
    bands = {
        "B03": np.full((2, 2), 0.20),
        "B04": np.full((2, 2), 0.08),
        "B08": np.full((2, 2), 0.12),
        "B11": np.full((2, 2), 0.05),
    }

    default_mask, default_diagnostics = create_water_mask(bands)
    optional_mask, optional_diagnostics = create_water_mask(
        bands, use_omniwatermask=True
    )

    np.testing.assert_array_equal(optional_mask, default_mask)
    assert default_diagnostics["water_mask_method"] == "mndwi_ndvi"
    assert optional_diagnostics["water_mask_method"] in {
        "mndwi_ndvi",
        "omniwatermask",
    }
