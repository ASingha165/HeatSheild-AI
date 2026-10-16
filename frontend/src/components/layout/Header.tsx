import React from 'react';
import { Cpu, Cloud, Wifi, RefreshCw } from 'lucide-react';
import type { HealthResponse, SystemConfigResponse } from '../../types/api';

interface HeaderProps {
  title: string;
  subtitle: string;
  health: HealthResponse | null;
  config: SystemConfigResponse | null;
  isLoading: boolean;
  onRefresh: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  title,
  subtitle,
  health,
  config,
  isLoading,
  onRefresh,
}) => {
  const isApiOnline = health !== null && health.status === 'healthy';
  const isDeciderReady = health?.decider_status === 'ready' || config?.decider.is_engine_loaded;
  const isBedrockConfigured = config?.bedrock.is_configured;

  return (
    <header className="h-20 bg-[#111620] border-b border-[#242d3d] px-6 flex items-center justify-between shrink-0">
      {/* Title */}
      <div>
        <h2 className="text-xl font-bold text-slate-100 tracking-tight">{title}</h2>
        <p className="text-xs text-slate-400 mt-0.5">{subtitle}</p>
      </div>

      {/* Subsystem Status Indicators */}
      <div className="flex items-center space-x-3">
        {/* Strands Decider Subsystem */}
        <div className="flex items-center space-x-2 px-3 py-1.5 rounded-lg bg-[#161c28] border border-[#242d3d] text-xs">
          <Cpu className={`w-3.5 h-3.5 ${isDeciderReady ? 'text-cyan-400' : 'text-amber-400'}`} />
          <span className="text-slate-400">Decider 2B:</span>
          <span className="font-semibold text-slate-200">
            {config?.decider.checkpoint ? 'hobson-v21 (Active)' : isDeciderReady ? 'Ready' : 'Standby'}
          </span>
          <span
            className={`w-2 h-2 rounded-full ${isDeciderReady ? 'bg-cyan-400 animate-pulse' : 'bg-amber-400'}`}
          />
        </div>

        {/* Amazon Bedrock Subsystem */}
        <div className="flex items-center space-x-2 px-3 py-1.5 rounded-lg bg-[#161c28] border border-[#242d3d] text-xs">
          <Cloud className={`w-3.5 h-3.5 ${isBedrockConfigured ? 'text-emerald-400' : 'text-amber-400'}`} />
          <span className="text-slate-400">Bedrock:</span>
          <span className="font-semibold text-slate-200">
            {isBedrockConfigured ? 'Live IAM' : 'Dev Mode (Fallback)'}
          </span>
          <span
            className={`w-2 h-2 rounded-full ${isBedrockConfigured ? 'bg-emerald-400' : 'bg-amber-400'}`}
          />
        </div>

        {/* API Ping & Refresh Button */}
        <div className="flex items-center space-x-2 px-3 py-1.5 rounded-lg bg-[#161c28] border border-[#242d3d] text-xs">
          <Wifi className={`w-3.5 h-3.5 ${isApiOnline ? 'text-emerald-400' : 'text-rose-400'}`} />
          <span className="font-medium text-slate-200">
            {isApiOnline ? 'API Connected' : 'Connecting...'}
          </span>
        </div>

        <button
          onClick={onRefresh}
          disabled={isLoading}
          title="Refresh Backend Subsystems"
          className="p-2 rounded-lg bg-[#161c28] border border-[#242d3d] hover:bg-[#1c2433] text-slate-400 hover:text-slate-200 transition-colors disabled:opacity-50"
        >
          <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin text-cyan-400' : ''}`} />
        </button>
      </div>
    </header>
  );
};
