import React, { useEffect, useMemo, useState } from 'react';
import {
  MapContainer,
  TileLayer,
  Marker,
  Popup,
  useMap,
} from 'react-leaflet';
import L from 'leaflet';
import {
  Thermometer,
  Trees,
  Users,
  ArrowRight,
} from 'lucide-react';
import type { SampleLocationItem } from '../../types/api';

// Create custom SVG markers matching Stitch tactical pin style
function createCustomIcon(temp: number, isSelected: boolean) {
  let color = '#4edea3'; // Primary Green (Nominal)
  let ringColor = 'rgba(78, 222, 163, 0.4)';

  if (temp >= 42.0) {
    color = '#ffb4ab'; // Error Crimson (Extreme)
    ringColor = 'rgba(255, 180, 171, 0.6)';
  } else if (temp >= 38.0) {
    color = '#ffb95f'; // Tertiary Amber (Warning)
    ringColor = 'rgba(255, 185, 95, 0.5)';
  } else if (temp >= 33.0) {
    color = '#4cd7f6'; // Secondary Cyan (Elevated)
    ringColor = 'rgba(76, 215, 246, 0.4)';
  }

  const pulseEffect = isSelected
    ? `<div style="position:absolute; width:44px; height:44px; border-radius:50%; background:${ringColor}; animation: ping 1.5s cubic-bezier(0, 0, 0.2, 1) infinite;"></div>`
    : '';

  const html = `
    <div style="position:relative; display:flex; align-items:center; justify-content:center; width:40px; height:40px; cursor:pointer;">
      ${pulseEffect}
      <div style="
        width: 34px;
        height: 34px;
        border-radius: 50%;
        background-color: #0e141b;
        border: 2px solid ${color};
        box-shadow: 0 0 14px ${ringColor};
        display: flex;
        align-items: center;
        justify-content: center;
        color: ${color};
        font-family: 'JetBrains Mono', monospace;
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
    iconSize: [40, 40],
    iconAnchor: [20, 20],
    popupAnchor: [0, -22],
  });
}

// Adjust bounds & handle map invalidation on resize
const MapBoundsAdjuster: React.FC<{ locations: SampleLocationItem[] }> = ({ locations }) => {
  const map = useMap();

  useEffect(() => {
    if (locations.length === 0) return;
    const bounds = L.latLngBounds(
      locations.map((loc) => [loc.coordinates.lat, loc.coordinates.lng])
    );
    map.fitBounds(bounds, { padding: [40, 40], maxZoom: 14 });

    // Ensure map tiles recalculate size on mount and window resize
    const handleResize = () => {
      map.invalidateSize();
    };
    window.addEventListener('resize', handleResize);
    const timer = setTimeout(() => {
      map.invalidateSize();
    }, 250);

    return () => {
      window.removeEventListener('resize', handleResize);
      clearTimeout(timer);
    };
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
  const [activeLayer, setActiveLayer] = useState<'heat' | 'canopy' | 'transit'>('heat');

  const defaultCenter: [number, number] = useMemo(() => {
    if (locations.length > 0) {
      return [locations[0].coordinates.lat, locations[0].coordinates.lng];
    }
    return [34.0522, -118.2437];
  }, [locations]);

  const selectedLoc = locations.find((l) => l.id === selectedLocationId) || locations[0];

  const currentLat = selectedLoc ? selectedLoc.coordinates.lat.toFixed(4) : '34.0522';
  const currentLng = selectedLoc ? Math.abs(selectedLoc.coordinates.lng).toFixed(4) : '118.2437';

  return (
    <div className="bg-surface-container-low/90 backdrop-blur-md rounded-xl p-4 sm:p-5 border border-outline-variant/30 shadow-lg flex flex-col space-y-4">
      {/* Leaflet Workspace Header & Layer Controls */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 pb-3 border-b border-outline-variant/20">
        <div className="flex items-center gap-2.5">
          <span className="material-symbols-outlined text-secondary text-[22px]">satellite_alt</span>
          <div className="flex flex-col min-w-0">
            <h2 className="font-headline-sm text-on-surface font-bold text-base sm:text-lg">
              Spatial Telemetry Heat Canvas
            </h2>
            <span className="font-label-mono-sm text-outline truncate">
              Lat: {currentLat}° N | Lon: {currentLng}° W | Los Angeles Metro (EPSG:3857)
            </span>
          </div>
        </div>

        {/* Tactical Layer Controls */}
        <div className="flex flex-wrap items-center gap-2 shrink-0">
          <button
            type="button"
            onClick={() => setActiveLayer('heat')}
            className={`px-2.5 py-1 rounded font-label-mono-sm flex items-center gap-1.5 transition-colors cursor-pointer ${
              activeLayer === 'heat'
                ? 'bg-surface-container-high text-primary border border-primary/40 font-bold'
                : 'bg-surface-container text-on-surface-variant hover:text-on-surface border border-outline-variant/30'
            }`}
          >
            <Thermometer className="w-3.5 h-3.5" />
            <span>Heat Index</span>
          </button>
          <button
            type="button"
            onClick={() => setActiveLayer('canopy')}
            className={`px-2.5 py-1 rounded font-label-mono-sm flex items-center gap-1.5 transition-colors cursor-pointer ${
              activeLayer === 'canopy'
                ? 'bg-surface-container-high text-primary border border-primary/40 font-bold'
                : 'bg-surface-container text-on-surface-variant hover:text-on-surface border border-outline-variant/30'
            }`}
          >
            <Trees className="w-3.5 h-3.5" />
            <span>Canopy</span>
          </button>
          <button
            type="button"
            onClick={() => setActiveLayer('transit')}
            className={`px-2.5 py-1 rounded font-label-mono-sm flex items-center gap-1.5 transition-colors cursor-pointer ${
              activeLayer === 'transit'
                ? 'bg-surface-container-high text-primary border border-primary/40 font-bold'
                : 'bg-surface-container text-on-surface-variant hover:text-on-surface border border-outline-variant/30'
            }`}
          >
            <Users className="w-3.5 h-3.5" />
            <span>Demographics</span>
          </button>
        </div>
      </div>

      {/* Map Container - Responsive height */}
      <div className="relative w-full h-[360px] sm:h-[420px] lg:h-[480px] rounded-xl overflow-hidden border border-outline-variant/30 bg-surface-container-lowest shadow-inner">
        <MapContainer
          center={defaultCenter}
          zoom={13}
          scrollWheelZoom={false}
          className="w-full h-full"
        >
          {/* Supported Dark Tile Provider: Esri World Dark Gray Canvas (No API Key Required, No Watermarks) */}
          <TileLayer
            attribution='&copy; <a href="https://www.esri.com/">Esri</a>, HERE, Garmin, &copy; OpenStreetMap contributors'
            url="https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}"
            maxZoom={16}
            eventHandlers={{
              tileerror: (error) => {
                console.warn('Basemap tile load warning:', error);
              },
            }}
          />

          {/* Reference Labels Overlay */}
          <TileLayer
            url="https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Reference/MapServer/tile/{z}/{y}/{x}"
            maxZoom={16}
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
                  <div className="space-y-3 min-w-[240px] text-on-surface">
                    <div>
                      <div className="flex items-center justify-between gap-2">
                        <h4 className="font-bold text-sm text-on-surface font-headline-sm">
                          {loc.name}
                        </h4>
                        <span className="font-label-mono-sm text-[10px] px-1.5 py-0.5 rounded bg-tertiary/15 text-tertiary border border-tertiary/30 shrink-0">
                          Synthetic
                        </span>
                      </div>
                      <p className="text-[11px] text-on-surface-variant mt-0.5">{loc.description}</p>
                    </div>

                    {/* Synthetic Metrics Grid */}
                    <div className="grid grid-cols-3 gap-2 bg-surface-container p-2 rounded-lg border border-outline-variant/30 text-center">
                      <div>
                        <div className="flex items-center justify-center text-error mb-0.5">
                          <Thermometer className="w-3.5 h-3.5" />
                        </div>
                        <p className="text-[10px] text-outline">Heat Index</p>
                        <p className="font-mono text-xs font-bold text-on-surface">
                          {measurements.heat_index_c}°C
                        </p>
                      </div>

                      <div>
                        <div className="flex items-center justify-center text-primary mb-0.5">
                          <Trees className="w-3.5 h-3.5" />
                        </div>
                        <p className="text-[10px] text-outline">Canopy</p>
                        <p className="font-mono text-xs font-bold text-on-surface">
                          {measurements.canopy_coverage_pct}%
                        </p>
                      </div>

                      <div>
                        <div className="flex items-center justify-center text-secondary mb-0.5">
                          <Users className="w-3.5 h-3.5" />
                        </div>
                        <p className="text-[10px] text-outline">Transit</p>
                        <p className="font-mono text-xs font-bold text-on-surface">
                          {measurements.transit_stops_count} stops
                        </p>
                      </div>
                    </div>

                    <div className="text-[11px] text-on-surface-variant flex items-center justify-between">
                      <span>Unshaded Waiting:</span>
                      <span className="font-mono font-semibold text-tertiary">
                        {measurements.unshaded_waiting_areas} areas
                      </span>
                    </div>

                    {onPreloadReport && (
                      <button
                        type="button"
                        onClick={() => onPreloadReport(loc)}
                        className="w-full flex items-center justify-center gap-1.5 py-1.5 px-3 rounded bg-primary/20 hover:bg-primary/30 text-primary border border-primary/40 text-xs font-medium transition-colors cursor-pointer"
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

        {/* Map Legend Bar (Bottom Left) */}
        <div className="absolute bottom-3 left-3 z-[1000] p-2.5 rounded-lg bg-surface-container-lowest/90 backdrop-blur-md border border-outline-variant/40 flex flex-col space-y-1 shadow-md pointer-events-auto max-w-[calc(100%-24px)]">
          <div className="flex justify-between text-[10px] font-label-mono-sm text-outline gap-3">
            <span>30°C (Nominal)</span>
            <span>38°C (Warning)</span>
            <span>46°C (Extreme)</span>
          </div>
          <div className="w-48 sm:w-52 h-2 rounded-full bg-gradient-to-r from-primary via-tertiary to-error"></div>
        </div>
      </div>

      {/* Map Location Details / Active Inspector Panel */}
      {selectedLoc && (
        <div className="p-3.5 rounded-lg bg-surface-container-high/60 border border-outline-variant/30 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-start sm:items-center gap-3">
            <span className="material-symbols-outlined text-secondary text-[22px] shrink-0 mt-0.5 sm:mt-0">radar</span>
            <div>
              <div className="flex flex-wrap items-center gap-2">
                <span className="font-label-mono-sm text-primary font-bold">
                  Active Inspector: {selectedLoc.name}
                </span>
                <span className="font-label-mono-sm text-[10px] px-1.5 py-0.2 rounded bg-tertiary/15 text-tertiary border border-tertiary/30">
                  SYNTHETIC BENCHMARK
                </span>
              </div>
              <div className="font-body-sm text-on-surface-variant mt-0.5 text-xs">
                Heat Index: {selectedLoc.synthetic_measurements.heat_index_c}°C • Canopy:{' '}
                {selectedLoc.synthetic_measurements.canopy_coverage_pct}% • Commuters:{' '}
                {selectedLoc.synthetic_measurements.daily_transit_commuters?.toLocaleString()} • Unshaded Platforms:{' '}
                {selectedLoc.synthetic_measurements.unshaded_waiting_areas}
              </div>
            </div>
          </div>
          {onPreloadReport && (
            <button
              type="button"
              onClick={() => onPreloadReport(selectedLoc)}
              className="px-3.5 py-1.5 rounded-lg bg-primary text-on-primary font-label-mono-sm font-bold uppercase tracking-wide hover:shadow-primary/30 shadow transition cursor-pointer self-start sm:self-auto shrink-0"
            >
              Load into Form &rarr;
            </button>
          )}
        </div>
      )}
    </div>
  );
};
