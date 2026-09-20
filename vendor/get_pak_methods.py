"""Import-compatible shim for the original get-pak-inspired estimators."""

from __future__ import annotations

import sys
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

# ``get-pak`` is a provenance directory and intentionally keeps its upstream
# spelling; load its original methods module without requiring an invalid
# hyphenated Python package name.
_IMPL_NAME = "vendor._get_pak_methods_impl"
_IMPL_PATH = Path(__file__).with_name("get-pak") / "methods.py"
_SPEC = spec_from_file_location(_IMPL_NAME, _IMPL_PATH)
if _SPEC is None or _SPEC.loader is None:  # pragma: no cover - packaging failure
    raise ImportError(f"unable to load estimator implementation: {_IMPL_PATH}")
_IMPL = module_from_spec(_SPEC)
sys.modules[_IMPL_NAME] = _IMPL
_SPEC.loader.exec_module(_IMPL)

B3 = _IMPL.B3
B4 = _IMPL.B4
B5 = _IMPL.B5
B8 = _IMPL.B8
Estimate = _IMPL.Estimate
estimate_chlorophyll_a = _IMPL.estimate_chlorophyll_a
estimate_from_bands = _IMPL.estimate_from_bands
estimate_turbidity = _IMPL.estimate_turbidity
finite_summary = _IMPL.finite_summary

__all__ = [
    "B3",
    "B4",
    "B5",
    "B8",
    "Estimate",
    "estimate_chlorophyll_a",
    "estimate_from_bands",
    "estimate_turbidity",
    "finite_summary",
]
