import React from 'react';
import {
  Wrench,
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
    <div className="bg-[#161c28] border border-[#242d3d] rounded-xl p-5 shadow-sm space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-[#242d3d]/60 pb-3">
        <div className="flex items-center space-x-2.5">
          <div className="p-2 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-emerald-400">
            <Wrench className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-base font-bold text-slate-100 flex items-center space-x-2">
              <span>Tool Execution: {toolExecution.tool_name}</span>
            </h3>
            <p className="text-xs text-slate-400 mt-0.5">
              Deterministic Python analytical module dispatched by Decider 2B.
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-1.5 px-3 py-1 rounded-full bg-[#111620] border border-[#242d3d] text-xs text-slate-400 font-mono">
            <Clock className="w-3.5 h-3.5 text-purple-400" />
            <span>{toolExecution.execution_time_ms.toLocaleString()} ms</span>
          </div>

          <div
            className={`flex items-center space-x-1.5 px-3 py-1 rounded-full text-xs font-semibold ${
              isSuccess
                ? 'bg-emerald-500/15 border border-emerald-500/30 text-emerald-300'
                : 'bg-rose-500/15 border border-rose-500/30 text-rose-300'
            }`}
          >
            {isSuccess ? (
              <>
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                <span>SUCCESS</span>
              </>
            ) : (
              <>
                <AlertCircle className="w-3.5 h-3.5 text-rose-400" />
                <span>FAILED</span>
              </>
            )}
          </div>
        </div>
      </div>

      {/* Synthetic Data Disclaimer Banner */}
      <div className="p-3 rounded-lg bg-[#111620] border border-amber-500/30 flex items-center justify-between text-xs text-slate-300">
        <div className="flex items-center space-x-2">
          <Database className="w-4 h-4 text-amber-400 shrink-0" />
          <span>
            <strong className="text-amber-300 font-semibold">Data Provenance:</strong>{' '}
            {out.data_label || 'SYNTHETIC_DEV_DATASET_V1'} &bull; {out.disclaimer || 'Sample measurements'}
          </span>
        </div>
      </div>

      {/* Tool-Specific Structured Metrics */}
      {toolExecution.tool_name === 'ANALYZE_HEAT' && (
        <div className="space-y-3">
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div className="p-3 rounded-lg bg-[#111620] border border-[#242d3d]">
              <span className="text-[11px] text-slate-400">Ambient Air Temp</span>
              <p className="font-mono text-xl font-bold text-rose-400 mt-1">
                {out.observed_ambient_temp_c}°C
              </p>
            </div>
            <div className="p-3 rounded-lg bg-[#111620] border border-[#242d3d]">
              <span className="text-[11px] text-slate-400">Radiant Surface Temp</span>
              <p className="font-mono text-xl font-bold text-amber-400 mt-1">
                {out.observed_surface_temp_c}°C
              </p>
            </div>
            <div className="p-3 rounded-lg bg-[#111620] border border-[#242d3d]">
              <span className="text-[11px] text-slate-400">Heat Index</span>
              <p className="font-mono text-xl font-bold text-purple-400 mt-1">
                {out.heat_index_c}°C
              </p>
            </div>
            <div className="p-3 rounded-lg bg-[#111620] border border-[#242d3d]">
              <span className="text-[11px] text-slate-400">Thermal Severity</span>
              <p className="font-mono text-sm font-bold text-rose-300 mt-2">
                {out.heat_severity_level}
              </p>
            </div>
          </div>

          <div className="p-3 rounded-lg bg-[#111620] border border-[#242d3d] space-y-1 text-xs">
            <span className="font-semibold text-slate-300">Nocturnal Retention Risk:</span>
            <p className="text-slate-400">{out.nocturnal_retention_risk}</p>
          </div>
        </div>
      )}

      {toolExecution.tool_name === 'CHECK_VEGETATION' && (
        <div className="space-y-3">
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div className="p-3 rounded-lg bg-[#111620] border border-[#242d3d]">
              <span className="text-[11px] text-slate-400">Canopy Coverage</span>
              <p className="font-mono text-xl font-bold text-emerald-400 mt-1">
                {out.canopy_coverage_pct}%
              </p>
            </div>
            <div className="p-3 rounded-lg bg-[#111620] border border-[#242d3d]">
              <span className="text-[11px] text-slate-400">Canopy Deficit (Goal 30%)</span>
              <p className="font-mono text-xl font-bold text-amber-400 mt-1">
                {out.canopy_deficit_pct}%
              </p>
            </div>
            <div className="p-3 rounded-lg bg-[#111620] border border-[#242d3d]">
              <span className="text-[11px] text-slate-400">NDVI Index</span>
              <p className="font-mono text-xl font-bold text-cyan-400 mt-1">
                {out.ndvi_index}
              </p>
            </div>
            <div className="p-3 rounded-lg bg-[#111620] border border-[#242d3d]">
              <span className="text-[11px] text-slate-400">Cooling Potential</span>
              <p className="font-mono text-xl font-bold text-emerald-300 mt-1">
                +{out.estimated_cooling_potential_c}°C
              </p>
            </div>
          </div>

          {out.recommended_planting_priorities?.length > 0 && (
            <div className="p-3 rounded-lg bg-[#111620] border border-[#242d3d] space-y-2 text-xs">
              <span className="font-semibold text-slate-300">Recommended Planting Priorities:</span>
              <ul className="list-disc list-inside text-slate-400 space-y-1">
                {out.recommended_planting_priorities.map((item: string, i: number) => (
                  <li key={i}>{item}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {toolExecution.tool_name === 'CHECK_EXPOSURE' && (
        <div className="space-y-3">
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div className="p-3 rounded-lg bg-[#111620] border border-[#242d3d]">
              <span className="text-[11px] text-slate-400">Exposure Level</span>
              <p className="font-mono text-sm font-bold text-rose-300 mt-2">
                {out.overall_exposure_level}
              </p>
            </div>
            <div className="p-3 rounded-lg bg-[#111620] border border-[#242d3d]">
              <span className="text-[11px] text-slate-400">Transit Stops</span>
              <p className="font-mono text-xl font-bold text-cyan-400 mt-1">
                {out.transit_stops_count}
              </p>
            </div>
            <div className="p-3 rounded-lg bg-[#111620] border border-[#242d3d]">
              <span className="text-[11px] text-slate-400">Daily Commuters</span>
              <p className="font-mono text-xl font-bold text-purple-400 mt-1">
                {out.daily_transit_commuters?.toLocaleString()}
              </p>
            </div>
            <div className="p-3 rounded-lg bg-[#111620] border border-[#242d3d]">
              <span className="text-[11px] text-slate-400">Unshaded Waiting Zones</span>
              <p className="font-mono text-xl font-bold text-amber-400 mt-1">
                {out.unshaded_waiting_areas}
              </p>
            </div>
          </div>

          {out.vulnerable_facilities?.length > 0 && (
            <div className="p-3 rounded-lg bg-[#111620] border border-[#242d3d] space-y-2 text-xs">
              <span className="font-semibold text-slate-300">Nearby Vulnerable Facilities:</span>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                {out.vulnerable_facilities.map((fac: any, i: number) => (
                  <div key={i} className="p-2 rounded bg-[#0d121c] border border-[#242d3d] flex justify-between">
                    <span className="font-medium text-slate-200">{fac.name}</span>
                    <span className="text-slate-400 font-mono text-[11px]">{fac.distance_m}m away</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {toolExecution.tool_name === 'COMPARE_INTERVENTIONS' && (
        <div className="space-y-3">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {out.interventions?.map((opt: any) => (
              <div
                key={opt.intervention_id}
                className="p-3.5 rounded-lg bg-[#111620] border border-[#242d3d] space-y-2 text-xs"
              >
                <div className="flex items-start justify-between">
                  <h4 className="font-bold text-slate-200 text-sm">{opt.name}</h4>
                  <span className="px-2 py-0.5 rounded bg-emerald-500/15 text-emerald-300 font-mono text-xs font-semibold">
                    -{opt.estimated_cooling_delta_c}°C
                  </span>
                </div>
                <p className="text-slate-400 text-[11px]">{opt.cooling_mechanism}</p>
                <div className="pt-2 border-t border-[#242d3d] flex justify-between text-[11px] text-slate-400">
                  <span>Cost: {opt.estimated_cost_tier}</span>
                  <span>Timeline: {opt.implementation_timeline}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {toolExecution.tool_name === 'REQUEST_MORE_DATA' && (
        <div className="space-y-3 text-xs">
          <div className="p-3 rounded-lg bg-[#111620] border border-[#242d3d] space-y-2">
            <span className="font-semibold text-amber-300">Identified Information Gaps:</span>
            <div className="space-y-1.5">
              {out.missing_parameters?.map((p: any, i: number) => (
                <div key={i} className="p-2 rounded bg-[#0d121c] border border-[#242d3d] flex justify-between">
                  <div>
                    <span className="font-mono text-slate-200 font-semibold">{p.parameter_name}</span>
                    <p className="text-[11px] text-slate-400 mt-0.5">{p.description}</p>
                  </div>
                  <span className="text-amber-400 font-mono text-[10px] shrink-0">{p.importance}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Summary Text */}
      {out.analysis_summary && (
        <div className="p-3 rounded-lg bg-[#111620] border border-[#242d3d] text-xs text-slate-300 leading-relaxed">
          <strong className="text-slate-200">Analytical Summary:</strong> {out.analysis_summary}
        </div>
      )}
    </div>
  );
};
