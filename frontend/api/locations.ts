const SAMPLE_NEIGHBORHOODS = [
  {
    id: "downtown_transit_hub",
    name: "Downtown Central Transit Plaza",
    coordinates: { lat: 34.0522, lng: -118.2437 },
    description: "Dense commercial core with heavy public transit ridership and high asphalt coverage.",
    is_synthetic: true,
    synthetic_measurements: {
      ambient_temp_c: 37.8,
      surface_temp_c: 49.5,
      heat_index_c: 41.2,
      canopy_coverage_pct: 6.5,
      ndvi_index: 0.12,
      impervious_surface_pct: 88.0,
      transit_stops_count: 8,
      daily_transit_commuters: 14500,
      vulnerable_facilities: [
        { name: "Central Senior Services", type: "senior_center", distance_m: 120 },
        { name: "Downtown Elementary", type: "school", distance_m: 450 }
      ],
      unshaded_waiting_areas: 5
    }
  },
  {
    id: "eastside_industrial",
    name: "Eastside Logistics & Industrial Corridor",
    coordinates: { lat: 34.0205, lng: -118.1985 },
    description: "Extensive low-slope metal roofs, expansive asphalt parking lots, minimal street trees.",
    is_synthetic: true,
    synthetic_measurements: {
      ambient_temp_c: 39.2,
      surface_temp_c: 54.1,
      heat_index_c: 43.0,
      canopy_coverage_pct: 3.2,
      ndvi_index: 0.08,
      impervious_surface_pct: 94.0,
      transit_stops_count: 3,
      daily_transit_commuters: 3200,
      vulnerable_facilities: [],
      unshaded_waiting_areas: 3
    }
  },
  {
    id: "riverside_parkway",
    name: "Riverside Parkway Residential District",
    coordinates: { lat: 34.0836, lng: -118.2711 },
    description: "Mature urban canopy alongside riparian buffer, single-family and mid-rise residential.",
    is_synthetic: true,
    synthetic_measurements: {
      ambient_temp_c: 31.4,
      surface_temp_c: 35.2,
      heat_index_c: 32.5,
      canopy_coverage_pct: 34.8,
      ndvi_index: 0.48,
      impervious_surface_pct: 42.0,
      transit_stops_count: 4,
      daily_transit_commuters: 1800,
      vulnerable_facilities: [
        { name: "Riverside Community Clinic", type: "clinic", distance_m: 300 }
      ],
      unshaded_waiting_areas: 1
    }
  },
  {
    id: "southside_market_district",
    name: "Southside Open Market & Pedestrian Zone",
    coordinates: { lat: 34.0118, lng: -118.2581 },
    description: "High foot-traffic street market with unshaded vendors and crowded bus lines.",
    is_synthetic: true,
    synthetic_measurements: {
      ambient_temp_c: 36.5,
      surface_temp_c: 46.8,
      heat_index_c: 39.8,
      canopy_coverage_pct: 8.0,
      ndvi_index: 0.15,
      impervious_surface_pct: 82.0,
      transit_stops_count: 6,
      daily_transit_commuters: 9800,
      vulnerable_facilities: [
        { name: "Southside Health Center", type: "health_center", distance_m: 250 },
        { name: "Hope Daycare Center", type: "daycare", distance_m: 180 }
      ],
      unshaded_waiting_areas: 4
    }
  }
];

export default function handler(req: any, res: any) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Accept');

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  return res.status(200).json({
    total: SAMPLE_NEIGHBORHOODS.length,
    locations: SAMPLE_NEIGHBORHOODS,
    is_synthetic_dataset: true,
    dataset_disclaimer: "DEMONSTRATION ONLY: All metrics (temperature, NDVI, exposure indices) are synthetic benchmark samples and must not be used for real municipal life-safety planning.",
  });
}
