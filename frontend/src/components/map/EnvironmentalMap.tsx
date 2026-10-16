import React, { useEffect, useMemo } from 'react';
import {
  MapContainer,
  TileLayer,
  Marker,
  Popup,
  useMap,
} from 'react-leaflet';
import L from 'leaflet';
import { Thermometer, Trees, Users, ArrowRight, Layers } from 'lucide-react';
import type { SampleLocationItem } from '../../types/api';

// Create custom SVG markers with color-coded severity rings
function createCustomIcon(temp: number, isSelected: boolean) {
  let color = '#10b981'; // Green (Moderate)
  let ringColor = 'rgba(16, 185, 129, 0.4)';

  if (temp >= 42.0) {
    color = '#f43f5e'; // Rose (Extreme)
    ringColor = 'rgba(244, 63, 94, 0.5)';
  } else if (temp >= 38.0) {
    color = '#f59e0b'; // Amber (Severe)
    ringColor = 'rgba(245, 158, 11, 0.4)';
  } else if (temp >= 33.0) {
    color = '#06b6d4'; // Cyan (High)
    ringColor = 'rgba(6, 182, 212, 0.4)';
  }

  const pulseEffect = isSelected
    ? `<div style="position:absolute; width:44px; height:44px; border-radius:50%; background:${ringColor}; animation: ping 1.5s cubic-bezier(0, 0, 0.2, 1) infinite;"></div>`
    : '';

  const html = `
    <div style="position:relative; display:flex; align-items:center; justify-content:center; width:36px; height:36px;">
      ${pulseEffect}
      <div style="
        width: 32px;
        height: 32px;
        border-radius: 50%;
        background-color: #111620;
        border: 2px solid ${color};
        box-shadow: 0 0 12px ${ringColor};
        display: flex;
        align-items: center;
        justify-content: center;
        color: ${color};
        font-family: monospace;
        font-size: 11px;
        font-weight: 700;
        z-index: 10;
      ">
        ${Math.round(temp)}°
      </div>
    </div>
  `;

  return L.divIcon({
    html,
    className: 'custom-heat-pin',
    iconSize: [36, 36],
    iconAnchor: [18, 18],
    popupAnchor: [0, -20],
  });
}

// Subcomponent to adjust bounds when locations load
const MapBoundsAdjuster: React.FC<{ locations: SampleLocationItem[] }> = ({ locations }) => {
  const map = useMap();

  useEffect(() => {
    if (locations.length === 0) return;
    const bounds = L.latLngBounds(
      locations.map((loc) => [loc.coordinates.lat, loc.coordinates.lng])
    );
    map.fitBounds(bounds, { padding: [50, 50], maxZoom: 14 });
  }, [locations, map]);

  return null;
};

interface EnvironmentalMapProps {
  locations: SampleLocationItem[];
  selectedLocationId?: string | null;
  onSelectLocation?: (loc: SampleLocationItem) => void;
  onPreloadReport?: (loc: SampleLocationItem) => void;
}

