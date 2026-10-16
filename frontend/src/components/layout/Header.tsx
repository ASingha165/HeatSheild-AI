import React, { useState, useEffect } from 'react';
import { Cpu, Cloud, Wifi, RefreshCw, Clock, Menu } from 'lucide-react';
import type { HealthResponse, SystemConfigResponse } from '../../types/api';

interface HeaderProps {
  title: string;
  subtitle: string;
  health: HealthResponse | null;
  config: SystemConfigResponse | null;
  apiLatencyMs: number | null;
  isLoading: boolean;
  onRefresh: () => void;
  onOpenMobileNav?: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  title,
  subtitle,
  health,
  config,
  apiLatencyMs,
  isLoading,
  onRefresh,
  onOpenMobileNav,
}) => {
  const isApiOnline = health !== null && health.status === 'healthy';
  const isDeciderLoaded = config?.decider.is_engine_loaded || health?.decider_status === 'ready';
  const isBedrockConfigured = config?.bedrock.is_configured;

  const [utcTime, setUtcTime] = useState<string>('');

  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      setUtcTime(now.toTimeString().split(' ')[0] + ' UTC');
    };
    updateTime();
    const interval = setInterval(updateTime, 1000);
    return () => clearInterval(interval);
  }, []);

  return (
    <header className="min-h-16 sm:h-20 bg-surface-container-lowest/85 backdrop-blur-xl border-b border-outline-variant/30 shadow-[0_1px_8px_rgba(0,0,0,0.25)] flex items-center justify-between px-4 sm:px-6 py-2.5 shrink-0 z-30 sticky top-0">
      {/* Left: Mobile Nav Toggle + Title Banner */}
      <div className="flex items-center gap-3 min-w-0 mr-2">
        {onOpenMobileNav && (
          <button
            type="button"
            onClick={onOpenMobileNav}
            className="lg:hidden p-2 rounded-lg bg-surface-container-high border border-outline-variant/30 text-on-surface hover:text-primary transition-colors cursor-pointer shrink-0"
            aria-label="Open navigation menu"
          >
            <Menu className="w-5 h-5" />
          </button>
        )}

        <div className="flex flex-col min-w-0">
          <h1 className="font-headline-sm text-on-surface font-bold text-sm sm:text-base lg:text-lg tracking-tight truncate">
            {title}
          </h1>
          <div className="flex items-center gap-2 text-on-surface-variant font-label-mono-sm text-[11px] mt-0.5 flex-wrap">
            <span className="flex items-center gap-1 text-secondary shrink-0">
              <span className="w-1.5 h-1.5 rounded-full bg-secondary animate-pulse" />
              <span>LIVE TELEMETRY</span>
            </span>
            <span className="text-outline hidden xs:inline">•</span>
            <span className="hidden xs:flex items-center gap-1 text-on-surface-variant shrink-0">
              <Clock className="w-3 h-3 text-outline" />
              <span>{utcTime || 'LIVE'}</span>
            </span>
            <span className="text-outline hidden md:inline">•</span>
            <span className="text-outline hidden md:inline truncate max-w-xs">{subtitle}</span>
          </div>
        </div>
      </div>

      {/* Right: Subsystem Telemetry Status Badges */}
      <div className="flex items-center gap-2 shrink-0">
        {/* Strands Decider 2B Status */}
        <div
          title={config?.decider.checkpoint || 'StrandsAgents/strands-decider-2B-hobson-v21'}
          className="hidden sm:flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-surface-container-high border border-outline-variant/30 text-xs"
        >
          <span
            className={`w-2 h-2 rounded-full ${isDeciderLoaded ? 'bg-primary animate-ping' : 'bg-secondary'}`}
          />
          <Cpu className="w-3.5 h-3.5 text-secondary" />
          <span className="font-label-mono-sm text-on-surface-variant hidden xl:inline">Decider 2B:</span>
          <span className="font-label-mono-sm font-bold text-primary text-[11px]">
            {isDeciderLoaded ? 'Ready' : 'Standby'}
          </span>
        </div>

        {/* Amazon Bedrock Status */}
        <div
          title={config?.bedrock.status_message || 'AWS Bedrock configuration status'}
          className="hidden md:flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-surface-container-high border border-outline-variant/30 text-xs"
        >
          <Cloud className={`w-3.5 h-3.5 ${isBedrockConfigured ? 'text-primary' : 'text-tertiary'}`} />
          <span className="font-label-mono-sm text-on-surface-variant hidden xl:inline">Bedrock:</span>
          <span
            className={`font-label-mono-sm font-bold text-[11px] ${
              isBedrockConfigured ? 'text-primary' : 'text-tertiary'
            }`}
          >
            {isBedrockConfigured ? `Live IAM (${config.bedrock.region})` : 'Dev Mode (Fallback)'}
          </span>
        </div>

        {/* FastAPI Connectivity with Real Measured Roundtrip Latency */}
        <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-surface-container-high border border-outline-variant/30 text-xs">
          <Wifi className={`w-3.5 h-3.5 ${isApiOnline ? 'text-primary' : 'text-error'}`} />
          <span
            className={`font-label-mono-sm font-semibold text-[11px] ${
              isApiOnline ? 'text-primary' : 'text-error'
            }`}
          >
            {isApiOnline
              ? `API ${apiLatencyMs !== null ? `${apiLatencyMs}ms` : 'Online'}`
              : 'Connecting...'}
          </span>
        </div>

        {/* Manual Telemetry Refresh Trigger */}
        <button
          type="button"
          onClick={onRefresh}
          disabled={isLoading}
          title="Refresh Subsystem Telemetry"
          className="p-1.5 sm:p-2 rounded-lg bg-surface-container-high border border-outline-variant/30 hover:bg-surface-container-highest text-on-surface-variant hover:text-on-surface transition-colors disabled:opacity-50 cursor-pointer shrink-0"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin text-secondary' : ''}`} />
        </button>
      </div>
    </header>
  );
};
