import React, { useState, useEffect } from 'react';
import {
  Sparkles,
  Sliders,
  Loader2,
  AlertCircle,
  Flame,
  GraduationCap,
  Factory,
  Trees,
} from 'lucide-react';
import type { SampleLocationItem } from '../../types/api';

export interface SampleScenario {
  id: string;
  title: string;
  location: string;
  report: string;
  threshold?: number;
  expectedBehavior: string;
  iconName: 'flame' | 'school' | 'factory' | 'park';
}

export const SAMPLE_SCENARIOS: SampleScenario[] = [
  {
    id: 'downtown-exposure',
    title: 'Downtown Heat Island Surge',
    location: 'Downtown Central Transit Plaza',
    report:
      'URGENT: Ambient temp reaching 42.1°C with 65% humidity in Sector 7C (Downtown Core). High concentration of elderly residents and unshaded bus transit corridors. Canopy cover measured at 8.2%. Requesting immediate mitigation priority analysis.',
    threshold: 0.60,
    expectedBehavior: 'High commuter density & vulnerable facilities -> routes to CHECK_EXPOSURE or ANALYZE_HEAT',
    iconName: 'flame',
  },
  {
    id: 'industrial-canopy',
    title: 'Industrial Corridor Inversion',
    location: 'Eastside Logistics & Industrial Corridor',
    report:
      'WARNING: Industrial Corridor Thermal Inversion. Expansive unshaded asphalt lots with surface temperatures exceeding 54°C and a critical canopy deficit under 4%. We need an analysis of vegetation loss and cooling potential.',
    threshold: 0.60,
    expectedBehavior: 'Severe canopy deficit -> routes to CHECK_VEGETATION',
    iconName: 'factory',
  },
  {
    id: 'vague-sparse-report',
    title: 'Low Vegetation District',
    location: 'Riverside Parkway Residential District',
    report:
      'ADVISORY: Low Vegetation District quadrant 4 displaying prolonged heat retention. Tree canopy deficit estimated at 88%. Residential night-cooling failure predicted.',
    threshold: 0.65,
    expectedBehavior: 'Vegetation analysis vs clarification gate',
    iconName: 'park',
  },
  {
    id: 'cooling-interventions',
    title: 'Eastside School District Alert',
    location: 'Southside Open Market & Pedestrian Zone',
    report:
      'ALERT: Eastside School District thermal index exceeding 39.4°C during recess discharge. 3 playgrounds with asphalt surfacing recording 48°C ground radiometry. Evaluating rapid cooling interventions: shaded canopies vs cool pavements.',
    threshold: 0.60,
    expectedBehavior: 'Intervention comparison requested -> routes to COMPARE_INTERVENTIONS',
    iconName: 'school',
  },
];

interface ReportFormProps {
  locations: SampleLocationItem[];
  onSubmit: (report: string, location: string | null, threshold: number | null) => void;
  isSubmitting: boolean;
  preloadedLocation?: SampleLocationItem | null;
}