export const EnvironmentalMap: React.FC<EnvironmentalMapProps> = ({
  locations,
  selectedLocationId,
  onSelectLocation,
  onPreloadReport,
}) => {
  const defaultCenter: [number, number] = useMemo(() => {
    if (locations.length > 0) {
      return [locations[0].coordinates.lat, locations[0].coordinates.lng];
    }
    return [34.0522, -118.2437]; // Los Angeles default
  }, [locations]);

  return (
    <div className="relative w-full h-[520px] rounded-xl overflow-hidden border border-[#242d3d] bg-[#0d121c] shadow-lg">
      {/* Legend & Provenance Badge Overlay */}
      <div className="absolute top-3 left-3 z-[1000] bg-[#111620]/90 backdrop-blur-md border border-[#242d3d] px-3.5 py-2.5 rounded-lg text-xs space-y-2 pointer-events-auto shadow-md">
        <div className="flex items-center space-x-2 text-slate-200 font-semibold border-b border-[#242d3d]/60 pb-1.5">
          <Layers className="w-3.5 h-3.5 text-cyan-400" />
          <span>Microclimate Heat Risk</span>
        </div>
        <div className="grid grid-cols-2 gap-x-3 gap-y-1 text-[11px] text-slate-400">
          <div className="flex items-center space-x-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-rose-500" />
            <span>Extreme (&ge;42°C)</span>
          </div>
          <div className="flex items-center space-x-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-amber-500" />
            <span>Severe (&ge;38°C)</span>
          </div>
          <div className="flex items-center space-x-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-cyan-500" />
            <span>High (&ge;33°C)</span>
          </div>
          <div className="flex items-center space-x-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-500" />
            <span>Moderate (&lt;33°C)</span>
          </div>
        </div>
        <p className="text-[10px] text-amber-400/90 font-mono pt-1 border-t border-[#242d3d]/40">
          SYNTHETIC_DEV_DATASET_V1
        </p>
      </div>

      <MapContainer
        center={defaultCenter}
        zoom={13}
        scrollWheelZoom={false}
        className="w-full h-full"
      >
        {/* CartoDB Dark Matter Tiles */}
        <TileLayer
          attribution='&copy; <a href="https://carto.com/">CARTO</a>'
          url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
        />

        <MapBoundsAdjuster locations={locations} />

        {locations.map((loc) => {
          const isSelected = loc.id === selectedLocationId;
          const measurements = loc.synthetic_measurements;
          const icon = createCustomIcon(measurements.heat_index_c, isSelected);

          return (
            <Marker
              key={loc.id}
              position={[loc.coordinates.lat, loc.coordinates.lng]}
              icon={icon}
              eventHandlers={{
                click: () => onSelectLocation?.(loc),
              }}
            >
              <Popup className="heatshield-popup">
                <div className="space-y-3 min-w-[240px] text-slate-200">
                  <div>
                    <h4 className="font-bold text-sm text-slate-100">{loc.name}</h4>
                    <p className="text-[11px] text-slate-400 mt-0.5">{loc.description}</p>
                  </div>

                  {/* Synthetic Metrics Grid */}
                  <div className="grid grid-cols-3 gap-2 bg-[#111620] p-2 rounded-lg border border-[#242d3d] text-center">
                    <div>
                      <div className="flex items-center justify-center text-rose-400 mb-0.5">
                        <Thermometer className="w-3.5 h-3.5" />
                      </div>
                      <p className="text-[10px] text-slate-400">Heat Index</p>
                      <p className="font-mono text-xs font-bold text-slate-100">
                        {measurements.heat_index_c}°C
                      </p>
                    </div>

                    <div>
                      <div className="flex items-center justify-center text-emerald-400 mb-0.5">
                        <Trees className="w-3.5 h-3.5" />
                      </div>
                      <p className="text-[10px] text-slate-400">Canopy</p>
                      <p className="font-mono text-xs font-bold text-slate-100">
                        {measurements.canopy_coverage_pct}%
                      </p>
                    </div>

                    <div>
                      <div className="flex items-center justify-center text-cyan-400 mb-0.5">
                        <Users className="w-3.5 h-3.5" />
                      </div>
                      <p className="text-[10px] text-slate-400">Transit Stops</p>
                      <p className="font-mono text-xs font-bold text-slate-100">
                        {measurements.transit_stops_count}
                      </p>
                    </div>
                  </div>

                  <div className="text-[11px] text-slate-400 flex items-center justify-between">
                    <span>Unshaded Platforms:</span>
                    <span className="font-mono font-semibold text-amber-400">
                      {measurements.unshaded_waiting_areas} areas
                    </span>
                  </div>

                  {/* Quick Action Button */}
                  {onPreloadReport && (
                    <button
                      onClick={() => onPreloadReport(loc)}
                      className="w-full flex items-center justify-center space-x-1.5 py-1.5 px-3 rounded bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-300 border border-emerald-500/40 text-xs font-medium transition-colors"
                    >
                      <span>Load into Report Form</span>
                      <ArrowRight className="w-3.5 h-3.5" />
                    </button>
                  )}
                </div>
              </Popup>
            </Marker>
          );
        })}
      </MapContainer>
    </div>
  );
};
