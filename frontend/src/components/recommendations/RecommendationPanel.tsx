import React from 'react';
import {
  Sparkles,
  ArrowRightCircle,
  FileCheck2,
  AlertTriangle,
  ClipboardList,
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
    <div className="bg-[#161c28] border border-[#242d3d] rounded-xl p-5 shadow-sm space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-[#242d3d]/60 pb-3">
        <div className="flex items-center space-x-2.5">
          <div className="p-2 rounded-lg bg-amber-500/10 border border-amber-500/30 text-amber-400">
            <Sparkles className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-base font-bold text-slate-100 flex items-center space-x-2">
              <span>Amazon Bedrock Generative Reasoning</span>
            </h3>
            <p className="text-xs text-slate-400 mt-0.5">
              Evidence-grounded recommendation synthesized from actual Decider selection and tool telemetry.
            </p>
          </div>
        </div>

        {/* Live vs Dev Mode Status Badge */}
        <div>
          {isLive ? (
            <div className="flex items-center space-x-1.5 px-3 py-1 rounded-full bg-emerald-500/15 border border-emerald-500/30 text-emerald-300 text-xs font-semibold">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              <span>LIVE BEDROCK ({recommendation.model_id})</span>
            </div>
          ) : (
            <div className="flex items-center space-x-1.5 px-3 py-1 rounded-full bg-amber-500/15 border border-amber-500/30 text-amber-300 text-xs font-semibold">
              <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
              <span>DEV MODE FALLBACK</span>
            </div>
          )}
        </div>
      </div>

      {/* Dev Mode Banner Notice */}
      {!isLive && (
        <div className="p-3 rounded-lg bg-amber-500/10 border border-amber-500/30 text-xs text-amber-200/90 leading-relaxed flex items-start space-x-2.5">
          <ShieldAlert className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
          <div>
            <strong className="font-semibold text-amber-300">AWS Integration Notice:</strong> AWS
            credentials or Amazon Bedrock model access are currently unconfigured in this environment.
            In compliance with the hackathon requirements, this recommendation is synthesized via a
            transparent deterministic fallback grounded directly in tool telemetry, rather than
            fabricating an unverified generative response.
          </div>
        </div>
      )}

      {/* Executive Summary */}
      <div className="p-4 rounded-lg bg-[#111620] border border-[#242d3d] space-y-1.5">
        <span className="text-xs font-semibold text-cyan-300">Executive Summary</span>
        <p className="text-xs text-slate-200 leading-relaxed font-sans">{recommendation.summary}</p>
      </div>

      {/* Recommended Next Step Box */}
      <div className="p-4 rounded-lg bg-emerald-500/10 border border-emerald-500/30 space-y-1.5">
        <div className="flex items-center space-x-2 text-emerald-400 text-xs font-bold">
          <ArrowRightCircle className="w-4 h-4" />
          <span>Recommended Next Action</span>
        </div>
        <p className="text-sm font-semibold text-emerald-200">{recommendation.recommended_next_step}</p>
      </div>

      {/* Supporting Evidence */}
      {recommendation.supporting_evidence?.length > 0 && (
        <div className="p-4 rounded-lg bg-[#111620] border border-[#242d3d] space-y-2">
          <span className="text-xs font-semibold text-slate-300 flex items-center space-x-1.5">
            <FileCheck2 className="w-3.5 h-3.5 text-cyan-400" />
            <span>Empirical Evidence Cited from Tool Results</span>
          </span>
          <ul className="space-y-1.5 text-xs text-slate-300">
            {recommendation.supporting_evidence.map((ev, i) => (
              <li key={i} className="flex items-start space-x-2">
                <span className="text-cyan-400 font-bold shrink-0">&bull;</span>
                <span>{ev}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Assumptions & Limitations Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
        <div className="p-3.5 rounded-lg bg-[#111620] border border-[#242d3d] space-y-1.5">
          <span className="font-semibold text-slate-300">Transparent Assumptions:</span>
          <ul className="list-disc list-inside space-y-1 text-slate-400 text-[11px]">
            {recommendation.assumptions?.map((item, i) => (
              <li key={i}>{item}</li>
            ))}
          </ul>
        </div>

        <div className="p-3.5 rounded-lg bg-[#111620] border border-[#242d3d] space-y-1.5">
          <span className="font-semibold text-slate-300">Known Limitations & Constraints:</span>
          <ul className="list-disc list-inside space-y-1 text-slate-400 text-[11px]">
            {recommendation.limitations?.map((item, i) => (
              <li key={i}>{item}</li>
            ))}
          </ul>
        </div>
      </div>

      {/* Follow-up Actions */}
      {recommendation.follow_up_actions?.length > 0 && (
        <div className="p-4 rounded-lg bg-[#111620] border border-[#242d3d] space-y-2">
          <span className="text-xs font-semibold text-slate-300 flex items-center space-x-1.5">
            <ClipboardList className="w-3.5 h-3.5 text-purple-400" />
            <span>Suggested Municipal Follow-Up Actions</span>
          </span>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
            {recommendation.follow_up_actions.map((act, i) => (
              <div
                key={i}
                className="p-2.5 rounded bg-[#0d121c] border border-[#242d3d] text-slate-300 flex items-start space-x-2"
              >
                <span className="font-mono text-purple-400 font-bold shrink-0">{i + 1}.</span>
                <span>{act}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
