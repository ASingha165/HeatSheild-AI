"""
CHECK_EXPOSURE: Tool for evaluating vulnerable populations and urban human exposure.
"""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from backend.data.sample_dataset import DATASET_METADATA, lookup_sample_location


class VulnerableFacility(BaseModel):
    name: str
    type: str
    distance_m: int


class ExposureAnalysisResult(BaseModel):
    tool_name: str = "CHECK_EXPOSURE"
    status: str = "success"
    execution_time_ms: float
    is_synthetic_data: bool = True
    data_label: str = DATASET_METADATA["dataset_label"]
    disclaimer: str = DATASET_METADATA["disclaimer"]
    
    # Quantitative Exposure Metrics
    location_name: str
    overall_exposure_level: str = Field(
        ...,
        description="CRITICAL_EXPOSURE, ELEVATED_EXPOSURE, or CONTROLLED_EXPOSURE"
    )
    transit_stops_count: int
    daily_transit_commuters: int
    unshaded_waiting_areas: int
    pedestrian_dwell_risk: str
    vulnerable_facilities: List[VulnerableFacility]
    high_exposure_hotspots: List[str]
    analysis_summary: str
    known_limitations: List[str]


def check_exposure(
    report: str,
    location: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
) -> ExposureAnalysisResult:
    """Evaluates indicators of human exposure, including transit stops, unshaded areas, and vulnerable facilities."""
    start_time = time.perf_counter()
    loc_data = lookup_sample_location(location or report)
    metrics = loc_data["synthetic_measurements"]
    ctx = context or {}

    stops_raw = ctx.get("transit_stops_count", ctx.get("transit_stops"))
    stops = int(stops_raw) if stops_raw is not None else int(metrics.get("transit_stops_count", 4))

    commuters_raw = ctx.get("daily_transit_commuters", ctx.get("commuters"))
    commuters = int(commuters_raw) if commuters_raw is not None else int(metrics.get("daily_transit_commuters", 5000))

    unshaded_raw = ctx.get("unshaded_waiting_areas", ctx.get("unshaded_stops"))
    unshaded = int(unshaded_raw) if unshaded_raw is not None else int(metrics.get("unshaded_waiting_areas", 2))

    raw_facs = ctx.get("vulnerable_facilities")
    if raw_facs is None:
        raw_facs = metrics.get("vulnerable_facilities", [])
    facilities = [VulnerableFacility(**f) if isinstance(f, dict) else f for f in raw_facs]

    if unshaded >= 3 or commuters >= 10000 or len(facilities) >= 2:
        exposure_level = "CRITICAL_EXPOSURE"
        dwell_risk = "HIGH (Commuters and sensitive groups endure >15 minute unshaded exposure during peak radiant hours)"
    elif unshaded >= 1 or commuters >= 4000 or len(facilities) >= 1:
        exposure_level = "ELEVATED_EXPOSURE"
        dwell_risk = "MODERATE (Intermittent shade deficits affect daily transit transfers)"
    else:
        exposure_level = "CONTROLLED_EXPOSURE"
        dwell_risk = "LOW (Sufficient pedestrian shelters or low dwell times)"

    hotspots: List[str] = []
    if unshaded > 0:
        hotspots.append(f"{unshaded} unshaded transit boarding platforms with direct solar exposure")
    for fac in facilities:
        hotspots.append(f"{fac.name} ({fac.type.replace('_', ' ').title()}) situated within {fac.distance_m}m of high heat zone")
    if commuters >= 5000:
        hotspots.append(f"Heavy commuter volume ({commuters:,} daily passengers) concentrated during peak thermal window")

    location_name = location or loc_data["name"]
    summary = (
        f"Human exposure analysis for {location_name} indicates {exposure_level}. "
        f"The zone features {stops} transit stops serving {commuters:,} daily commuters, with "
        f"{unshaded} unshaded queue zones and {len(facilities)} sensitive community facilities nearby."
    )

    limitations = [
        "Commuter volumes and facility counts are SYNTHETIC sample figures, not real-time transit automated passenger counters (APC).",
        "Individual demographic vulnerability (age, pre-existing respiratory or cardiovascular conditions) is generalized.",
        "Emergency medical service (EMS) dispatch call volumes are not integrated in this baseline tier."
    ]

    data_label = str(ctx.get("dataset_label") or ctx.get("data_source") or DATASET_METADATA["dataset_label"])
    elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)

    return ExposureAnalysisResult(
        execution_time_ms=elapsed_ms,
        location_name=location_name,
        overall_exposure_level=exposure_level,
        transit_stops_count=stops,
        daily_transit_commuters=commuters,
        unshaded_waiting_areas=unshaded,
        pedestrian_dwell_risk=dwell_risk,
        vulnerable_facilities=facilities,
        high_exposure_hotspots=hotspots,
        analysis_summary=summary,
        known_limitations=limitations,
        data_label=data_label,
    )
