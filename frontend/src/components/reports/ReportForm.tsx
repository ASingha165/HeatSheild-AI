import React, { useState } from 'react';
import { Send, RotateCcw, Sparkles, Sliders, AlertCircle, Loader2 } from 'lucide-react';
import type { SampleLocationItem } from '../../types/api';

export interface SampleScenario {
  id: string;
  title: string;
  location: string;
  report: string;
  threshold?: number;
  expectedBehavior: string;
}

export const SAMPLE_SCENARIOS: SampleScenario[] = [
  {
    id: 'downtown-exposure',
    title: 'Downtown Commuter & Senior Heat Alert',
    location: 'Downtown Central Transit Plaza',
    report:
      'The downtown transit plaza has recorded severe 38°C afternoon temperatures, extremely low tree canopy, and large crowds of senior commuters waiting at unshaded bus shelters.',
    threshold: 0.60,
    expectedBehavior: 'High commuter density & vulnerable facilities -> routes to CHECK_EXPOSURE or ANALYZE_HEAT',
  },
  {
    id: 'industrial-canopy',
    title: 'Eastside Industrial Asphalt Desert',
    location: 'Eastside Logistics & Industrial Corridor',
    report:
      'Expansive unshaded asphalt lots with surface temperatures exceeding 54°C and a critical canopy deficit under 4%. We need an analysis of vegetation loss and cooling potential.',
    threshold: 0.60,
    expectedBehavior: 'Severe canopy deficit -> routes to CHECK_VEGETATION',
  },
  {
    id: 'vague-sparse-report',
    title: 'Sparse / Ambiguous Citizen Report',
    location: 'Unspecified Urban Neighborhood',
    report:
      'It felt uncomfortably hot outside yesterday in the afternoon and there are hardly any trees around.',
    threshold: 0.65,
    expectedBehavior: 'Lacks quantitative telemetry -> routes to REQUEST_MORE_DATA or triggers confidence gate',
  },
  {
    id: 'cooling-interventions',
    title: 'Cooling Mitigation Planning',
    location: 'Southside Open Market & Pedestrian Zone',
    report:
      'Evaluating rapid cooling interventions for unshaded market pedestrian corridors. We need to compare engineered transit canopies, high-albedo cool roofs, and street trees.',
    threshold: 0.60,
    expectedBehavior: 'Action comparison requested -> routes to COMPARE_INTERVENTIONS',
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
      ? `High heat stress observed at ${preloadedLocation.name}. Low tree canopy (${preloadedLocation.synthetic_measurements.canopy_coverage_pct}%) and ${preloadedLocation.synthetic_measurements.unshaded_waiting_areas} unshaded waiting areas.`
      : ''
  );
  const [location, setLocation] = useState<string>(preloadedLocation?.name || '');
  const [threshold, setThreshold] = useState<number>(0.60);
  const [showAdvanced, setShowAdvanced] = useState<boolean>(false);
  const [validationError, setValidationError] = useState<string | null>(null);

  // Sync if preloadedLocation changes
  React.useEffect(() => {
    if (preloadedLocation) {
      setLocation(preloadedLocation.name);
      setReport(
        `High heat stress observed at ${preloadedLocation.name}. Low tree canopy (${preloadedLocation.synthetic_measurements.canopy_coverage_pct}%) and ${preloadedLocation.synthetic_measurements.unshaded_waiting_areas} unshaded transit platforms.`
      );
    }
  }, [preloadedLocation]);

  const handleScenarioSelect = (scenario: SampleScenario) => {
    setReport(scenario.report);
    setLocation(scenario.location);
    if (scenario.threshold !== undefined) {
      setThreshold(scenario.threshold);
    }
    setValidationError(null);
  };

  const handleReset = () => {
    setReport('');
    setLocation('');
    setThreshold(0.60);
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

  return (
    <div className="bg-[#161c28] border border-[#242d3d] rounded-xl p-5 shadow-sm space-y-5">
      <div className="flex items-center justify-between border-b border-[#242d3d]/60 pb-3">
        <div>
          <h3 className="text-base font-bold text-slate-100 flex items-center space-x-2">
            <span>Environmental Report Submission</span>
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">
            Submit urban heat observations for Strands Decider 2B routing and Bedrock reasoning.
          </p>
        </div>
        <button
          type="button"
          onClick={() => setShowAdvanced(!showAdvanced)}
          className={`px-3 py-1.5 rounded-lg border text-xs font-medium flex items-center space-x-1.5 transition-colors ${
            showAdvanced
              ? 'bg-cyan-500/20 text-cyan-300 border-cyan-500/40'
              : 'bg-[#111620] text-slate-400 border-[#242d3d] hover:text-slate-200'
          }`}
        >
          <Sliders className="w-3.5 h-3.5" />
          <span>Confidence Gate ({Math.round(threshold * 100)}%)</span>
        </button>
      </div>

      {/* Preset Example Scenarios */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <label className="text-xs font-semibold text-slate-300 flex items-center space-x-1.5">
            <Sparkles className="w-3.5 h-3.5 text-cyan-400" />
            <span>Preset Scenarios (1-Click Load)</span>
          </label>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2">
          {SAMPLE_SCENARIOS.map((sc) => (
            <button
              key={sc.id}
              type="button"
              onClick={() => handleScenarioSelect(sc)}
              className="text-left p-2.5 rounded-lg bg-[#111620] border border-[#242d3d] hover:border-cyan-500/40 hover:bg-[#1a2130] transition-all group flex flex-col justify-between"
            >
              <div>
                <p className="text-xs font-semibold text-slate-200 group-hover:text-cyan-300 transition-colors">
                  {sc.title}
                </p>
                <p className="text-[11px] text-slate-400 line-clamp-2 mt-1">{sc.report}</p>
              </div>
              <p className="text-[10px] text-emerald-400/90 font-mono mt-2 pt-1 border-t border-[#242d3d]/50">
                {sc.expectedBehavior}
              </p>
            </button>
          ))}
        </div>
      </div>

      {/* Main Submission Form */}
      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Optional Location Input */}
        <div>
          <label htmlFor="report-location-input" className="block text-xs font-medium text-slate-300 mb-1.5">
            Target Location / Municipal Zone (Optional)
          </label>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            <select
              id="report-location-select"
              aria-label="Preset location"
              value={locations.some((l) => l.name === location) ? location : ''}
              onChange={(e) => setLocation(e.target.value)}
              className="bg-[#111620] border border-[#242d3d] rounded-lg px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-cyan-500/50"
            >
              <option value="">Select a monitored sample zone...</option>
              {locations.map((loc) => (
                <option key={loc.id} value={loc.name}>
                  {loc.name} ({loc.synthetic_measurements.heat_index_c}°C heat index)
                </option>
              ))}
            </select>
            <input
              id="report-location-input"
              type="text"
              placeholder="Or enter custom zone (e.g. 5th & Main St)"
              value={location}
              onChange={(e) => setLocation(e.target.value)}
              className="bg-[#111620] border border-[#242d3d] rounded-lg px-3 py-2 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-500/50"
            />
          </div>
        </div>

        {/* Environmental Report Textarea */}
        <div>
          <label htmlFor="report-text-area" className="block text-xs font-medium text-slate-300 mb-1.5">
            Environmental Report Narrative <span className="text-rose-400">*</span>
          </label>
          <textarea
            id="report-text-area"
            rows={3}
            value={report}
            onChange={(e) => {
              setReport(e.target.value);
              if (validationError) setValidationError(null);
            }}
            placeholder="Describe temperature observations, unshaded transit stops, tree canopy deficits, or proposed cooling interventions..."
            className="w-full bg-[#111620] border border-[#242d3d] rounded-lg p-3 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-cyan-500/60 font-sans leading-relaxed resize-y"
          />
          <div className="flex justify-between items-center mt-1 text-[11px] text-slate-400">
            <span>Minimum 5 characters required for structured extraction.</span>
            <span className="font-mono">{report.length} chars</span>
          </div>
        </div>

        {/* Advanced Slider: Confidence Threshold */}
        {showAdvanced && (
          <div className="p-3.5 rounded-lg bg-[#111620] border border-cyan-500/30 space-y-2">
            <div className="flex justify-between items-center text-xs">
              <span className="font-semibold text-cyan-300">
                Strands Decider 2B Confidence Safety Threshold
              </span>
              <span className="font-mono text-cyan-400 font-bold">
                {Math.round(threshold * 100)}% ({threshold.toFixed(2)})
              </span>
            </div>
            <input
              type="range"
              min="0.0"
              max="1.0"
              step="0.05"
              value={threshold}
              onChange={(e) => setThreshold(parseFloat(e.target.value))}
              className="w-full accent-cyan-400 cursor-pointer"
            />
            <p className="text-[11px] text-slate-400 leading-snug">
              Decisions with confidence below this threshold are held at the safety gate (
              <code className="text-amber-300 font-mono">REQUEST_HUMAN_CLARIFICATION</code>) to prevent
              unauthorized automated tool execution under ambiguous conditions.
            </p>
          </div>
        )}

        {/* Validation Error Banner */}
        {validationError && (
          <div className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/30 flex items-center space-x-2 text-rose-300 text-xs">
            <AlertCircle className="w-4 h-4 shrink-0 text-rose-400" />
            <span>{validationError}</span>
          </div>
        )}

        {/* Buttons */}
        <div className="flex items-center justify-between pt-2">
          <button
            type="button"
            onClick={handleReset}
            disabled={isSubmitting || (!report && !location)}
            className="px-4 py-2 rounded-lg bg-[#111620] border border-[#242d3d] text-slate-400 hover:text-slate-200 text-xs font-medium flex items-center space-x-1.5 transition-colors disabled:opacity-40"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>Reset Form</span>
          </button>

          <button
            type="submit"
            disabled={isSubmitting || report.trim().length < 5}
            className="px-6 py-2.5 rounded-lg bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-semibold text-xs flex items-center space-x-2 transition-all shadow-md hover:shadow-emerald-500/20 disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
          >
            {isSubmitting ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin text-slate-950" />
                <span>Running Strands Decider 2B...</span>
              </>
            ) : (
              <>
                <Send className="w-4 h-4 text-slate-950" />
                <span>Run Decision Agent</span>
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
};
