import React from 'react';
import { Clock } from 'lucide-react';
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
  const completedCount = steps.filter((s) => s.status === 'completed').length;

  return (
    <div className="bg-surface-container-low/95 backdrop-blur-md rounded-xl p-5 border border-outline-variant/30 shadow-xl flex flex-col space-y-4">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-outline-variant/20">
        <div className="flex items-center gap-2">
          <span className="material-symbols-outlined text-secondary text-[22px]">account_tree</span>
          <h2 className="font-headline-sm text-on-surface font-bold">
            Decision Execution Trace
          </h2>
        </div>

        <div className="flex items-center gap-3">
          <span className="font-label-mono-sm text-primary uppercase font-bold">
            {completedCount} of {steps.length} Steps Complete
          </span>
          <div className="flex items-center gap-1 px-2.5 py-1 rounded bg-surface-container border border-outline-variant/30 font-label-mono-sm text-secondary">
            <Clock className="w-3.5 h-3.5" />
            <span>Total: {totalLatencyMs.toLocaleString()} ms</span>
          </div>
        </div>
      </div>

      {/* Terminal State Callout */}
      <div className="flex items-center justify-between px-3.5 py-2 rounded-lg bg-surface-container border border-outline-variant/20 text-xs">
        <span className="font-label-mono-sm text-outline">Pipeline Terminal State:</span>
        <span className="font-mono font-bold text-primary px-2 py-0.5 rounded bg-primary/10 border border-primary/30">
          {workflowStage}
        </span>
      </div>

      {/* Timeline Pipeline Container (Stitch vertical pipeline) */}
      <div className="relative pl-7 space-y-4 before:absolute before:left-2 before:top-2 before:bottom-2 before:w-0.5 before:bg-surface-container-highest">
        {steps.map((step, idx) => {
          let dotColor = 'bg-primary';
          let statusColor = 'text-primary';

          if (step.status === 'gated') {
            dotColor = 'bg-tertiary';
            statusColor = 'text-tertiary';
          } else if (step.status === 'failed') {
            dotColor = 'bg-error';
            statusColor = 'text-error';
          } else if (step.status === 'skipped') {
            dotColor = 'bg-outline';
            statusColor = 'text-outline';
          }

          return (
            <div key={idx} className="relative flex flex-col space-y-1 group">
              {/* Stepper Node Dot */}
              <div
                className={`absolute -left-[27px] top-1 w-3.5 h-3.5 rounded-full ${dotColor} flex items-center justify-center ring-4 ring-surface-container-low shadow-sm z-10 transition-transform group-hover:scale-125`}
              />

              {/* Step Info */}
              <div className="p-3 rounded-lg bg-surface-container border border-outline-variant/30 hover:border-outline-variant transition-all space-y-1">
                <div className="flex items-center justify-between">
                  <span className="font-label-mono-sm font-bold text-on-surface">
                    {step.step_number}. {step.name}
                  </span>
                  <div className="flex items-center gap-2">
                    <span className={`font-label-mono-sm uppercase font-bold text-[10px] ${statusColor}`}>
                      {step.status}
                    </span>
                    <span className="font-label-mono-sm text-secondary font-mono text-[11px]">
                      {step.duration_ms.toLocaleString()} ms
                    </span>
                  </div>
                </div>

                {/* Metadata Details */}
                {Object.keys(step.details || {}).length > 0 && (
                  <div className="pt-1 text-[11px] text-on-surface-variant font-mono space-y-0.5">
                    {Object.entries(step.details).map(([k, v]) => (
                      <div key={k} className="flex items-baseline gap-1.5">
                        <span className="text-outline">{k}:</span>
                        <span className="text-on-surface">
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
