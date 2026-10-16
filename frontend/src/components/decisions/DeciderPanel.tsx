import {
  CheckCircle2,
  AlertTriangle,
  XCircle,
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

const ACTION_OPTIONS = [
  'ANALYZE_HEAT',
  'CHECK_VEGETATION',
  'CHECK_EXPOSURE',
  'COMPARE_INTERVENTIONS',
  'REQUEST_MORE_DATA',
];

export const DeciderPanel: React.FC<DeciderPanelProps> = ({ decision }) => {
  const isAccepted = decision.status === 'accepted';
  const isClarification = decision.status === 'requires_clarification';
  const isInvalid = decision.status === 'rejected_invalid';

  // Format probabilities for Recharts bar chart
  const probData = ACTION_OPTIONS.map((action) => {
    const val = decision.probabilities?.[action] ?? 0;
    return {
      action,
      probability: Math.round(val * 1000) / 10, // e.g. 87.0%
      rawVal: val,
      isSelected: action === decision.decision,
    };
  }).sort((a, b) => b.probability - a.probability);

  const confidencePct = Math.round((decision.confidence ?? 0) * 100);

  return (
    <div className="bg-surface-container-low/95 backdrop-blur-md rounded-xl p-5 border border-outline-variant/30 shadow-xl flex flex-col space-y-4 relative overflow-hidden">
      {/* Subtle tactical corner indicator */}
      <div className="absolute top-0 right-0 w-32 h-32 bg-primary/5 rounded-bl-full pointer-events-none"></div>

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-outline-variant/20">
        <div className="flex items-center gap-2">
          <span className="material-symbols-outlined text-secondary text-[22px]">psychology_alt</span>
          <h2 className="font-headline-sm text-on-surface font-bold">
            Strands Decider 2B Decision Engine
          </h2>
        </div>
        <span className="font-label-mono-sm text-outline uppercase tracking-wider">
          Action Classification & Gating
        </span>
      </div>

      {/* Highlight Action Banner (Stitch Anchor) */}
      <div className="p-4 rounded-xl bg-surface-container-high/90 border border-outline-variant/30 shadow-md flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-primary/20 border border-primary/40 flex items-center justify-center text-primary shadow-[0_0_16px_rgba(78,222,163,0.3)] shrink-0">
            <span className="material-symbols-outlined text-[28px]">flare</span>
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-label-mono-sm uppercase text-outline">Selected Action:</span>
              <span className="font-label-mono-md font-bold text-primary tracking-wide text-base">
                {decision.decision}
              </span>
              <span className="h-2 w-2 rounded-full bg-primary animate-ping"></span>
            </div>
            <div className="flex flex-wrap items-center gap-2 mt-1">
              <span className="px-2 py-0.5 rounded bg-primary text-on-primary font-label-mono-sm font-bold">
                {confidencePct}% Confidence
              </span>
              <span className="font-label-mono-sm text-on-surface-variant">
                Latency: {decision.latency_ms?.toLocaleString() ?? 0} ms (Decider 2B)
              </span>
              <span className="font-label-mono-sm text-primary">
                Execution-gate: {isAccepted ? 'PASSED (≥60%)' : isClarification ? 'REQUIRES_CLARIFICATION' : 'REJECTED'}
              </span>
            </div>
            <p className="font-label-mono-sm text-outline mt-1 italic text-[11px]">
              * Confidence reflects statistical causal softmax margin across allowed action space.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 self-start md:self-center shrink-0">
          {isAccepted && (
            <span className="px-3 py-1.5 rounded-lg bg-primary/10 text-primary border border-primary/30 font-label-mono-sm flex items-center gap-1.5 font-bold shadow-sm">
              <CheckCircle2 className="w-4 h-4 text-primary" />
              <span>Gated to Tools</span>
            </span>
          )}
          {isClarification && (
            <span className="px-3 py-1.5 rounded-lg bg-tertiary/15 text-tertiary border border-tertiary/30 font-label-mono-sm flex items-center gap-1.5 font-bold shadow-sm">
              <AlertTriangle className="w-4 h-4 text-tertiary" />
              <span>Safety Gate Held</span>
            </span>
          )}
          {isInvalid && (
            <span className="px-3 py-1.5 rounded-lg bg-error-container/20 text-error border border-error/30 font-label-mono-sm flex items-center gap-1.5 font-bold shadow-sm">
              <XCircle className="w-4 h-4 text-error" />
              <span>Rejected Invalid</span>
            </span>
          )}
        </div>
      </div>

      {/* Candidate Action Space Distribution Matrix (Stitch 5-Box Grid) */}
      <div className="flex flex-col space-y-2">
        <span className="font-label-mono-sm uppercase text-outline">
          Candidate Action Space Distribution
        </span>
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-2">
          {ACTION_OPTIONS.map((action) => {
            const isSelected = action === decision.decision;
            const prob = decision.probabilities?.[action] ?? 0;
            const pct = Math.round(prob * 1000) / 10;

            return (
              <div
                key={action}
                className={`p-2.5 rounded-lg border transition-all flex flex-col justify-between ${
                  isSelected
                    ? 'bg-surface-container-highest border-primary/50 shadow-[inset_0_0_10px_rgba(78,222,163,0.15)]'
                    : 'bg-surface-container border-outline-variant/30 opacity-75 hover:opacity-100'
                }`}
              >
                <div className="flex items-center justify-between">
                  <span
                    className={`font-label-mono-sm truncate ${
                      isSelected ? 'font-bold text-primary' : 'text-on-surface'
                    }`}
                  >
                    {action}
                  </span>
                  {isSelected && <span className="w-1.5 h-1.5 rounded-full bg-primary animate-pulse" />}
                </div>

                <div className="mt-2">
                  <div className="w-full bg-surface-container-high rounded-full h-1.5 overflow-hidden">
                    <div
                      className={`h-1.5 rounded-full ${isSelected ? 'bg-primary' : 'bg-outline'}`}
                      style={{ width: `${Math.max(pct, 2)}%` }}
                    />
                  </div>
                  <div className="flex justify-between items-center mt-1 text-[10px] font-label-mono-sm">
                    <span className="text-outline">Prob</span>
                    <span className={isSelected ? 'text-primary font-bold' : 'text-on-surface-variant'}>
                      {pct}%
                    </span>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Recharts Detailed Distribution Chart */}
      <div className="space-y-2 pt-2 border-t border-outline-variant/20">
        <div className="flex items-center justify-between">
          <span className="font-label-mono-sm text-outline uppercase">
            Probability Distribution Spectrum
          </span>
          <span className="font-label-mono-sm text-on-surface-variant text-[11px]">
            Pointer Readout Softmax
          </span>
        </div>
        <div className="h-44 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              data={probData}
              layout="vertical"
              margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
            >
              <XAxis
                type="number"
                domain={[0, 100]}
                unit="%"
                stroke="#86948a"
                tick={{ fill: '#86948a', fontSize: 10, fontFamily: 'JetBrains Mono' }}
              />
              <YAxis
                type="category"
                dataKey="action"
                width={140}
                stroke="#86948a"
                tick={{ fill: '#dde3ed', fontSize: 10, fontFamily: 'JetBrains Mono' }}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#161c23',
                  borderColor: '#3c4a42',
                  borderRadius: '0.375rem',
                  color: '#dde3ed',
                  fontFamily: 'JetBrains Mono',
                  fontSize: '11px',
                }}
                formatter={(value: any) => [`${value}%`, 'Softmax Probability']}
              />
              <Bar dataKey="probability" radius={[0, 4, 4, 0]}>
                {probData.map((entry, index) => (
                  <Cell
                    key={`cell-${index}`}
                    fill={entry.isSelected ? '#4edea3' : '#343a41'}
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
};
