import React from 'react';
import { Database, AlertTriangle, Zap, CheckCircle2, MapPin } from 'lucide-react';
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
  const lastLatency =
    mostRecent?.decision?.latency_ms !== undefined
      ? `${mostRecent.decision.latency_ms.toLocaleString()} ms`
      : 'Not yet measured';

  const cards = [
    {
      label: 'Monitored Sample Zones',
      value: `${totalLocations > 0 ? totalLocations : 4} Zones`,
      subtext: 'Synthetic demonstration hubs',
      badge: 'SYNTHETIC DEMO',
      badgeClass: 'bg-primary/10 text-primary border-primary/20',
      sparklineColor: 'text-primary',
      icon: <MapPin className="w-4 h-4 text-primary" />,
      sparklineD: 'M0 25 L15 22 L30 26 L45 18 L60 14 L75 16 L90 8 L100 5',
    },
    {
      label: 'Session Reports Analyzed',
      value: `${reportsCount} Processed`,
      subtext: reportsCount > 0 ? 'Evaluated in current session' : 'Awaiting user report intake',
      badge: reportsCount > 0 ? 'Active Session' : 'Idle',
      badgeClass: 'bg-secondary/10 text-secondary border-secondary/20',
      sparklineColor: 'text-secondary',
      icon: <CheckCircle2 className="w-4 h-4 text-secondary" />,
      sparklineD: 'M0 20 L20 18 L35 24 L55 12 L70 15 L85 6 L100 4',
    },
    {
      label: 'Decisions Requiring Clarification',
      value: `${clarificationCount} Gated`,
      subtext: 'Confidence < 60% policy threshold',
      badge: clarificationCount > 0 ? 'Human Review' : 'Zero Intercepts',
      badgeClass: clarificationCount > 0 ? 'bg-tertiary/15 text-tertiary border-tertiary/20' : 'bg-primary/10 text-primary border-primary/20',
      sparklineColor: 'text-tertiary',
      icon: <AlertTriangle className="w-4 h-4 text-tertiary" />,
      sparklineD: 'M0 15 L25 15 L35 20 L55 10 L75 14 L100 12',
    },
    {
      label: 'Most Recent Decision Latency',
      value: lastLatency,
      subtext: mostRecent ? 'Decider 2B CPU forward pass' : 'Run an analysis to measure',
      badge: mostRecent ? 'Measured' : 'Not Measured',
      badgeClass: 'bg-secondary/10 text-secondary border-secondary/20',
      sparklineColor: 'text-secondary',
      icon: <Zap className="w-4 h-4 text-secondary" />,
      sparklineD: 'M0 25 L20 22 L40 18 L60 12 L80 14 L100 7',
    },
  ];

  return (
    <div className="flex flex-col space-y-4">
      {/* Stitch Top Hero Section - Fully Responsive */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-3 pb-3 border-b border-outline-variant/30">
        <div>
          <div className="flex items-center gap-2 text-primary font-label-mono-sm uppercase tracking-widest text-xs flex-wrap">
            <span className="h-2 w-2 rounded-full bg-primary animate-ping"></span>
            <span>Tactical Environmental Resilience Telemetry</span>
            <span className="text-outline">/</span>
            <span className="text-secondary">Urban Decision Agent</span>
          </div>
          <h1 className="font-headline-lg text-on-surface tracking-tight mt-1 font-bold text-xl sm:text-2xl lg:text-3xl">
            Detect the heat. Decide the response. Protect the people.
          </h1>
        </div>
        <div className="text-left md:text-right">
          <p className="font-label-mono-sm text-on-surface-variant max-w-md text-xs leading-relaxed">
            Telemetry reflects demonstrator benchmark data and FastAPI Strands Decider 2B analytical pipeline.
          </p>
        </div>
      </div>

      {/* Synthetic Dataset Disclaimer Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 p-3 rounded-lg bg-surface-container-low border border-tertiary/30 text-xs">
        <div className="flex items-start sm:items-center gap-2.5 text-tertiary">
          <Database className="w-4 h-4 shrink-0 mt-0.5 sm:mt-0" />
          <span className="leading-relaxed">
            <strong className="font-semibold text-tertiary">Synthetic Data Disclaimer:</strong> All physical indicators (temperatures, NDVI canopy, pedestrian counts) are simulated benchmark samples (<code className="font-mono text-[11px] text-tertiary bg-surface-container-high px-1.5 py-0.5 rounded">SYNTHETIC_DEV_DATASET_V1</code>). No real-world physical sensors are connected.
          </span>
        </div>
        <span className="font-label-mono-sm text-outline shrink-0 text-[10px] hidden lg:inline">
          AWS Decider 2B Hackathon
        </span>
      </div>

      {/* 4 Reusable MetricCards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {cards.map((c, i) => (
          <div
            key={i}
            className="bg-surface-container-low/90 backdrop-blur-md p-4 rounded-xl border border-outline-variant/30 shadow-md hover:bg-surface-container transition-all flex flex-col justify-between"
          >
            <div className="flex items-start justify-between gap-2">
              <div className="flex flex-col min-w-0">
                <span className="font-label-mono-sm uppercase text-outline text-[11px] truncate">{c.label}</span>
                <span className="font-telemetry-value text-on-surface mt-1 text-xl sm:text-2xl truncate">{c.value}</span>
              </div>
              <span className={`px-2 py-0.5 rounded border ${c.badgeClass} font-label-mono-sm text-[10px] shrink-0 flex items-center gap-1`}>
                <span className="w-1.5 h-1.5 rounded-full bg-current"></span>
                <span>{c.badge}</span>
              </span>
            </div>

            <div className="mt-4 flex items-end justify-between pt-2 border-t border-outline-variant/20 gap-2">
              <span className="font-body-sm text-on-surface-variant text-[11px] truncate">{c.subtext}</span>
              <div className="w-16 h-5 shrink-0">
                <svg className={`w-full h-full ${c.sparklineColor}`} fill="none" preserveAspectRatio="none" viewBox="0 0 100 30">
                  <path
                    d={c.sparklineD}
                    stroke="currentColor"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth="2.5"
                  />
                  <path
                    d={`${c.sparklineD} L100 30 L0 30 Z`}
                    fill="currentColor"
                    fillOpacity="0.12"
                  />
                </svg>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
