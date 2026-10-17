"""
ANALYZE_HEAT: Tool for assessing urban thermal indicators and microclimate risk.
"""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from backend.data.sample_dataset import DATASET_METADATA, lookup_sample_location


class HeatAnalysisResult(BaseModel):
    tool_name: str = "ANALYZE_HEAT"
    status: str = "success"
    execution_time_ms: float
    is_synthetic_data: bool = True
    data_label: str = DATASET_METADATA["dataset_label"]
    disclaimer: str = DATASET_METADATA["disclaimer"]
    
    # Quantitative Thermal Metrics
    location_name: str
    observed_ambient_temp_c: float
    observed_surface_temp_c: float
    heat_index_c: float
    urban_heat_island_delta_c: float = Field(
        ...,
        description="Estimated temperature elevation above regional rural baseline (+2.5°C to +6.0°C)"
    )
    heat_severity_level: str = Field(
        ...,
        description="Risk categorization: LOW, MODERATE, HIGH, SEVERE, or EXTREME"
    )
    nocturnal_retention_risk: str = Field(
        ...,
        description="Evaluation of night-time heat trapping by impervious thermal mass"
    )
    risk_indicators_detected: List[str]
    analysis_summary: str
    known_limitations: List[str]


def analyze_heat(
    report: str,
    location: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
) -> HeatAnalysisResult:
    """Analyzes available temperature observations and explicitly identified heat-risk indicators."""
    start_time = time.perf_counter()
    loc_data = lookup_sample_location(location or report)
    metrics = loc_data["synthetic_measurements"]
    ctx = context or {}

    ambient_raw = ctx.get("ambient_temperature_c")
    if ambient_raw is None:
        ambient_raw = ctx.get("ambient_temp_c")
    ambient = float(ambient_raw) if ambient_raw is not None else float(metrics["ambient_temp_c"])

    surface_raw = ctx.get("surface_temperature_c")
    if surface_raw is None:
        surface_raw = ctx.get("surface_temp_c")
    surface = float(surface_raw) if surface_raw is not None else float(metrics["surface_temp_c"])

    heat_index_raw = ctx.get("heat_index_c")
    if heat_index_raw is not None:
        heat_index = float(heat_index_raw)
    else:
        heat_index = round(ambient + max(2.0, (surface - ambient) * 0.25), 1)

    uhi_delta = round(surface - (ambient - 2.0), 1)

    # Classify severity
    if heat_index >= 42.0:
        severity = "EXTREME"
    elif heat_index >= 38.0:
        severity = "SEVERE"
    elif heat_index >= 33.0:
        severity = "HIGH"
    elif heat_index >= 28.0:
        severity = "MODERATE"
    else:
        severity = "LOW"

    # Classify nocturnal retention
    impervious_raw = ctx.get("impervious_surface_pct")
    if impervious_raw is None:
        impervious_raw = ctx.get("impervious_pct")
    impervious = float(impervious_raw) if impervious_raw is not None else float(metrics.get("impervious_surface_pct", 75.0))

    if impervious >= 85.0:
        retention = "HIGH (Heavy asphalt/concrete mass delays cooling by >4 hours post-sunset)"
    elif impervious >= 60.0:
        retention = "MODERATE (Partial nocturnal dissipation observed)"
    else:
        retention = "LOW (Permeable soils and vegetative moisture enable rapid night cooling)"

    indicators: List[str] = []
    if ambient >= 35.0:
        indicators.append(f"Elevated ambient temperature exceeding 35°C threshold ({ambient}°C)")
    if surface >= 45.0:
        indicators.append(f"Superheated pavement surface ({surface}°C) radiating radiant heat")
    if heat_index >= 40.0:
        indicators.append(f"Hazardous combined thermal heat index ({heat_index}°C)")
    if impervious >= 80.0:
        indicators.append(f"High impervious surface density ({impervious}%) driving nocturnal heat island")

    location_name = location or loc_data["name"]
    summary = (
        f"Microclimate analysis for {location_name} indicates {severity} heat stress. "
        f"Ambient air temperature is {ambient}°C with surface radiative temperatures reaching {surface}°C "
        f"(heat index {heat_index}°C). Nocturnal retention risk is {retention}."
    )

    limitations = [
        "Metrics are sourced from SYNTHETIC development samples and do not reflect real-time ground weather telemetry.",
        "Micro-topographical wind channeling and diurnal atmospheric inversion dynamics are not modeled.",
        "Indoor residential temperatures are not measured; figures apply strictly to ambient exterior public rights-of-way."
    ]

    data_label = str(ctx.get("dataset_label") or ctx.get("data_source") or DATASET_METADATA["dataset_label"])
    elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)

    return HeatAnalysisResult(
        execution_time_ms=elapsed_ms,
        location_name=location_name,
        observed_ambient_temp_c=ambient,
        observed_surface_temp_c=surface,
        heat_index_c=heat_index,
        urban_heat_island_delta_c=uhi_delta,
        heat_severity_level=severity,
        nocturnal_retention_risk=retention,
        risk_indicators_detected=indicators,
        analysis_summary=summary,
        known_limitations=limitations,
        data_label=data_label,
    )
