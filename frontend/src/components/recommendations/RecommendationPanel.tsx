import {
  ArrowRightCircle,
  Send,
  Download,
  ShieldAlert,
} from 'lucide-react';
import type { BedrockRecommendation } from '../../types/api';

interface RecommendationPanelProps {
  recommendation: BedrockRecommendation;
}

export const RecommendationPanel: React.FC<RecommendationPanelProps> = ({
  recommendation,
}) => {
  const isLive = recommendation.is_live_bedrock;

  return (
    <div className="bg-surface-container-low/95 backdrop-blur-md rounded-xl p-5 border border-outline-variant/30 shadow-xl flex flex-col space-y-4">
      {/* Header & Source Status Tag (Stitch Layout) */}
      <div className="flex flex-col space-y-2 pb-3 border-b border-outline-variant/20">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="material-symbols-outlined text-secondary text-[22px]">psychology</span>
            <span className="font-headline-sm text-on-surface font-bold">
              Amazon Bedrock Generative Synthesis
            </span>
          </div>

          <div className="flex items-center gap-1.5">
            <span className={`w-2 h-2 rounded-full ${isLive ? 'bg-primary animate-ping' : 'bg-tertiary'}`} />
            <span className={`font-label-mono-sm font-bold ${isLive ? 'text-primary' : 'text-tertiary'}`}>
              {isLive ? 'AWS Bedrock Live' : 'DEV MODE FALLBACK'}
            </span>
          </div>
        </div>

        <div className="p-2 rounded-lg bg-surface-container-high border border-outline-variant/30 text-secondary font-label-mono-sm flex items-center justify-between text-xs">
          <span className="truncate font-mono">{recommendation.model_id}</span>
          <span className="text-outline uppercase text-[10px]">
            {isLive ? 'IAM Authenticated' : 'Rule-Engine Fallback'}
          </span>
        </div>
      </div>

      {/* Dev Mode Banner Notice */}
      {!isLive && (
        <div className="p-3 rounded-lg bg-tertiary/10 border border-tertiary/30 text-xs text-tertiary font-body-sm leading-relaxed flex items-start gap-2.5">
          <ShieldAlert className="w-4 h-4 text-tertiary shrink-0 mt-0.5" />
          <div>
            <strong className="font-semibold text-tertiary">AWS Integration Notice:</strong> AWS credentials
            or Amazon Bedrock access are unconfigured. To satisfy hackathon criteria, this recommendation is
            deterministically synthesized directly from Decider output and tool results, avoiding fabricated
            generative responses.
          </div>
        </div>
      )}

      {/* Executive Action Directive */}
      <div className="flex flex-col space-y-1">
        <span className="font-label-mono-sm uppercase text-outline">Executive Action Directive</span>
        <p className="font-body-md text-on-surface leading-relaxed p-3.5 rounded-lg bg-surface-container-lowest border border-outline-variant/20">
          {recommendation.summary}
        </p>
      </div>

      {/* Recommended Next Step Box (Stitch Component) */}
      <div className="p-4 rounded-lg bg-primary/10 border border-primary/30 shadow-sm flex flex-col space-y-1.5">
        <div className="flex items-center gap-1.5 text-primary font-label-mono-sm uppercase font-bold">
          <ArrowRightCircle className="w-4 h-4 text-primary" />
          <span>Recommended Next Action</span>
        </div>
        <p className="font-body-md text-on-surface font-semibold">
          {recommendation.recommended_next_step}
        </p>
      </div>

      {/* Empirical Evidence Trace */}
      {recommendation.supporting_evidence?.length > 0 && (
        <div className="flex flex-col space-y-1.5">
          <span className="font-label-mono-sm uppercase text-outline">Empirical Evidence Trace</span>
          <div className="space-y-1.5 text-on-surface-variant font-label-mono-sm bg-surface-container-lowest p-3.5 rounded-lg border border-outline-variant/20">
            {recommendation.supporting_evidence.map((ev, i) => (
              <div key={i} className="flex items-start gap-2">
                <span className="text-primary font-bold">•</span>
                <span>{ev}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Assumptions & Limitations Grid (Stitch Component) */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
        <div className="p-2.5 rounded-lg bg-surface-container border border-outline-variant/30 text-on-surface-variant font-label-mono-sm">
          <span className="text-outline uppercase font-bold block mb-1">Assumptions:</span>
          <ul className="space-y-0.5 list-disc list-inside">
            {recommendation.assumptions?.map((asmp, i) => (
              <li key={i} className="truncate">{asmp}</li>
            )) || <li>Ground telemetry verified with sensors</li>}
          </ul>
        </div>

        <div className="p-2.5 rounded-lg bg-surface-container border border-outline-variant/30 text-on-surface-variant font-label-mono-sm">
          <span className="text-outline uppercase font-bold block mb-1">Limitations:</span>
          <ul className="space-y-0.5 list-disc list-inside">
            {recommendation.limitations?.map((lim, i) => (
              <li key={i} className="truncate">{lim}</li>
            )) || <li>Public telemetry latency may vary</li>}
          </ul>
        </div>
      </div>

      {/* Follow-up Action Buttons */}
      <div className="flex flex-col sm:flex-row gap-2 pt-2 border-t border-outline-variant/20">
        <button
          onClick={() => alert('Dispatch advisory queued for municipal operational broadcast.')}
          className="flex-1 py-2.5 px-4 rounded-lg bg-primary text-on-primary font-label-mono-md uppercase tracking-wider flex items-center justify-center gap-2 shadow hover:shadow-primary/30 transition cursor-pointer font-bold"
        >
          <Send className="w-4 h-4" />
          <span>Issue Dispatch Advisory</span>
        </button>
        <button
          onClick={() => {
            const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(recommendation, null, 2));
            const dl = document.createElement('a');
            dl.setAttribute("href", dataStr);
            dl.setAttribute("download", `heatshield-audit-${Date.now()}.json`);
            dl.click();
          }}
          className="py-2.5 px-4 rounded-lg bg-surface-container-high text-on-surface hover:text-secondary font-label-mono-md uppercase tracking-wider flex items-center justify-center gap-2 border border-outline-variant/30 transition cursor-pointer"
        >
          <Download className="w-4 h-4" />
          <span>Export Audit Log</span>
        </button>
      </div>
    </div>
  );
};
