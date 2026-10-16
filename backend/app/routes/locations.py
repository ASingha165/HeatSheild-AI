"""
Locations endpoint providing sample urban monitoring zones for the interactive map.
"""

from __future__ import annotations

from fastapi import APIRouter

from backend.app.schemas import LocationsResponse, SampleLocationItem
from backend.data.sample_dataset import DATASET_METADATA, SAMPLE_NEIGHBORHOODS

router = APIRouter(tags=["Locations"])


@router.get("/locations", response_model=LocationsResponse)
def get_sample_locations() -> LocationsResponse:
    """
    Returns pre-configured sample urban neighborhoods for Leaflet map visualization.
    Explicitly tags all metrics with synthetic data provenance.
    """
    items = []
    for loc_id, data in SAMPLE_NEIGHBORHOODS.items():
        items.append(
            SampleLocationItem(
                id=data["id"],
                name=data["name"],
                coordinates=data["coordinates"],
                description=data["description"],
                is_synthetic=True,
                synthetic_measurements=data["synthetic_measurements"],
            )
        )

    return LocationsResponse(
        total=len(items),
        locations=items,
        is_synthetic_dataset=True,
        dataset_disclaimer=DATASET_METADATA["disclaimer"],
    )
