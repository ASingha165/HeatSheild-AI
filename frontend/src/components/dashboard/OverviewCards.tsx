import React from 'react';
import { MapPin, FileCheck, AlertTriangle, Zap, Database } from 'lucide-react';
import type { ReportAnalyzeResponse } from '../../types/api';

interface OverviewCardsProps {
  totalLocations: number;
  analyzedReports: ReportAnalyzeResponse[];
  onSelectAction?: (actionName: string) => void;
}

export const OverviewCards: React.FC<OverviewCardsProps> = ({
  totalLocations,
  analyzedReports,
}) => {
  const reportsCount = analyzedReports.length;
  const clarificationCount = analyzedReports.filter(
    (r) => r.workflow_stage === 'NEEDS_CLARIFICATION'
  ).length;

  const mostRecent = analyzedReports[0];
  const lastLatency = mostRecent?.decision?.latency_ms !== undefined
    ? `${mostRecent.decision.latency_ms.toLocaleString()} ms`
    : 'Not yet measured';

  const cards = [
    {
      label: 'Sample Urban Zones',
      value: totalLocations > 0 ? totalLocations.toString() : '0',
      description: 'Monitored benchmark microclimates',
      icon: <MapPin className="w-5 h-5 text-cyan-400" />,
      tag: 'SYNTHETIC_DATASET',
      color: 'border-cyan-500/20 bg-cyan-500/5',
    },
    {
      label: 'Reports Processed',
      value: reportsCount.toString(),
      description: 'Analyzed in current session',
      icon: <FileCheck className="w-5 h-5 text-emerald-400" />,
      tag: reportsCount > 0 ? 'ACTIVE_SESSION' : 'AWAITING_INPUT',
      color: 'border-emerald-500/20 bg-emerald-500/5',
    },
    {
      label: 'Gated / Clarifications',
      value: clarificationCount.toString(),
      description: 'Confidence below safety gate',
      icon: <AlertTriangle className="w-5 h-5 text-amber-400" />,
      tag: 'SAFETY_GATE_TRIGGERED',
      color: 'border-amber-500/20 bg-amber-500/5',
    },
    {
      label: 'Last Decider Latency',
      value: lastLatency,
      description: 'Single causal forward pass (CPU)',
      icon: <Zap className="w-5 h-5 text-purple-400" />,
      tag: 'SUB-SECOND_ROUTING',
      color: 'border-purple-500/20 bg-purple-500/5',
    },
  ];

  return (
    <div className="space-y-4">
      {/* Synthetic Dataset Notice Banner */}
      <div className="flex items-center justify-between p-3 rounded-lg bg-[#161c28] border border-amber-500/30 text-xs">
        <div className="flex items-center space-x-2.5 text-amber-300">
          <Database className="w-4 h-4 shrink-0" />
          <span>
            <strong className="font-semibold">Development Notice:</strong> All physical measurements (temperatures, NDVI canopy, pedestrian counts) are sourced from synthetic demonstration benchmarks (<code className="font-mono text-[11px] text-amber-200 bg-amber-950/40 px-1 py-0.5 rounded">SYNTHETIC_DEV_DATASET_V1</code>).
          </span>
        </div>
        <span className="text-[11px] text-slate-400 shrink-0 font-medium">AWS Decider 2B Hackathon</span>
      </div>

      {/* Grid of 4 Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {cards.map((c, i) => (
          <div
            key={i}
            className={`p-5 rounded-xl border ${c.color} bg-[#161c28] flex flex-col justify-between shadow-sm hover:border-[#334055] transition-all`}
          >
            <div className="flex items-start justify-between">
              <div>
                <p className="text-xs text-slate-400 font-medium">{c.label}</p>
                <h3 className="text-2xl font-bold text-slate-100 mt-1 font-mono tracking-tight">{c.value}</h3>
              </div>
              <div className="p-2.5 rounded-lg bg-[#111620] border border-[#242d3d] shrink-0">
                {c.icon}
              </div>
            </div>
            <div className="mt-4 pt-3 border-t border-[#242d3d]/60 flex items-center justify-between text-[11px]">
              <span className="text-slate-400">{c.description}</span>
              <span className="font-mono text-[10px] text-slate-400 px-1.5 py-0.5 rounded bg-[#111620] border border-[#242d3d]">
                {c.tag}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
