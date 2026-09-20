"""Import-compatible shim for the original get-pak-inspired estimators."""

from .get_pak.methods import (
    B3,
    B4,
    B5,
    B8,
    Estimate,
    estimate_chlorophyll_a,
    estimate_from_bands,
    estimate_turbidity,
    finite_summary,
)

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