export const ReportForm: React.FC<ReportFormProps> = ({
  locations,
  onSubmit,
  isSubmitting,
  preloadedLocation,
}) => {
  const [report, setReport] = useState<string>(
    preloadedLocation
      ? `High heat stress observed at ${preloadedLocation.name}. Low tree canopy (${preloadedLocation.synthetic_measurements.canopy_coverage_pct}%) and ${preloadedLocation.synthetic_measurements.unshaded_waiting_areas} unshaded transit platforms.`
      : SAMPLE_SCENARIOS[0].report
  );
  const [location, setLocation] = useState<string>(
    preloadedLocation?.name || SAMPLE_SCENARIOS[0].location
  );
  const [threshold, setThreshold] = useState<number>(0.60);
  const [showAdvanced, setShowAdvanced] = useState<boolean>(false);
  const [activeScenarioId, setActiveScenarioId] = useState<string>(SAMPLE_SCENARIOS[0].id);
  const [validationError, setValidationError] = useState<string | null>(null);

  useEffect(() => {
    if (preloadedLocation) {
      setLocation(preloadedLocation.name);
      setReport(
        `High heat stress observed at ${preloadedLocation.name}. Low tree canopy (${preloadedLocation.synthetic_measurements.canopy_coverage_pct}%) and ${preloadedLocation.synthetic_measurements.unshaded_waiting_areas} unshaded transit platforms.`
      );
      setActiveScenarioId('');
    }
  }, [preloadedLocation]);

  const handleScenarioSelect = (scenario: SampleScenario) => {
    setReport(scenario.report);
    setLocation(scenario.location);
    setActiveScenarioId(scenario.id);
    if (scenario.threshold !== undefined) {
      setThreshold(scenario.threshold);
    }
    setValidationError(null);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const cleanReport = report.trim();
    if (cleanReport.length < 5) {
      setValidationError('Environmental report must contain at least 5 characters.');
      return;
    }
    setValidationError(null);
    onSubmit(cleanReport, location.trim() || null, threshold);
  };

  const getScenarioIcon = (icon: string) => {
    switch (icon) {
      case 'flame':
        return <Flame className="w-3.5 h-3.5" />;
      case 'school':
        return <GraduationCap className="w-3.5 h-3.5" />;
      case 'factory':
        return <Factory className="w-3.5 h-3.5" />;
      case 'park':
        return <Trees className="w-3.5 h-3.5" />;
      default:
        return <Sparkles className="w-3.5 h-3.5" />;
    }
  };

  return (
    <div className="bg-surface-container-low/90 backdrop-blur-md rounded-xl p-5 border border-outline-variant/30 shadow-lg flex flex-col space-y-4">
      {/* Module Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-outline-variant/20">
        <div className="flex items-center gap-2">
          <span className="material-symbols-outlined text-primary text-[20px]">terminal</span>
          <h2 className="font-headline-sm text-on-surface font-bold">
            Incident / Environmental Report Intake
          </h2>
        </div>
        <span className="font-label-mono-sm px-2.5 py-1 rounded bg-surface-container-high text-secondary border border-outline-variant/20 self-start sm:self-auto">
          FastAPI: POST /api/reports/analyze
        </span>
      </div>

      {/* Quick Scenario Presets */}
      <div className="flex flex-col space-y-1.5">
        <span className="font-label-mono-sm uppercase text-outline">Scenario Presets</span>
        <div className="flex flex-wrap gap-2">
          {SAMPLE_SCENARIOS.map((sc) => {
            const isSelected = activeScenarioId === sc.id;
            return (
              <button
                key={sc.id}
                type="button"
                onClick={() => handleScenarioSelect(sc)}
                className={`px-3 py-1.5 rounded-lg font-label-mono-sm flex items-center gap-1.5 transition-all cursor-pointer ${
                  isSelected
                    ? 'bg-primary text-on-primary font-bold shadow-[0_0_12px_rgba(78,222,163,0.3)]'
                    : 'bg-surface-container-high text-on-surface-variant hover:text-primary hover:bg-surface-container-highest border border-outline-variant/30'
                }`}
              >
                {getScenarioIcon(sc.iconName)}
                <span>{sc.title}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Intake Form */}
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          {/* Main Textarea */}
          <div className="md:col-span-2 flex flex-col space-y-1">
            <label htmlFor="report-textarea" className="font-label-mono-sm uppercase text-outline">
              Environmental Field Dispatch Text
            </label>
            <textarea
              id="report-textarea"
              rows={4}
              value={report}
              onChange={(e) => setReport(e.target.value)}
              placeholder="Describe observed thermal stress, vulnerable populations, canopy coverage, or cooling interventions..."
              className="w-full bg-surface-container-lowest text-on-surface font-body-md p-3 rounded-lg border border-outline-variant/30 focus:outline-none focus:ring-1 focus:ring-primary shadow-inner resize-none leading-relaxed"
            />
          </div>

          {/* Right Column: Location & Telemetry Context */}
          <div className="flex flex-col space-y-3 justify-between">
            <div className="flex flex-col space-y-1">
              <label htmlFor="report-location-select" className="font-label-mono-sm uppercase text-outline">
                Geographic Location
              </label>
              <select
                id="report-location-select"
                aria-label="Preset location"
                value={locations.some((l) => l.name === location) ? location : ''}
                onChange={(e) => setLocation(e.target.value)}
                className="w-full bg-surface-container-lowest text-on-surface font-label-mono-sm p-2.5 rounded-lg border border-outline-variant/30 focus:outline-none focus:ring-1 focus:ring-primary"
              >
                <option value="">-- Choose Municipal Zone --</option>
                {locations.map((loc) => (
                  <option key={loc.id} value={loc.name}>
                    {loc.name}
                  </option>
                ))}
              </select>
            </div>

            <div className="flex flex-col space-y-1">
              <label className="font-label-mono-sm uppercase text-outline">Telemetry Context</label>
              <div className="p-2.5 rounded-lg bg-surface-container-lowest text-on-surface-variant font-label-mono-sm leading-relaxed border border-outline-variant/20">
                Peak: 13:00-17:30 UTC<br />
                Albedo: 0.12 (asphalt dominant)<br />
                Confidence Gate: {Math.round(threshold * 100)}%
              </div>
            </div>
          </div>
        </div>

        {/* Confidence Gate Accordion / Advanced Options */}
        {showAdvanced && (
          <div className="p-3.5 rounded-lg bg-surface-container-lowest border border-outline-variant/30 space-y-2">
            <div className="flex items-center justify-between text-xs font-label-mono-sm">
              <span className="text-secondary font-bold">Policy Safety Gate Threshold</span>
              <span className="text-primary font-mono">{Math.round(threshold * 100)}% Confidence Required</span>
            </div>
            <input
              type="range"
              min="0.30"
              max="0.95"
              step="0.05"
              value={threshold}
              onChange={(e) => setThreshold(parseFloat(e.target.value))}
              className="w-full accent-[#4edea3] cursor-pointer"
            />
            <p className="text-[11px] text-on-surface-variant font-label-mono-sm">
              Decisions below this threshold will be held at the safety gate with <code>REQUEST_HUMAN_CLARIFICATION</code>.
            </p>
          </div>
        )}

        {/* Validation Error Message */}
        {validationError && (
          <div className="p-3 rounded-lg bg-error-container/20 border border-error/40 flex items-center gap-2 text-xs text-error font-body-sm">
            <AlertCircle className="w-4 h-4 shrink-0 text-error" />
            <span>{validationError}</span>
          </div>
        )}

        {/* Form Footer Action Strip */}
        <div className="flex flex-col sm:flex-row items-center justify-between gap-3 pt-2 border-t border-outline-variant/20">
          <div className="flex items-center gap-2 text-on-surface-variant font-label-mono-sm">
            <span className="material-symbols-outlined text-primary text-[16px]">verified</span>
            <span>Schema Payload: v2.4 JSON valid</span>
            <button
              type="button"
              onClick={() => setShowAdvanced(!showAdvanced)}
              className="text-secondary hover:underline ml-2 flex items-center gap-1 cursor-pointer"
            >
              <Sliders className="w-3 h-3" />
              <span>{showAdvanced ? 'Hide Gate' : 'Adjust Gate'}</span>
            </button>
          </div>

          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full sm:w-auto px-6 py-2.5 rounded-lg bg-primary text-on-primary font-label-mono-md uppercase tracking-wider flex items-center justify-center gap-2 shadow-lg hover:shadow-primary/30 transition-all cursor-pointer font-bold disabled:opacity-50"
          >
            {isSubmitting ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin text-on-primary" />
                <span>Executing Decider 2B (POST)...</span>
              </>
            ) : (
              <>
                <span className="material-symbols-outlined text-[18px]">psychology</span>
                <span>Run Decider Agent (POST)</span>
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
};
