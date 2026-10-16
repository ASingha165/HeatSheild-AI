"""
COMPARE_INTERVENTIONS: Tool for evaluating and comparing urban heat mitigation interventions.
"""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from backend.data.sample_dataset import DATASET_METADATA, lookup_sample_location


class InterventionOption(BaseModel):
    intervention_id: str
    name: str
    category: str
    estimated_cooling_delta_c: float = Field(
        ...,
        description="Estimated localized air or surface temperature reduction"
    )
    cooling_mechanism: str
    estimated_cost_tier: str  # LOW, MODERATE, HIGH, VERY_HIGH
    estimated_cost_usd_per_unit: str
    implementation_timeline: str
    durability_years: int
    co_benefits: List[str]
    trade_offs: List[str]
    transparent_assumptions: List[str]


class InterventionComparisonResult(BaseModel):
    tool_name: str = "COMPARE_INTERVENTIONS"
    status: str = "success"
    execution_time_ms: float
    is_synthetic_data: bool = True
    data_label: str = DATASET_METADATA["dataset_label"]
    disclaimer: str = DATASET_METADATA["disclaimer"]
    
    location_name: str
    recommended_primary_intervention: str
    recommended_fast_track_intervention: str
    interventions: List[InterventionOption]
    comparison_matrix_summary: str
    known_limitations: List[str]


def compare_interventions(
    report: str,
    location: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
) -> InterventionComparisonResult:
    """Compares tree planting, shade structures, cool roofs, and shaded pedestrian routes with transparent assumptions."""
    start_time = time.perf_counter()
    loc_data = lookup_sample_location(location or report)
    metrics = loc_data["synthetic_measurements"]
    
    canopy = float(metrics.get("canopy_coverage_pct", 10.0))
    unshaded = int(metrics.get("unshaded_waiting_areas", 2))

    options: List[InterventionOption] = [
        InterventionOption(
            intervention_id="urban_tree_canopy",
            name="Targeted Urban Tree Canopy Expansion",
            category="Green Infrastructure",
            estimated_cooling_delta_c=2.8,
            cooling_mechanism="Evapotranspiration and continuous solar interception",
            estimated_cost_tier="MODERATE",
            estimated_cost_usd_per_unit="$850 - $1,400 per mature sapling planted with deep watering",
            implementation_timeline="3 to 7 years for mature canopy shade",
            durability_years=35,
            co_benefits=[
                "Stormwater runoff retention and pollutant filtering",
                "Particulate matter air purification (PM2.5 / PM10)",
                "Biodiversity enhancement and neighborhood biophilic value"
            ],
            trade_offs=[
                "Requires ongoing irrigation and root barrier maintenance",
                "Delayed cooling benefits while saplings mature"
            ],
            transparent_assumptions=[
                "Assumes 85% sapling survival rate with municipal stewardship",
                "Assumes species selection prioritized for drought-tolerant native broadleafs"
            ]
        ),
        InterventionOption(
            intervention_id="engineered_shade_canopies",
            name="Engineered Shade Structures & Transit Canopies",
            category="Physical Infrastructure",
            estimated_cooling_delta_c=5.2,
            cooling_mechanism="Direct 100% solar radiation blockage over queuing surfaces",
            estimated_cost_tier="LOW_TO_MODERATE",
            estimated_cost_usd_per_unit="$12,000 - $28,000 per transit shelter canopy",
            implementation_timeline="2 to 6 months (Fast-track deployment)",
            durability_years=15,
            co_benefits=[
                "Immediate thermal relief for vulnerable transit riders",
                "Can integrate rooftop solar PV and USB emergency charging stations",
                "Weather protection against rain and hail"
            ],
            trade_offs=[
                "Localized relief footprint limited to shelter perimeter",
                "Does not reduce regional ambient air temperature"
            ],
            transparent_assumptions=[
                "Assumes high-tensile fabric or PV panel overhead with solar reflectance index (SRI) >= 78",
                "Assumes right-of-way permit clearance across municipal bus stops"
            ]
        ),
        InterventionOption(
            intervention_id="high_albedo_cool_pavements",
            name="High-Albedo Cool Roofs & Solar-Reflective Pavements",
            category="Materials & Surface Modification",
            estimated_cooling_delta_c=3.4,
            cooling_mechanism="High Solar Reflectance Index (SRI > 80) prevents surface heat absorption",
            estimated_cost_tier="MODERATE",
            estimated_cost_usd_per_unit="$2.50 - $4.00 per sq ft of surface coating",
            implementation_timeline="6 to 12 months",
            durability_years=8,
            co_benefits=[
                "Dramatically reduces building cooling energy demands (up to 18%)",
                "Suppresses night-time thermal mass radiative discharge"
            ],
            trade_offs=[
                "Reflected glare can cause discomfort if applied to high-traffic pedestrian crosswalks",
                "Coating re-application required every 6 to 10 years"
            ],
            transparent_assumptions=[
                "Assumes initial solar reflectance > 0.65 and thermal emittance > 0.85",
                "Assumes commercial building owners participate in municipal cool roof rebate program"
            ]
        ),
        InterventionOption(
            intervention_id="shaded_green_corridor",
            name="Protected Shaded Green Pedestrian Corridor",
            category="Integrated Transit & Pedestrian Route",
            estimated_cooling_delta_c=4.1,
            cooling_mechanism="Combined micro-canopy trees, permeable pavers, and bioswales along commuter route",
            estimated_cost_tier="HIGH",
            estimated_cost_usd_per_unit="$180,000 - $350,000 per linear pedestrian block",
            implementation_timeline="1 to 2 years",
            durability_years=25,
            co_benefits=[
                "Encourages active pedestrian and micro-mobility commuting",
                "Reduces vehicular traffic heat emission along corridor",
                "Connects residential sectors directly to transit nodes"
            ],
            trade_offs=[
                "Requires comprehensive traffic engineering and parking reallocations",
                "Higher upfront capital budgeting requirement"
            ],
            transparent_assumptions=[
                "Assumes 1.2 km contiguous right-of-way easement",
                "Assumes co-funding from regional transit and clean air grants"
            ]
        )
    ]

    # Prioritize primary recommendations based on current deficit
    if unshaded >= 2:
        recommended_fast = "Engineered Shade Structures & Transit Canopies"
        recommended_primary = "Targeted Urban Tree Canopy Expansion + Engineered Shade Canopies"
    else:
        recommended_fast = "High-Albedo Cool Roofs & Solar-Reflective Pavements"
        recommended_primary = "Targeted Urban Tree Canopy Expansion"

    summary = (
        f"Comparative intervention evaluation for {loc_data['name']}: "
        f"Immediate thermal protection is best achieved via '{recommended_fast}' (immediate 5.2°C surface relief), "
        f"while sustainable long-term resilience requires '{recommended_primary}' to counteract the {canopy}% canopy deficit."
    )

    limitations = [
        "Cost estimates are SYNTHETIC benchmark planning ranges and require engineering contractor bidding.",
        "Underground utility conflict surveys (gas, water, fiber-optic) must precede tree root trenching.",
        "Microclimate wind velocity effects on convective cooling are simplified in linear deltas."
    ]

    elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)

    return InterventionComparisonResult(
        execution_time_ms=elapsed_ms,
        location_name=loc_data["name"],
        recommended_primary_intervention=recommended_primary,
        recommended_fast_track_intervention=recommended_fast,
        interventions=options,
        comparison_matrix_summary=summary,
        known_limitations=limitations,
    )
