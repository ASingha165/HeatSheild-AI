import React from 'react';
import {
  Clock,
  AlertTriangle,
  XCircle,
  HelpCircle,
  GitCommit,
  Check,
} from 'lucide-react';
import type { TraceStep, WorkflowStage } from '../../types/api';

interface ExecutionTraceProps {
  steps: TraceStep[];
  totalLatencyMs: number;
  workflowStage: WorkflowStage;
}

export const ExecutionTrace: React.FC<ExecutionTraceProps> = ({
  steps,
  totalLatencyMs,
  workflowStage,
}) => {
  return (
    <div className="bg-[#161c28] border border-[#242d3d] rounded-xl p-5 shadow-sm space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-[#242d3d]/60 pb-3">
        <div className="flex items-center space-x-2.5">
          <div className="p-2 rounded-lg bg-purple-500/10 border border-purple-500/30 text-purple-400">
            <GitCommit className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-base font-bold text-slate-100 flex items-center space-x-2">
              <span>Transparent Execution Trace</span>
            </h3>
            <p className="text-xs text-slate-400 mt-0.5">
              Auditable step-by-step pipeline execution trace with individual latencies.
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-2 px-3 py-1 rounded-full bg-[#111620] border border-[#242d3d] text-xs font-mono text-slate-300">
          <Clock className="w-3.5 h-3.5 text-purple-400" />
          <span>Total Latency: {totalLatencyMs.toLocaleString()} ms</span>
        </div>
      </div>

      {/* Workflow Stage Callout */}
      <div className="flex items-center justify-between px-3.5 py-2 rounded-lg bg-[#111620] border border-[#242d3d] text-xs">
        <span className="text-slate-400 font-medium">Pipeline Terminal State:</span>
        <span className="font-mono font-bold text-cyan-300 px-2 py-0.5 rounded bg-cyan-950/40 border border-cyan-500/30">
          {workflowStage}
        </span>
      </div>

      {/* Stepper Timeline */}
      <div className="relative pl-6 space-y-4 before:absolute before:left-2.5 before:top-3 before:bottom-3 before:w-0.5 before:bg-[#242d3d]">
        {steps.map((step, idx) => {
          let icon = <Check className="w-3.5 h-3.5 text-emerald-400" />;
          let iconBg = 'bg-emerald-500/20 border-emerald-500/40 text-emerald-400';

          if (step.status === 'gated') {
            icon = <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />;
            iconBg = 'bg-amber-500/20 border-amber-500/40 text-amber-400';
          } else if (step.status === 'failed') {
            icon = <XCircle className="w-3.5 h-3.5 text-rose-400" />;
            iconBg = 'bg-rose-500/20 border-rose-500/40 text-rose-400';
          } else if (step.status === 'skipped') {
            icon = <HelpCircle className="w-3.5 h-3.5 text-slate-500" />;
            iconBg = 'bg-[#111620] border-[#242d3d] text-slate-500';
          }

          return (
            <div key={idx} className="relative group">
              {/* Stepper Node Icon */}
              <div
                className={`absolute -left-[30px] top-1 w-6 h-6 rounded-full border flex items-center justify-center ${iconBg} shadow-sm z-10 transition-transform group-hover:scale-110`}
              >
                {icon}
              </div>

              {/* Step Card */}
              <div className="p-3 rounded-lg bg-[#111620] border border-[#242d3d] hover:border-[#334055] transition-all space-y-1.5 text-xs">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-slate-200">
                    Step {step.step_number}: {step.name}
                  </span>
                  <div className="flex items-center space-x-2">
                    <span
                      className={`text-[10px] font-mono px-1.5 py-0.5 rounded uppercase font-semibold ${
                        step.status === 'completed'
                          ? 'bg-emerald-500/10 text-emerald-300 border border-emerald-500/20'
                          : step.status === 'gated'
                          ? 'bg-amber-500/10 text-amber-300 border border-amber-500/20'
                          : 'bg-rose-500/10 text-rose-300 border border-rose-500/20'
                      }`}
                    >
                      {step.status}
                    </span>
                    <span className="text-[11px] font-mono text-purple-300">
                      {step.duration_ms.toLocaleString()} ms
                    </span>
                  </div>
                </div>

                {/* Step Metadata details */}
                {Object.keys(step.details || {}).length > 0 && (
                  <div className="pt-1 text-[11px] text-slate-400 font-mono space-y-0.5">
                    {Object.entries(step.details).map(([k, v]) => (
                      <div key={k} className="flex items-baseline space-x-1">
                        <span className="text-slate-500">{k}:</span>
                        <span className="text-slate-300">
                          {typeof v === 'object' ? JSON.stringify(v) : String(v)}
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
