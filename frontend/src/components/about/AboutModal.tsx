import React from 'react';
import { Cpu, Cloud, ShieldCheck, Layers } from 'lucide-react';

export const AboutView: React.FC = () => {
  return (
    <div className="space-y-6 max-w-4xl">
      {/* Intro Hero */}
      <div className="p-6 rounded-xl bg-surface-container-low/90 backdrop-blur-md border border-outline-variant/30 space-y-3 shadow-lg">
        <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded-full bg-secondary/10 border border-secondary/30 text-secondary font-label-mono-sm font-semibold">
          <Layers className="w-3.5 h-3.5" />
          <span>AWS Strands Decider 2B Agent Experience Hackathon</span>
        </div>
        <h3 className="font-headline-sm text-xl font-bold text-on-surface">
          Architecture: System 1 Decision Model + System 2 Generative Reasoner
        </h3>
        <p className="font-body-md text-on-surface-variant leading-relaxed">
          HeatShield AI combines high-speed, calibrated decision routing via <strong>Strands Decider 2B</strong> with
          evidence-grounded municipal synthesis via <strong>Amazon Bedrock</strong>. It solves the critical latency,
          hallucination, and confidence-calibration vulnerabilities of traditional agentic LLM routing.
        </p>
      </div>

      {/* Dual Engine Comparison */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Strands Decider 2B Card */}
        <div className="p-5 rounded-xl bg-surface-container-low/90 backdrop-blur-md border border-primary/30 space-y-3 flex flex-col justify-between shadow-md">
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-primary">
              <Cpu className="w-5 h-5" />
              <h4 className="font-headline-sm font-bold text-sm text-on-surface">Strands Decider 2B</h4>
            </div>
            <p className="font-label-mono-sm text-primary font-bold">Deterministic Tool Selection ("System 1")</p>
            <ul className="space-y-1.5 font-body-sm text-on-surface-variant pt-1">
              <li className="flex items-start gap-2">
                <span className="text-primary font-bold">&bull;</span>
                <span>Specialized 2B parameter torso with a pointer readout head.</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-primary font-bold">&bull;</span>
                <span>Single causal forward pass without slow autoregressive token generation.</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-primary font-bold">&bull;</span>
                <span>Calibrated confidence formula: <code className="font-mono text-primary bg-surface-container px-1 py-0.5 rounded">(N*p_max - 1)/(N - 1)</code>.</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-primary font-bold">&bull;</span>
                <span>Picks from 5 predefined typed actions: ANALYZE_HEAT, CHECK_VEGETATION, CHECK_EXPOSURE, COMPARE_INTERVENTIONS, REQUEST_MORE_DATA.</span>
              </li>
            </ul>
          </div>
          <div className="pt-3 border-t border-outline-variant/20 font-label-mono-sm text-primary font-mono">
            Model: StrandsAgents/strands-decider-2B-hobson-v21
          </div>
        </div>

        {/* Amazon Bedrock Card */}
        <div className="p-5 rounded-xl bg-surface-container-low/90 backdrop-blur-md border border-tertiary/30 space-y-3 flex flex-col justify-between shadow-md">
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-tertiary">
              <Cloud className="w-5 h-5" />
              <h4 className="font-headline-sm font-bold text-sm text-on-surface">Amazon Bedrock</h4>
            </div>
            <p className="font-label-mono-sm text-tertiary font-bold">Evidence-Based Generative Reasoning ("System 2")</p>
            <ul className="space-y-1.5 font-body-sm text-on-surface-variant pt-1">
              <li className="flex items-start gap-2">
                <span className="text-tertiary font-bold">&bull;</span>
                <span>Executes only after Decider choice passes the confidence safety gate.</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-tertiary font-bold">&bull;</span>
                <span>Strictly grounded in actual tool telemetry; cannot replace Decider choice.</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-tertiary font-bold">&bull;</span>
                <span>Enforces transparent disclosure of data provenance, assumptions, and limitations.</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-tertiary font-bold">&bull;</span>
                <span>Seamless IAM role authentication in AWS EC2 deployment.</span>
              </li>
            </ul>
          </div>
          <div className="pt-3 border-t border-outline-variant/20 font-label-mono-sm text-tertiary font-mono">
            Model: Amazon Nova 2 Lite (global.amazon.nova-2-lite-v1:0)
          </div>
        </div>
      </div>

      {/* Safety Gate & Invariants */}
      <div className="p-5 rounded-xl bg-surface-container-low/90 backdrop-blur-md border border-outline-variant/30 space-y-3 shadow-md">
        <div className="flex items-center gap-2 text-primary">
          <ShieldCheck className="w-5 h-5" />
          <h4 className="font-headline-sm font-bold text-sm text-on-surface">
            Core Safety Invariant: Confidence Gating
          </h4>
        </div>
        <p className="font-body-md text-on-surface-variant leading-relaxed">
          Autonomous environmental agents must not execute high-impact actions under unverified uncertainty.
          HeatShield AI enforces a configurable confidence gate (default <strong>60.0%</strong>):
        </p>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-1 text-xs">
          <div className="p-3 rounded-lg bg-surface-container border border-primary/30 space-y-1">
            <span className="font-label-mono-sm text-primary font-bold">1. ACCEPTED (≥60%)</span>
            <p className="text-[11px] text-on-surface-variant">Action executed immediately via deterministic Python tool.</p>
          </div>
          <div className="p-3 rounded-lg bg-surface-container border border-tertiary/30 space-y-1">
            <span className="font-label-mono-sm text-tertiary font-bold">2. GATED (&lt;60%)</span>
            <p className="text-[11px] text-on-surface-variant">Execution blocked. Tool withheld; clarification request generated.</p>
          </div>
          <div className="p-3 rounded-lg bg-surface-container border border-error/30 space-y-1">
            <span className="font-label-mono-sm text-error font-bold">3. REJECTED</span>
            <p className="text-[11px] text-on-surface-variant">Unrecognized or malformed choice safely trapped; fallback triggered.</p>
          </div>
        </div>
      </div>
    </div>
  );
};
