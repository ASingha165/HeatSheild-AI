import React from 'react';
import {
  Activity,
  MapPin,
  FileText,
  History,
  Info,
  Shield,
  Layers,
  X,
} from 'lucide-react';
import type { HealthResponse, SystemConfigResponse } from '../../types/api';

export type NavTab = 'overview' | 'map' | 'analyze' | 'history' | 'about';

interface SidebarProps {
  activeTab: NavTab;
  onSelectTab: (tab: NavTab) => void;
  reportCount: number;
  isOpenMobile?: boolean;
  onCloseMobile?: () => void;
  health: HealthResponse | null;
  config: SystemConfigResponse | null;
  locationsCount: number;
}

export const Sidebar: React.FC<SidebarProps> = ({
  activeTab,
  onSelectTab,
  reportCount,
  isOpenMobile = false,
  onCloseMobile,
  health,
  config,
  locationsCount,
}) => {
  const navItems: Array<{ id: NavTab; label: string; icon: React.ReactNode; badge?: number }> = [
    { id: 'overview', label: 'Overview', icon: <Activity className="w-4 h-4" /> },
    { id: 'map', label: 'Environmental Map', icon: <MapPin className="w-4 h-4" /> },
    { id: 'analyze', label: 'Analyze Report', icon: <FileText className="w-4 h-4" /> },
    {
      id: 'history',
      label: 'Decision History',
      icon: <History className="w-4 h-4" />,
      badge: reportCount > 0 ? reportCount : undefined,
    },
    { id: 'about', label: 'Decider Architecture', icon: <Info className="w-4 h-4" /> },
  ];

  const isDeciderLoaded = config?.decider.is_engine_loaded || health?.decider_status === 'ready';
  const isBedrockLive = config?.bedrock.is_configured;

  const handleNavClick = (tab: NavTab) => {
    onSelectTab(tab);
    onCloseMobile?.();
  };

  const sidebarContent = (
    <aside className="h-full w-64 xl:w-72 bg-surface-container-lowest/98 backdrop-blur-xl flex flex-col justify-between border-r border-outline-variant/30 shadow-[0_1px_8px_rgba(0,0,0,0.3)]">
      <div className="flex flex-col">
        {/* Brand Header */}
        <div className="px-5 py-4 flex items-center justify-between bg-surface-container-low/40 border-b border-outline-variant/20">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-primary-container/20 border border-primary/30 flex items-center justify-center text-primary shrink-0 glow-primary">
              <Shield className="w-5 h-5 text-primary" />
            </div>
            <div className="flex flex-col min-w-0">
              <span className="font-headline-sm text-on-surface tracking-tight truncate font-bold text-base">
                HeatShield AI
              </span>
              <span className="font-label-mono-sm uppercase text-secondary tracking-wider truncate text-[10px]">
                Detect • Decide • Protect
              </span>
            </div>
          </div>
          {/* Mobile close button */}
          {onCloseMobile && (
            <button
              type="button"
              onClick={onCloseMobile}
              className="lg:hidden p-1.5 rounded-lg text-outline hover:text-on-surface hover:bg-surface-container-high cursor-pointer"
              aria-label="Close navigation"
            >
              <X className="w-5 h-5" />
            </button>
          )}
        </div>

        {/* Section Label */}
        <div className="px-4 pt-4 pb-2">
          <span className="font-label-mono-sm text-outline uppercase tracking-widest px-2 text-[10px]">
            Operations Deck
          </span>
        </div>

        {/* Navigation Items */}
        <nav className="flex flex-col px-3 gap-1">
          {navItems.map((item) => {
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                type="button"
                onClick={() => handleNavClick(item.id)}
                className={`flex items-center justify-between px-3.5 py-2.5 rounded-lg transition-all text-left cursor-pointer ${
                  isActive
                    ? 'bg-surface-container-high text-primary font-title-md shadow-[inset_3px_0_0_0_#4edea3,0_0_16px_rgba(16,185,129,0.15)]'
                    : 'text-on-surface-variant hover:bg-surface-container-high hover:text-on-surface font-body-md'
                }`}
              >
                <div className="flex items-center gap-2.5">
                  <span className={isActive ? 'text-primary' : 'text-on-surface-variant'}>
                    {item.icon}
                  </span>
                  <span className="text-sm">{item.label}</span>
                </div>
                {item.badge !== undefined && (
                  <span className="px-1.5 py-0.5 text-[10px] font-mono font-semibold bg-primary/20 text-primary rounded border border-primary/30">
                    {item.badge}
                  </span>
                )}
              </button>
            );
          })}
        </nav>
      </div>

      {/* System Matrix Telemetry Deck - All values derived from real API telemetry */}
      <div className="p-3.5 m-3 rounded-xl bg-surface-container-low/80 backdrop-blur-md border border-outline-variant/30 space-y-2">
        <div className="flex items-center justify-between pb-1.5 border-b border-outline-variant/20">
          <span className="font-label-mono-sm uppercase text-outline flex items-center gap-1.5 text-[10px]">
            <Layers className="w-3.5 h-3.5 text-secondary" />
            <span>Subsystem Telemetry</span>
          </span>
          <span className="flex h-2 w-2 relative">
            <span
              className={`animate-ping absolute inline-flex h-full w-full rounded-full ${
                health?.status === 'healthy' ? 'bg-primary' : 'bg-tertiary'
              } opacity-75`}
            ></span>
            <span
              className={`relative inline-flex rounded-full h-2 w-2 ${
                health?.status === 'healthy' ? 'bg-primary' : 'bg-tertiary'
              }`}
            ></span>
          </span>
        </div>

        <div className="space-y-1.5 text-xs">
          <div className="flex justify-between items-center">
            <span className="font-body-sm text-on-surface-variant text-[11px]">API Health</span>
            <span className="font-label-mono-sm text-primary font-bold text-[11px]">
              {health?.status ? health.status.toUpperCase() : 'CONNECTING'}
            </span>
          </div>
          <div className="flex justify-between items-center">
            <span className="font-body-sm text-on-surface-variant text-[11px]">Decider 2B</span>
            <span className="font-label-mono-sm text-secondary text-[11px]">
              {isDeciderLoaded ? 'In-Memory Ready' : 'Standby'}
            </span>
          </div>
          <div className="flex justify-between items-center">
            <span className="font-body-sm text-on-surface-variant text-[11px]">Bedrock Engine</span>
            <span className={`font-label-mono-sm text-[11px] ${isBedrockLive ? 'text-primary' : 'text-tertiary'}`}>
              {isBedrockLive ? 'Live IAM' : 'Dev Mode (Fallback)'}
            </span>
          </div>
          <div className="flex justify-between items-center">
            <span className="font-body-sm text-on-surface-variant text-[11px]">Benchmark Zones</span>
            <span className="font-label-mono-sm text-on-surface text-[11px]">
              {locationsCount} (Synthetic)
            </span>
          </div>
        </div>
      </div>
    </aside>
  );

  return (
    <>
      {/* Desktop Persistent Sidebar (>= lg) */}
      <div className="hidden lg:block fixed left-0 top-0 h-full z-40">
        {sidebarContent}
      </div>

      {/* Mobile Off-Canvas Drawer (< lg) */}
      {isOpenMobile && (
        <div className="lg:hidden fixed inset-0 z-50 flex">
          {/* Backdrop */}
          <div
            className="fixed inset-0 bg-black/70 backdrop-blur-sm transition-opacity"
            onClick={onCloseMobile}
          />
          {/* Drawer content */}
          <div className="relative z-10 w-64 max-w-[80vw]">
            {sidebarContent}
          </div>
        </div>
      )}
    </>
  );
};
