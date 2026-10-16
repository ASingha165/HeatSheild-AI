import React from 'react';
import {
  Clock,
  Database,
  CheckCircle2,
  AlertCircle,
} from 'lucide-react';
import type { ToolExecutionResponse } from '../../types/api';

interface ToolExecutionPanelProps {
  toolExecution: ToolExecutionResponse;
}

export const ToolExecutionPanel: React.FC<ToolExecutionPanelProps> = ({ toolExecution }) => {
  const isSuccess = toolExecution.status === 'success';
  const out = toolExecution.output || {};

  return (
    <div className="bg-surface-container-low/90 backdrop-blur-md rounded-xl p-5 border border-outline-variant/30 shadow-lg flex flex-col space-y-4">
      {/* Header (Stitch styling) */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-outline-variant/20">
        <div className="flex items-center gap-2">
          <span className="material-symbols-outlined text-primary text-[22px]">data_object</span>
          <h2 className="font-headline-sm text-on-surface font-bold">
            Analytical Tool Execution Payloads
          </h2>
        </div>

        <div className="flex items-center gap-2.5">
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-surface-container text-xs font-mono text-outline">
            <Clock className="w-3 h-3 text-secondary" />
            <span>Runtime: {toolExecution.execution_time_ms.toLocaleString()} ms</span>
          </div>

          <div
            className={`flex items-center gap-1 px-2.5 py-1 rounded text-xs font-label-mono-sm font-bold ${
              isSuccess
                ? 'bg-primary/10 text-primary border border-primary/30'
                : 'bg-error-container/20 text-error border border-error/30'
            }`}
          >
            {isSuccess ? (
              <>
                <CheckCircle2 className="w-3.5 h-3.5 text-primary" />
                <span>SUCCESS</span>
              </>
            ) : (
              <>
                <AlertCircle className="w-3.5 h-3.5 text-error" />
                <span>FAILED</span>
              </>
            )}
          </div>
        </div>
      </div>

      {/* Data Provenance & Synthetic Disclaimer */}
      <div className="p-3 rounded-lg bg-surface-container border border-outline-variant/30 flex items-center justify-between text-xs text-on-surface-variant font-label-mono-sm">
        <div className="flex items-center gap-2">
          <Database className="w-4 h-4 text-tertiary shrink-0" />
          <span>
            <strong className="text-tertiary">Data Provenance:</strong>{' '}
            {out.data_label || 'SYNTHETIC_DEV_DATASET_V1'} &bull;{' '}
            {out.disclaimer || 'Sample measurements'}
          </span>
        </div>
        <span className="font-mono text-outline text-[11px] hidden md:inline">
          Action: {toolExecution.tool_name}
        </span>
      </div>

      {/* Tool 1: ANALYZE_HEAT */}
      {toolExecution.tool_name === 'ANALYZE_HEAT' && (
        <div className="space-y-3">
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div className="p-3.5 rounded-lg bg-surface-container border border-outline-variant/30">
              <span className="font-label-mono-sm text-outline">Ambient Air Temp</span>
              <p className="font-telemetry-value text-error mt-1">
                {out.observed_ambient_temp_c}°C
              </p>
            </div>
            <div className="p-3.5 rounded-lg bg-surface-container border border-outline-variant/30">
              <span className="font-label-mono-sm text-outline">Radiant Surface Temp</span>
              <p className="font-telemetry-value text-tertiary mt-1">
                {out.observed_surface_temp_c}°C
              </p>
            </div>
            <div className="p-3.5 rounded-lg bg-surface-container border border-outline-variant/30">
              <span className="font-label-mono-sm text-outline">Heat Index</span>
              <p className="font-telemetry-value text-error mt-1">
                {out.heat_index_c}°C
              </p>
            </div>
            <div className="p-3.5 rounded-lg bg-surface-container border border-outline-variant/30">
              <span className="font-label-mono-sm text-outline">Thermal Severity</span>
              <p className="font-mono text-sm font-bold text-error mt-2">
                {out.heat_severity_level}
              </p>
            </div>
          </div>

          <div className="p-3.5 rounded-lg bg-surface-container border border-outline-variant/30 space-y-1 font-body-sm text-on-surface-variant">
            <span className="font-bold text-on-surface font-label-mono-sm text-secondary">
              Nocturnal Retention Risk:
            </span>
            <p className="mt-0.5 leading-relaxed">{out.nocturnal_retention_risk}</p>
          </div>
        </div>
      )}

      {/* Tool 2: CHECK_VEGETATION */}
      {toolExecution.tool_name === 'CHECK_VEGETATION' && (
        <div className="space-y-3">
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div className="p-3.5 rounded-lg bg-surface-container border border-outline-variant/30">
              <span className="font-label-mono-sm text-outline">Canopy Coverage</span>
              <p className="font-telemetry-value text-primary mt-1">
                {out.canopy_coverage_pct}%
              </p>
            </div>
            <div className="p-3.5 rounded-lg bg-surface-container border border-outline-variant/30">
              <span className="font-label-mono-sm text-outline">Canopy Deficit (Goal 30%)</span>
              <p className="font-telemetry-value text-tertiary mt-1">
                {out.canopy_deficit_pct}%
              </p>
            </div>
            <div className="p-3.5 rounded-lg bg-surface-container border border-outline-variant/30">
              <span className="font-label-mono-sm text-outline">NDVI Index</span>
              <p className="font-telemetry-value text-secondary mt-1">
                {out.ndvi_index}
              </p>
            </div>
            <div className="p-3.5 rounded-lg bg-surface-container border border-outline-variant/30">
              <span className="font-label-mono-sm text-outline">Cooling Potential</span>
              <p className="font-telemetry-value text-primary mt-1">
                +{out.estimated_cooling_potential_c}°C
              </p>
            </div>
          </div>

          {out.recommended_planting_priorities?.length > 0 && (
            <div className="p-3.5 rounded-lg bg-surface-container border border-outline-variant/30 space-y-2 text-xs">
              <span className="font-label-mono-sm text-secondary uppercase font-bold">
                Recommended Planting Priorities:
              </span>
              <ul className="list-disc list-inside text-on-surface-variant space-y-1 font-body-sm">
                {out.recommended_planting_priorities.map((item: string, i: number) => (
                  <li key={i}>{item}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* Tool 3: CHECK_EXPOSURE */}
      {toolExecution.tool_name === 'CHECK_EXPOSURE' && (
        <div className="space-y-3">
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div className="p-3.5 rounded-lg bg-surface-container border border-outline-variant/30">
              <span className="font-label-mono-sm text-outline">Exposure Level</span>
              <p className="font-mono text-sm font-bold text-error mt-2">
                {out.overall_exposure_level}
              </p>
            </div>
            <div className="p-3.5 rounded-lg bg-surface-container border border-outline-variant/30">
              <span className="font-label-mono-sm text-outline">Transit Stops</span>
              <p className="font-telemetry-value text-secondary mt-1">
                {out.transit_stops_count}
              </p>
            </div>
            <div className="p-3.5 rounded-lg bg-surface-container border border-outline-variant/30">
              <span className="font-label-mono-sm text-outline">Daily Commuters</span>
              <p className="font-telemetry-value text-primary mt-1">
                {out.daily_transit_commuters?.toLocaleString()}
              </p>
            </div>
            <div className="p-3.5 rounded-lg bg-surface-container border border-outline-variant/30">
              <span className="font-label-mono-sm text-outline">Unshaded Waiting Zones</span>
              <p className="font-telemetry-value text-tertiary mt-1">
                {out.unshaded_waiting_areas}
              </p>
            </div>
          </div>

          {out.vulnerable_facilities?.length > 0 && (
            <div className="p-3.5 rounded-lg bg-surface-container border border-outline-variant/30 space-y-2 text-xs">
              <span className="font-label-mono-sm text-secondary uppercase font-bold">
                Nearby Vulnerable Facilities:
              </span>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                {out.vulnerable_facilities.map((fac: any, i: number) => (
                  <div key={i} className="p-2 rounded bg-surface-container-lowest border border-outline-variant/20 flex justify-between">
                    <span className="font-medium text-on-surface">{fac.name}</span>
                    <span className="text-outline font-mono text-[11px]">{fac.distance_m}m away</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Tool 4: COMPARE_INTERVENTIONS */}
      {toolExecution.tool_name === 'COMPARE_INTERVENTIONS' && (
        <div className="space-y-3">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {out.interventions?.map((opt: any) => (
              <div
                key={opt.intervention_id}
                className="p-3.5 rounded-lg bg-surface-container border border-outline-variant/30 space-y-2 text-xs"
              >
                <div className="flex items-start justify-between">
                  <h4 className="font-bold text-on-surface text-sm font-headline-sm">{opt.name}</h4>
                  <span className="px-2 py-0.5 rounded bg-primary/15 text-primary font-mono text-xs font-semibold">
                    -{opt.estimated_cooling_delta_c}°C
                  </span>
                </div>
                <p className="text-on-surface-variant text-[11px] leading-relaxed">{opt.cooling_mechanism}</p>
                <div className="pt-2 border-t border-outline-variant/20 flex justify-between text-[11px] text-outline font-label-mono-sm">
                  <span>Cost: {opt.estimated_cost_tier}</span>
                  <span>Timeline: {opt.implementation_timeline}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Tool 5: REQUEST_MORE_DATA */}
      {toolExecution.tool_name === 'REQUEST_MORE_DATA' && (
        <div className="space-y-3 text-xs">
          <div className="p-3.5 rounded-lg bg-surface-container border border-outline-variant/30 space-y-2">
            <span className="font-label-mono-sm text-tertiary uppercase font-bold">
              Identified Information Gaps:
            </span>
            <div className="space-y-2">
              {out.missing_parameters?.map((p: any, i: number) => (
                <div key={i} className="p-2.5 rounded bg-surface-container-lowest border border-outline-variant/20 flex justify-between items-center">
                  <div>
                    <span className="font-mono text-on-surface font-semibold text-xs">{p.parameter_name}</span>
                    <p className="text-[11px] text-on-surface-variant mt-0.5">{p.description}</p>
                  </div>
                  <span className="text-tertiary font-mono text-[10px] uppercase font-bold shrink-0">{p.importance}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Summary Narrative */}
      {out.analysis_summary && (
        <div className="p-3.5 rounded-lg bg-surface-container-lowest border border-outline-variant/30 text-xs text-on-surface leading-relaxed font-body-sm">
          <strong className="text-primary font-label-mono-sm uppercase">Analytical Summary:</strong>{' '}
          {out.analysis_summary}
        </div>
      )}
    </div>
  );
};
