"""
Synthetic Sample Dataset for Urban Heat Risk Development.

NOTICE: All values in this file are simulated synthetic observations created
strictly for development, demonstration, and testing purposes. They do NOT represent
actual measured environmental telemetry or physical sensor readings.
"""

from typing import Any, Dict, List

DATASET_METADATA: Dict[str, Any] = {
    "is_synthetic": True,
    "dataset_label": "SYNTHETIC_DEV_DATASET_V1",
    "disclaimer": (
        "DEMONSTRATION ONLY: All metrics (temperature, NDVI, exposure indices) "
        "are synthetic benchmark samples and must not be used for real municipal life-safety planning."
    ),
    "version": "1.0.0",
}

# Pre-defined sample urban neighborhoods for testing and demonstration
SAMPLE_NEIGHBORHOODS: Dict[str, Dict[str, Any]] = {
    "downtown_transit_hub": {
        "id": "downtown_transit_hub",
        "name": "Downtown Central Transit Plaza",
        "coordinates": {"lat": 34.0522, "lng": -118.2437},
        "description": "Dense commercial core with heavy public transit ridership and high asphalt coverage.",
        "synthetic_measurements": {
            "ambient_temp_c": 37.8,
            "surface_temp_c": 49.5,
            "heat_index_c": 41.2,
            "canopy_coverage_pct": 6.5,
            "ndvi_index": 0.12,
            "impervious_surface_pct": 88.0,
            "transit_stops_count": 8,
            "daily_transit_commuters": 14500,
            "vulnerable_facilities": [
                {"name": "Central Senior Services", "type": "senior_center", "distance_m": 120},
                {"name": "Downtown Elementary", "type": "school", "distance_m": 450}
            ],
            "unshaded_waiting_areas": 5
        }
    },
    "eastside_industrial": {
        "id": "eastside_industrial",
        "name": "Eastside Logistics & Industrial Corridor",
        "coordinates": {"lat": 34.0205, "lng": -118.1985},
        "description": "Extensive low-slope metal roofs, expansive asphalt parking lots, minimal street trees.",
        "synthetic_measurements": {
            "ambient_temp_c": 39.2,
            "surface_temp_c": 54.1,
            "heat_index_c": 43.0,
            "canopy_coverage_pct": 3.2,
            "ndvi_index": 0.08,
            "impervious_surface_pct": 94.0,
            "transit_stops_count": 3,
            "daily_transit_commuters": 3200,
            "vulnerable_facilities": [],
            "unshaded_waiting_areas": 3
        }
    },
    "riverside_parkway": {
        "id": "riverside_parkway",
        "name": "Riverside Parkway Residential District",
        "coordinates": {"lat": 34.0836, "lng": -118.2711},
        "description": "Mature urban canopy alongside riparian buffer, single-family and mid-rise residential.",
        "synthetic_measurements": {
            "ambient_temp_c": 31.4,
            "surface_temp_c": 35.2,
            "heat_index_c": 32.5,
            "canopy_coverage_pct": 34.8,
            "ndvi_index": 0.48,
            "impervious_surface_pct": 42.0,
            "transit_stops_count": 4,
            "daily_transit_commuters": 1800,
            "vulnerable_facilities": [
                {"name": "Riverside Community Clinic", "type": "clinic", "distance_m": 300}
            ],
            "unshaded_waiting_areas": 1
        }
    },
    "southside_market_district": {
        "id": "southside_market_district",
        "name": "Southside Open Market & Pedestrian Zone",
        "coordinates": {"lat": 34.0118, "lng": -118.2581},
        "description": "High foot-traffic street market with unshaded vendors and crowded bus lines.",
        "synthetic_measurements": {
            "ambient_temp_c": 36.5,
            "surface_temp_c": 46.8,
            "heat_index_c": 39.8,
            "canopy_coverage_pct": 8.0,
            "ndvi_index": 0.15,
            "impervious_surface_pct": 82.0,
            "transit_stops_count": 6,
            "daily_transit_commuters": 9800,
            "vulnerable_facilities": [
                {"name": "Southside Health Center", "type": "health_center", "distance_m": 250},
                {"name": "Hope Daycare Center", "type": "daycare", "distance_m": 180}
            ],
            "unshaded_waiting_areas": 4
        }
    }
}


def lookup_sample_location(query: str) -> Dict[str, Any]:
    """Finds the closest matching sample location or provides a generic synthetic profile."""
    q = query.lower()
    for key, data in SAMPLE_NEIGHBORHOODS.items():
        if key in q or data["name"].lower() in q or any(term in q for term in key.split("_")):
            return data
    # Generic fallback synthetic profile
    return {
        "id": "generic_urban_sample",
        "name": query if query else "Unspecified Urban Zone",
        "coordinates": {"lat": 34.0500, "lng": -118.2500},
        "description": "Generic urban mixed-use synthetic profile.",
        "synthetic_measurements": {
            "ambient_temp_c": 35.0,
            "surface_temp_c": 44.0,
            "heat_index_c": 38.0,
            "canopy_coverage_pct": 12.0,
            "ndvi_index": 0.20,
            "impervious_surface_pct": 75.0,
            "transit_stops_count": 4,
            "daily_transit_commuters": 5000,
            "vulnerable_facilities": [],
            "unshaded_waiting_areas": 2
        }
    }
