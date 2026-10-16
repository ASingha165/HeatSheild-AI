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

    missing_params: List[MissingParameter] = []
    user_questions: List[str] = []

    # Check temperature specificity
    if not any(k in rep_lower for k in ["°c", "°f", "degrees", "celsius", "fahrenheit"]):
        missing_params.append(
            MissingParameter(
                parameter_name="ambient_temperature_reading",
                importance="CRITICAL",
                description="Specific daytime ambient temperature measurement or heat advisory level.",
                suggested_source="Nearest NOAA/NWS automated surface observation station (ASOS) or IoT micro-sensor."
            )
        )
        user_questions.append("What specific peak daytime temperature or heat advisory tier was observed?")

    # Check canopy/vegetation specificity
    if not any(k in rep_lower for k in ["canopy", "ndvi", "tree cover", "vegetation percentage", "%"]):
        missing_params.append(
            MissingParameter(
                parameter_name="canopy_coverage_metric",
                importance="HIGH",
                description="Quantified tree canopy percentage or satellite vegetative density index.",
                suggested_source="Municipal LiDAR canopy assessment or Landsat-8/Sentinel-2 NDVI spectral bands."
            )
        )
        user_questions.append("Can you estimate the approximate percentage of tree canopy or shade along the sidewalks?")

    # Check exposure / vulnerable facility specifics
    if not any(k in rep_lower for k in ["transit", "bus", "pedestrian", "school", "clinic", "elderly", "crowd"]):
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
        # Fallback if report was fairly detailed
        missing_params.append(
            MissingParameter(
                parameter_name="ground_surface_material_survey",
                importance="MODERATE",
                description="Pavement albedo and percentage of permeable vs impervious ground cover.",
                suggested_source="Municipal street pavement inventory or high-resolution orthophotography."
            )
        )
        user_questions.append("Would you like to specify surface pavement types (e.g., black asphalt vs concrete) to refine cooling models?")

    telemetry_sources = [
        "NOAA Automated Surface Observing Systems (ASOS)",
        "Sentinel-2 Level-2A Multi-Spectral Surface Reflectance (10m resolution)",
        "Municipal Open Data GIS Portal (Urban Tree Canopy & Public Transit GIS layers)",
        "USGS Landsat 9 Thermal Infrared Sensor (TIRS-2)"
    ]

    summary = (
        f"Data completeness review for report on '{loc_data['name']}': Identified {len(missing_params)} "
        f"missing or uncertain parameters necessary for robust environmental modeling. "
        "Formulated actionable clarification questions to prompt higher-fidelity observations."
    )

    limitations = [
        "Inferred data gaps are based on keyword analysis of the user narrative and sample benchmark indicators.",
        "Public data sources may have latency ranging from 24 hours (satellite pass) to annual (LiDAR surveys)."
    ]

    elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)

    return ClarificationRequestResult(
        execution_time_ms=elapsed_ms,
        location_name=loc_data["name"],
        missing_parameters=missing_params,
        suggested_user_questions=user_questions,
        suggested_telemetry_sources=telemetry_sources,
        recommended_next_step="Request user clarification or pull automated regional weather telemetry.",
        analysis_summary=summary,
        known_limitations=limitations,
    )
