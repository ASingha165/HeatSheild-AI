import React from 'react';
import {
  Cpu,
  Clock,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  BarChart2,
} from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from 'recharts';
import type { NormalizedDecision } from '../../types/api';

interface DeciderPanelProps {
  decision: NormalizedDecision;
}

export const DeciderPanel: React.FC<DeciderPanelProps> = ({ decision }) => {
  const isAccepted = decision.status === 'accepted';
  const isClarification = decision.status === 'requires_clarification';
  const isInvalid = decision.status === 'rejected_invalid';

  // Format probabilities for Recharts bar chart
  const probData = Object.entries(decision.probabilities || {}).map(([action, val]) => ({
    action,
    probability: Math.round(val * 1000) / 10, // e.g. 88.5%
    rawVal: val,
    isSelected: action === decision.decision,
  })).sort((a, b) => b.probability - a.probability);

  return (
    <div className="bg-[#161c28] border border-[#242d3d] rounded-xl p-5 shadow-sm space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-[#242d3d]/60 pb-3">
        <div className="flex items-center space-x-2.5">
          <div className="p-2 rounded-lg bg-cyan-500/10 border border-cyan-500/30 text-cyan-400">
            <Cpu className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-base font-bold text-slate-100 flex items-center space-x-2">
              <span>Strands Decider 2B Routing</span>
              <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-cyan-500/15 text-cyan-300 border border-cyan-500/30">
                Pointer Readout Head
              </span>
            </h3>
            <p className="text-xs text-slate-400 mt-0.5">
              Typed single forward-pass classification across 5 predefined analytical actions.
            </p>
          </div>
        </div>

        {/* Status Badge */}
        <div>
          {isAccepted && (
            <div className="flex items-center space-x-1.5 px-3 py-1 rounded-full bg-emerald-500/15 border border-emerald-500/30 text-emerald-300 text-xs font-semibold">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
              <span>ACCEPTED &bull; PROCEED_TO_TOOL</span>
            </div>
          )}
          {isClarification && (
            <div className="flex items-center space-x-1.5 px-3 py-1 rounded-full bg-amber-500/15 border border-amber-500/30 text-amber-300 text-xs font-semibold">
              <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
              <span>GATED &bull; REQUIRES_CLARIFICATION</span>
            </div>
          )}
          {isInvalid && (
            <div className="flex items-center space-x-1.5 px-3 py-1 rounded-full bg-rose-500/15 border border-rose-500/30 text-rose-300 text-xs font-semibold">
              <XCircle className="w-3.5 h-3.5 text-rose-400" />
              <span>REJECTED_INVALID</span>
            </div>
          )}
        </div>
      </div>

      {/* Main Choice & Metrics Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        {/* Selected Action Card */}
        <div className="p-4 rounded-lg bg-[#111620] border border-[#242d3d] flex flex-col justify-between">
          <span className="text-xs text-slate-400 font-medium">Selected Analytical Tool</span>
          <div className="mt-1">
            <span className="font-mono text-base font-bold text-cyan-300">
              {decision.decision}
            </span>
          </div>
          <span className="text-[11px] text-slate-400 mt-2">
            Predefined action option
          </span>
        </div>

        {/* Calibrated Model Confidence */}
        <div className="p-4 rounded-lg bg-[#111620] border border-[#242d3d] flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <span className="text-xs text-slate-400 font-medium">Calibrated Confidence</span>
            <span className="text-[10px] text-slate-400 font-mono">
              Gate: &ge;{Math.round(decision.confidence_threshold * 100)}%
            </span>
          </div>
          <div className="mt-1 flex items-baseline space-x-2">
            <span className={`font-mono text-xl font-bold ${
              decision.is_above_threshold ? 'text-emerald-400' : 'text-amber-400'
            }`}>
              {(decision.confidence * 100).toFixed(1)}%
            </span>
            <span className="text-xs text-slate-400 font-mono">({decision.confidence.toFixed(4)})</span>
          </div>
          <div className="w-full bg-[#1e2636] h-1.5 rounded-full overflow-hidden mt-2">
            <div
              className={`h-full rounded-full transition-all ${
                decision.is_above_threshold ? 'bg-emerald-400' : 'bg-amber-400'
              }`}
              style={{ width: `${Math.min(100, Math.max(0, decision.confidence * 100))}%` }}
            />
          </div>
        </div>

        {/* Measured Decision Latency */}
        <div className="p-4 rounded-lg bg-[#111620] border border-[#242d3d] flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <span className="text-xs text-slate-400 font-medium">Model Latency</span>
            <Clock className="w-3.5 h-3.5 text-purple-400" />
          </div>
          <div className="mt-1">
            <span className="font-mono text-xl font-bold text-purple-300">
              {decision.latency_ms.toLocaleString()} ms
            </span>
          </div>
          <span className="text-[11px] text-slate-400 mt-2">
            Single causal forward-pass
          </span>
        </div>
      </div>

      {/* Low-Confidence Safety Notice */}
      {isClarification && decision.clarification_prompt && (
        <div className="p-3.5 rounded-lg bg-amber-500/10 border border-amber-500/30 flex items-start space-x-3 text-xs text-amber-200">
          <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
          <div className="space-y-1">
            <p className="font-semibold text-amber-300">
              Safety Gate Tripped: Autonomous Tool Execution Paused
            </p>
            <p className="text-slate-300 leading-relaxed">
              {decision.clarification_prompt}
            </p>
          </div>
        </div>
      )}

      {/* Probabilities Distribution Chart */}
      {probData.length > 0 && (
        <div className="p-4 rounded-lg bg-[#111620] border border-[#242d3d] space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-300 flex items-center space-x-1.5">
              <BarChart2 className="w-3.5 h-3.5 text-cyan-400" />
              <span>Full Probability Distribution Across Allowed Actions</span>
            </span>
            <span className="text-[11px] text-slate-400 font-mono">Softmax Logits</span>
          </div>

          <div className="h-44 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={probData}
                layout="vertical"
                margin={{ top: 5, right: 30, left: 100, bottom: 5 }}
              >
                <XAxis type="number" domain={[0, 100]} unit="%" tick={{ fill: '#64748b', fontSize: 11 }} />
                <YAxis
                  type="category"
                  dataKey="action"
                  tick={{ fill: '#94a3b8', fontSize: 11, fontFamily: 'monospace' }}
                  width={130}
                />
                <Tooltip
                  formatter={(val: any) => [`${val}%`, 'Probability']}
                  contentStyle={{
                    backgroundColor: '#161c28',
                    borderColor: '#334055',
                    borderRadius: '0.5rem',
                    color: '#f1f5f9',
                    fontSize: '12px',
                  }}
                />
                <Bar dataKey="probability" radius={[0, 4, 4, 0]}>
                  {probData.map((entry, index) => (
                    <Cell
                      key={`cell-${index}`}
                      fill={entry.isSelected ? '#06b6d4' : '#242d3d'}
                      stroke={entry.isSelected ? '#38bdf8' : '#334055'}
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}
    </div>
  );
};
