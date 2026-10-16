import React from 'react';
import { History, ArrowRight, Clock } from 'lucide-react';
import type { ReportAnalyzeResponse } from '../../types/api';

interface DecisionHistoryProps {
  reports: ReportAnalyzeResponse[];
  selectedReportId?: string | null;
  onSelectReport: (report: ReportAnalyzeResponse) => void;
}

export const DecisionHistory: React.FC<DecisionHistoryProps> = ({
  reports,
  selectedReportId,
  onSelectReport,
}) => {
  if (reports.length === 0) {
    return (
      <div className="bg-surface-container-low/90 backdrop-blur-md border border-outline-variant/30 rounded-xl p-8 text-center space-y-3">
        <div className="w-12 h-12 rounded-full bg-surface-container border border-outline-variant/30 flex items-center justify-center text-outline mx-auto">
          <History className="w-6 h-6" />
        </div>
        <h4 className="font-headline-sm text-sm font-semibold text-on-surface">
          No Decision History in Current Session
        </h4>
        <p className="font-body-sm text-on-surface-variant max-w-sm mx-auto">
          Submit an environmental report from the Analyze tab or choose a monitored zone on the map to run the decision agent.
        </p>
      </div>
    );
  }

  return (
    <div className="bg-surface-container-low/90 backdrop-blur-md border border-outline-variant/30 rounded-xl p-5 shadow-lg space-y-4">
      <div className="flex items-center justify-between border-b border-outline-variant/20 pb-3">
        <div>
          <h3 className="font-headline-sm text-on-surface font-bold flex items-center gap-2">
            <span>Session Decision Audit History</span>
            <span className="font-label-mono-sm px-2 py-0.5 rounded bg-primary/10 text-primary border border-primary/30">
              {reports.length} {reports.length === 1 ? 'Record' : 'Records'}
            </span>
          </h3>
          <p className="font-label-mono-sm text-outline mt-0.5">
            Audit history of environmental analyses executed during this session.
          </p>
        </div>
      </div>

      <div className="space-y-2.5">
        {reports.map((rep) => {
          const isSelected = rep.report_id === selectedReportId;
          const isAccepted = rep.decision?.status === 'accepted';
          const isGated = rep.workflow_stage === 'NEEDS_CLARIFICATION';

          return (
            <div
              key={rep.report_id}
              onClick={() => onSelectReport(rep)}
              className={`p-3.5 rounded-lg border transition-all cursor-pointer flex flex-col sm:flex-row sm:items-center justify-between gap-3 ${
                isSelected
                  ? 'bg-surface-container-highest border-primary/50 shadow-sm'
                  : 'bg-surface-container border-outline-variant/30 hover:border-outline-variant hover:bg-surface-container-high'
              }`}
            >
              <div className="space-y-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="font-mono text-xs font-bold text-on-surface">{rep.report_id}</span>
                  <span className="text-outline text-xs">&bull;</span>
                  <span className="font-body-sm font-medium text-on-surface-variant">{rep.location}</span>
                  <span
                    className={`font-label-mono-sm px-1.5 py-0.5 rounded text-[10px] uppercase font-bold ${
                      isAccepted
                        ? 'bg-primary/15 text-primary border border-primary/30'
                        : isGated
                        ? 'bg-tertiary/15 text-tertiary border border-tertiary/30'
                        : 'bg-error-container/20 text-error border border-error/30'
                    }`}
                  >
                    {rep.workflow_stage}
                  </span>
                </div>
                <p className="font-body-sm text-outline line-clamp-1 max-w-xl truncate">
                  {rep.original_report}
                </p>
              </div>

              <div className="flex items-center gap-4 shrink-0 text-xs">
                <div className="text-right">
                  <span className="font-mono text-primary font-bold block">
                    {rep.decision?.decision || 'NONE'}
                  </span>
                  <span className="font-label-mono-sm text-outline">
                    Conf: {((rep.decision?.confidence || 0) * 100).toFixed(1)}%
                  </span>
                </div>

                <div className="text-right hidden sm:block">
                  <div className="flex items-center gap-1 font-label-mono-sm text-secondary">
                    <Clock className="w-3 h-3" />
                    <span>{rep.total_latency_ms.toLocaleString()} ms</span>
                  </div>
                </div>

                <div className="p-1 rounded bg-surface-container-highest border border-outline-variant/30 text-on-surface-variant">
                  <ArrowRight className="w-4 h-4" />
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
