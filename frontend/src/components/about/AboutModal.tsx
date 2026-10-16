import React from 'react';
import { Cpu, Cloud, ShieldCheck, Layers } from 'lucide-react';

export const AboutView: React.FC = () => {
  return (
    <div className="space-y-6 max-w-4xl">
      {/* Intro Hero */}
      <div className="p-6 rounded-xl bg-[#161c28] border border-[#242d3d] space-y-3">
        <div className="inline-flex items-center space-x-2 px-2.5 py-1 rounded-full bg-cyan-500/10 border border-cyan-500/30 text-cyan-300 text-xs font-semibold">
          <Layers className="w-3.5 h-3.5" />
          <span>AWS Strands Decider 2B Agent Experience Hackathon</span>
        </div>
        <h3 className="text-xl font-bold text-slate-100">
          Architecture: System 1 Decision Model + System 2 Generative Reasoner
        </h3>
        <p className="text-xs text-slate-300 leading-relaxed">
          HeatShield AI combines high-speed, calibrated decision routing via <strong>Strands Decider 2B</strong> with
          evidence-grounded municipal synthesis via <strong>Amazon Bedrock</strong>. It solves the critical latency,
          hallucination, and confidence-calibration vulnerabilities of traditional agentic LLM routing.
        </p>
      </div>

      {/* Dual Engine Comparison */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Strands Decider 2B Card */}
        <div className="p-5 rounded-xl bg-[#161c28] border border-cyan-500/30 space-y-3 flex flex-col justify-between">
          <div className="space-y-2">
            <div className="flex items-center space-x-2 text-cyan-400">
              <Cpu className="w-5 h-5" />
              <h4 className="font-bold text-sm text-slate-100">Strands Decider 2B</h4>
            </div>
            <p className="text-xs text-slate-400 font-medium">Deterministic Tool Selection ("System 1")</p>
            <ul className="space-y-1.5 text-xs text-slate-300 pt-1">
              <li className="flex items-start space-x-2">
                <span className="text-cyan-400 font-bold">&bull;</span>
                <span>Specialized 2B parameter torso with a pointer readout head.</span>
              </li>
              <li className="flex items-start space-x-2">
                <span className="text-cyan-400 font-bold">&bull;</span>
                <span>Single causal forward pass without slow autoregressive token generation.</span>
              </li>
              <li className="flex items-start space-x-2">
                <span className="text-cyan-400 font-bold">&bull;</span>
                <span>Calibrated confidence formula: <code className="font-mono text-cyan-300">(N*p_max - 1)/(N - 1)</code>.</span>
              </li>
              <li className="flex items-start space-x-2">
                <span className="text-cyan-400 font-bold">&bull;</span>
                <span>Picks from 5 predefined typed actions: ANALYZE_HEAT, CHECK_VEGETATION, CHECK_EXPOSURE, COMPARE_INTERVENTIONS, REQUEST_MORE_DATA.</span>
              </li>
            </ul>
          </div>
          <div className="pt-3 border-t border-[#242d3d] text-[11px] text-cyan-300 font-mono">
            Model: StrandsAgents/strands-decider-2B-hobson-v21
          </div>
        </div>

        {/* Amazon Bedrock Card */}
        <div className="p-5 rounded-xl bg-[#161c28] border border-amber-500/30 space-y-3 flex flex-col justify-between">
          <div className="space-y-2">
            <div className="flex items-center space-x-2 text-amber-400">
              <Cloud className="w-5 h-5" />
              <h4 className="font-bold text-sm text-slate-100">Amazon Bedrock</h4>
            </div>
            <p className="text-xs text-slate-400 font-medium">Evidence-Based Generative Reasoning ("System 2")</p>
            <ul className="space-y-1.5 text-xs text-slate-300 pt-1">
              <li className="flex items-start space-x-2">
                <span className="text-amber-400 font-bold">&bull;</span>
                <span>Executes only after Decider choice passes the confidence safety gate.</span>
              </li>
              <li className="flex items-start space-x-2">
                <span className="text-amber-400 font-bold">&bull;</span>
                <span>Strictly grounded in actual tool telemetry; cannot replace Decider choice.</span>
              </li>
              <li className="flex items-start space-x-2">
                <span className="text-amber-400 font-bold">&bull;</span>
                <span>Enforces transparent disclosure of data provenance, assumptions, and limitations.</span>
              </li>
              <li className="flex items-start space-x-2">
                <span className="text-amber-400 font-bold">&bull;</span>
                <span>Seamless IAM role authentication in AWS EC2 deployment.</span>
              </li>
            </ul>
          </div>
          <div className="pt-3 border-t border-[#242d3d] text-[11px] text-amber-300 font-mono">
            Model: anthropic.claude-3-haiku-20240307-v1:0
          </div>
        </div>
      </div>

      {/* Safety Gate & Invariants */}
      <div className="p-5 rounded-xl bg-[#161c28] border border-[#242d3d] space-y-3">
        <div className="flex items-center space-x-2 text-emerald-400">
          <ShieldCheck className="w-5 h-5" />
          <h4 className="font-bold text-sm text-slate-100">Core Safety Invariant: Confidence Gating</h4>
        </div>
        <p className="text-xs text-slate-300 leading-relaxed">
          Autonomous environmental agents must not execute high-impact actions under unverified uncertainty.
          HeatShield AI enforces a configurable confidence gate (default <strong>60.0%</strong>):
        </p>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5 pt-1 text-xs">
          <div className="p-3 rounded-lg bg-[#111620] border border-emerald-500/30">
            <span className="font-bold text-emerald-400 font-mono">C &ge; Threshold</span>
            <p className="text-slate-400 text-[11px] mt-1">
              Gate: <code className="text-emerald-300 font-mono">PROCEED_TO_TOOL</code>. Automated analytical tool execution proceeds.
            </p>
          </div>
          <div className="p-3 rounded-lg bg-[#111620] border border-amber-500/30">
            <span className="font-bold text-amber-400 font-mono">C &lt; Threshold</span>
            <p className="text-slate-400 text-[11px] mt-1">
              Gate: <code className="text-amber-300 font-mono">REQUEST_HUMAN_CLARIFICATION</code>. Tool execution is blocked; human review requested.
            </p>
          </div>
          <div className="p-3 rounded-lg bg-[#111620] border border-rose-500/30">
            <span className="font-bold text-rose-400 font-mono">Invalid Choice</span>
            <p className="text-slate-400 text-[11px] mt-1">
              Gate: <code className="text-rose-300 font-mono">REJECT_INVALID_CHOICE</code>. Disallowed actions rejected by schema validator.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
