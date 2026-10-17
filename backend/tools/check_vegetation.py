"""
CHECK_VEGETATION: Tool for evaluating urban canopy coverage and vegetation deficits.
"""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from backend.data.sample_dataset import DATASET_METADATA, lookup_sample_location


class VegetationAnalysisResult(BaseModel):
    tool_name: str = "CHECK_VEGETATION"
    status: str = "success"
    execution_time_ms: float
    is_synthetic_data: bool = True
    data_label: str = DATASET_METADATA["dataset_label"]
    disclaimer: str = DATASET_METADATA["disclaimer"]
    
    # Quantitative Vegetation Metrics
    location_name: str
    canopy_coverage_pct: float
    target_municipal_canopy_pct: float = 30.0
    canopy_deficit_pct: float
    ndvi_index: float = Field(
        ...,
        description="Normalized Difference Vegetation Index [0.0 - 1.0]"
    )
    impervious_surface_pct: float
    deficit_classification: str = Field(
        ...,
        description="CRITICAL_DEFICIT, SEVERE_DEFICIT, MODERATE_DEFICIT, or HEALTHY_CANOPY"
    )
    estimated_cooling_potential_c: float = Field(
        ...,
        description="Estimated localized surface cooling achievable with target 30% canopy expansion"
    )
    recommended_planting_priorities: List[str]
    analysis_summary: str
    known_limitations: List[str]


def check_vegetation(
    report: str,
    location: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
) -> VegetationAnalysisResult:
    """Analyzes available vegetation-coverage and canopy deficit information."""
    start_time = time.perf_counter()
    loc_data = lookup_sample_location(location or report)
    metrics = loc_data["synthetic_measurements"]
    ctx = context or {}

    canopy_raw = ctx.get("canopy_coverage_pct")
    if canopy_raw is None:
        canopy_raw = ctx.get("canopy_pct")
    canopy = float(canopy_raw) if canopy_raw is not None else float(metrics["canopy_coverage_pct"])

    target = 30.0
    deficit = max(0.0, round(target - canopy, 1))

    ndvi_raw = ctx.get("ndvi_index")
    if ndvi_raw is None:
        ndvi_raw = ctx.get("ndvi")
    ndvi = float(ndvi_raw) if ndvi_raw is not None else float(metrics["ndvi_index"])

    impervious_raw = ctx.get("impervious_surface_pct")
    if impervious_raw is None:
        impervious_raw = ctx.get("impervious_pct")
    impervious = float(impervious_raw) if impervious_raw is not None else float(metrics.get("impervious_surface_pct", 75.0))

    if canopy < 10.0:
        deficit_class = "CRITICAL_DEFICIT"
        cooling_potential = 3.5
    elif canopy < 20.0:
        deficit_class = "SEVERE_DEFICIT"
        cooling_potential = 2.4
    elif canopy < 30.0:
        deficit_class = "MODERATE_DEFICIT"
        cooling_potential = 1.2
    else:
        deficit_class = "HEALTHY_CANOPY"
        cooling_potential = 0.4

    priorities: List[str] = []
    if canopy < 15.0:
        priorities.append("Sidewalk buffer planting along active pedestrian corridors")
    if impervious >= 80.0:
        priorities.append("Depaving asphalt parking fringes and median bioswales")
    unshaded_val = ctx.get("unshaded_waiting_areas", metrics.get("unshaded_waiting_areas", 0))
    if int(unshaded_val) > 0:
        priorities.append("Direct shade canopy planting adjacent to public transit queuing zones")

    location_name = location or loc_data["name"]
    summary = (
        f"Vegetation assessment for {location_name} identifies a {deficit_class}. "
        f"Existing canopy coverage is {canopy}% versus municipal target of {target}% "
        f"(deficit: {deficit}%). Expanding vegetative cover could yield an estimated "
        f"{cooling_potential}°C microclimate cooling benefit."
    )

    limitations = [
        "Vegetation and NDVI values are SYNTHETIC demonstration figures, not high-resolution multi-spectral imagery.",
        "Soil permeability, underground utility conflicts, and irrigation water rights are not factored into planting feasibility.",
        "Tree maturation timeline (typically 7-15 years for full shade benefits) is not reflected in instantaneous cooling potential."
    ]

    data_label = str(ctx.get("dataset_label") or ctx.get("data_source") or DATASET_METADATA["dataset_label"])
    elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)

    return VegetationAnalysisResult(
        execution_time_ms=elapsed_ms,
        location_name=location_name,
        canopy_coverage_pct=canopy,
        target_municipal_canopy_pct=target,
        canopy_deficit_pct=deficit,
        ndvi_index=ndvi,
        impervious_surface_pct=impervious,
        deficit_classification=deficit_class,
        estimated_cooling_potential_c=cooling_potential,
        recommended_planting_priorities=priorities,
        analysis_summary=summary,
        known_limitations=limitations,
        data_label=data_label,
    )
