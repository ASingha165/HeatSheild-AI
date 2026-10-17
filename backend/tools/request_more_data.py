"""
REQUEST_MORE_DATA: Tool for identifying missing data and generating structured clarification requests.
"""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from backend.data.sample_dataset import DATASET_METADATA, lookup_sample_location


class MissingParameter(BaseModel):
    parameter_name: str
    importance: str  # CRITICAL, HIGH, MODERATE
    description: str
    suggested_source: str


class ClarificationRequestResult(BaseModel):
    tool_name: str = "REQUEST_MORE_DATA"
    status: str = "success"
    execution_time_ms: float
    is_synthetic_data: bool = True
    data_label: str = DATASET_METADATA["dataset_label"]
    disclaimer: str = DATASET_METADATA["disclaimer"]
    
    location_name: str
    missing_parameters: List[MissingParameter]
    suggested_user_questions: List[str]
    suggested_telemetry_sources: List[str]
    recommended_next_step: str
    analysis_summary: str
    known_limitations: List[str]


def request_more_data(
    report: str,
    location: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
) -> ClarificationRequestResult:
    """Identifies missing information and generates a structured clarification request."""
    start_time = time.perf_counter()
    loc_data = lookup_sample_location(location or report)
    rep_lower = report.lower()
    ctx = context or {}

    missing_params: List[MissingParameter] = []
    user_questions: List[str] = []

    # Check temperature specificity in context or report
    has_ambient = (
        ctx.get("ambient_temperature_c") is not None
        or ctx.get("ambient_temp_c") is not None
    )
    has_temp_in_report = any(k in rep_lower for k in ["°c", "°f", "degrees", "celsius", "fahrenheit"])
    if not (has_ambient or has_temp_in_report):
        missing_params.append(
            MissingParameter(
                parameter_name="ambient_temperature_reading",
                importance="CRITICAL",
                description="Specific daytime ambient temperature measurement or heat advisory level.",
                suggested_source="Nearest NOAA/NWS automated surface observation station (ASOS) or IoT micro-sensor."
            )
        )
        user_questions.append("What specific peak daytime temperature or heat advisory tier was observed?")

    # Check canopy/vegetation specificity in context or report
    has_canopy = (
        ctx.get("canopy_coverage_pct") is not None
        or ctx.get("ndvi_index") is not None
        or ctx.get("canopy_pct") is not None
        or ctx.get("ndvi") is not None
    )
    has_canopy_in_report = any(k in rep_lower for k in ["canopy", "ndvi", "tree cover", "vegetation percentage", "%"])
    if not (has_canopy or has_canopy_in_report):
        missing_params.append(
            MissingParameter(
                parameter_name="canopy_coverage_metric",
                importance="HIGH",
                description="Quantified tree canopy percentage or satellite vegetative density index.",
                suggested_source="Municipal LiDAR canopy assessment or Landsat-8/Sentinel-2 NDVI spectral bands."
            )
        )
        user_questions.append("Can you estimate the approximate percentage of tree canopy or shade along the sidewalks?")

    # Check exposure / vulnerable facility specifics in context or report
    has_exposure = (
        ctx.get("daily_transit_commuters") is not None
        or ctx.get("unshaded_waiting_areas") is not None
        or ctx.get("transit_stops_count") is not None
        or ctx.get("commuters") is not None
    )
    has_exposure_in_report = any(k in rep_lower for k in ["transit", "bus", "pedestrian", "school", "clinic", "elderly", "crowd"])
    if not (has_exposure or has_exposure_in_report):
        missing_params.append(
            MissingParameter(
                parameter_name="pedestrian_exposure_density",
                importance="HIGH",
                description="Pedestrian volumes, presence of transit waiting stops, or proximity to sensitive facilities.",
                suggested_source="Municipal GIS social vulnerability index (SVI) or transit agency boarding records."
            )
        )
        user_questions.append("Are there specific bus stops, schools, senior centers, or unshaded waiting zones nearby?")

    if not missing_params:
        # Core telemetry is supplied; identify advanced microclimate telemetry needs
        missing_params.append(
            MissingParameter(
                parameter_name="diurnal_temperature_profile",
                importance="MODERATE",
                description="Continuous 24-hour diurnal microclimate telemetry to quantify nocturnal heat retention.",
                suggested_source="Localized IoT microclimate sensor logger or high-resolution thermal drone survey."
            )
        )
        user_questions.append("Would you like to include 24-hour diurnal thermal profile measurements to refine nighttime cooling models?")

    telemetry_sources = [
        "NOAA Automated Surface Observing Systems (ASOS)",
        "Sentinel-2 Level-2A Multi-Spectral Surface Reflectance (10m resolution)",
        "Municipal Open Data GIS Portal (Urban Tree Canopy & Public Transit GIS layers)",
        "USGS Landsat 9 Thermal Infrared Sensor (TIRS-2)"
    ]

    location_name = location or loc_data["name"]
    summary = (
        f"Data completeness review for report on '{location_name}': Identified {len(missing_params)} "
        f"missing or uncertain parameters necessary for robust environmental modeling. "
        "Formulated actionable clarification questions to prompt higher-fidelity observations."
    )

    limitations = [
        "Inferred data gaps are based on keyword analysis of the user narrative and sample benchmark indicators.",
        "Public data sources may have latency ranging from 24 hours (satellite pass) to annual (LiDAR surveys)."
    ]

    data_label = str(ctx.get("dataset_label") or ctx.get("data_source") or DATASET_METADATA["dataset_label"])
    elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)

    return ClarificationRequestResult(
        execution_time_ms=elapsed_ms,
        location_name=location_name,
        missing_parameters=missing_params,
        suggested_user_questions=user_questions,
        suggested_telemetry_sources=telemetry_sources,
        recommended_next_step="Request user clarification or pull automated regional weather telemetry.",
        analysis_summary=summary,
        known_limitations=limitations,
        data_label=data_label,
    )
