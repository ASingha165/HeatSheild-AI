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
      <div className="bg-[#161c28] border border-[#242d3d] rounded-xl p-8 text-center space-y-3">
        <div className="w-12 h-12 rounded-full bg-[#111620] border border-[#242d3d] flex items-center justify-center text-slate-500 mx-auto">
          <History className="w-6 h-6" />
        </div>
        <h4 className="text-sm font-semibold text-slate-300">No Decision History in Current Session</h4>
        <p className="text-xs text-slate-500 max-w-sm mx-auto">
          Submit an environmental report from the Analyze tab or choose a monitored zone on the map to run the decision agent.
        </p>
      </div>
    );
  }

  return (
    <div className="bg-[#161c28] border border-[#242d3d] rounded-xl p-5 shadow-sm space-y-4">
      <div className="flex items-center justify-between border-b border-[#242d3d]/60 pb-3">
        <div>
          <h3 className="text-base font-bold text-slate-100 flex items-center space-x-2">
            <span>Session Decision History</span>
            <span className="text-xs font-mono px-2 py-0.5 rounded bg-emerald-500/15 text-emerald-300 border border-emerald-500/30">
              {reports.length} {reports.length === 1 ? 'Record' : 'Records'}
            </span>
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">
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
                  ? 'bg-cyan-500/10 border-cyan-500/40 shadow-sm'
                  : 'bg-[#111620] border-[#242d3d] hover:border-[#334055] hover:bg-[#1a2130]'
              }`}
            >
              <div className="space-y-1">
                <div className="flex items-center space-x-2">
                  <span className="font-mono text-xs font-bold text-slate-200">{rep.report_id}</span>
                  <span className="text-slate-500 text-xs">&bull;</span>
                  <span className="text-xs font-medium text-slate-300">{rep.location}</span>
                  <span
                    className={`text-[10px] font-mono px-1.5 py-0.2 rounded font-semibold ${
                      isAccepted
                        ? 'bg-emerald-500/15 text-emerald-300 border border-emerald-500/30'
                        : isGated
                        ? 'bg-amber-500/15 text-amber-300 border border-amber-500/30'
                        : 'bg-rose-500/15 text-rose-300 border border-rose-500/30'
                    }`}
                  >
                    {rep.workflow_stage}
                  </span>
                </div>
                <p className="text-xs text-slate-400 line-clamp-1 max-w-xl">{rep.original_report}</p>
              </div>

              <div className="flex items-center space-x-4 shrink-0 text-xs">
                <div className="text-right">
                  <span className="font-mono text-cyan-300 font-semibold block">
                    {rep.decision?.decision || 'NONE'}
                  </span>
                  <span className="text-[11px] text-slate-400 font-mono">
                    Conf: {((rep.decision?.confidence || 0) * 100).toFixed(1)}%
                  </span>
                </div>

                <div className="text-right hidden sm:block">
                  <div className="flex items-center space-x-1 text-slate-400 text-[11px] font-mono">
                    <Clock className="w-3 h-3 text-purple-400" />
                    <span>{rep.total_latency_ms.toLocaleString()} ms</span>
                  </div>
                </div>

                <div className="p-1 rounded bg-[#161c28] border border-[#242d3d] text-slate-400">
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
