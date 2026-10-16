import React from 'react';
import {
  ShieldAlert,
  MapPin,
  FileText,
  Activity,
  History,
  Info,
  ExternalLink,
} from 'lucide-react';

export type NavTab = 'overview' | 'map' | 'analyze' | 'history' | 'about';

interface SidebarProps {
  activeTab: NavTab;
  onSelectTab: (tab: NavTab) => void;
  reportCount: number;
}

export const Sidebar: React.FC<SidebarProps> = ({
  activeTab,
  onSelectTab,
  reportCount,
}) => {
  const navItems: Array<{ id: NavTab; label: string; icon: React.ReactNode; badge?: number }> = [
    { id: 'overview', label: 'Overview', icon: <Activity className="w-5 h-5" /> },
    { id: 'map', label: 'Environmental Map', icon: <MapPin className="w-5 h-5" /> },
    { id: 'analyze', label: 'Analyze Report', icon: <FileText className="w-5 h-5" /> },
    {
      id: 'history',
      label: 'Decision History',
      icon: <History className="w-5 h-5" />,
      badge: reportCount > 0 ? reportCount : undefined,
    },
    { id: 'about', label: 'Decider Pattern & Docs', icon: <Info className="w-5 h-5" /> },
  ];

  return (
    <aside className="w-64 bg-[#111620] border-r border-[#242d3d] flex flex-col shrink-0 min-h-screen">
      {/* Brand Header */}
      <div className="p-5 border-b border-[#242d3d] flex items-center space-x-3">
        <div className="w-10 h-10 rounded-lg bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400 shrink-0">
          <ShieldAlert className="w-6 h-6" />
        </div>
        <div>
          <h1 className="text-lg font-bold text-slate-100 tracking-tight">HeatShield AI</h1>
          <p className="text-[11px] text-emerald-400 font-medium">Decider 2B Agent</p>
        </div>
      </div>

      {/* Mission Tagline */}
      <div className="px-5 py-3 bg-[#0d121c]/70 border-b border-[#242d3d]/50">
        <p className="text-[11px] text-slate-400 leading-snug">
          <span className="text-cyan-400 font-semibold">Detect</span> heat. <span className="text-emerald-400 font-semibold">Decide</span> response. <span className="text-amber-400 font-semibold">Protect</span> people.
        </p>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-3 space-y-1">
        {navItems.map((item) => {
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => onSelectTab(item.id)}
              className={`w-full flex items-center justify-between px-3.5 py-2.5 rounded-lg text-sm font-medium transition-all ${
                isActive
                  ? 'bg-emerald-500/15 text-emerald-300 border border-emerald-500/30 shadow-sm'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-[#161c28]'
              }`}
            >
              <div className="flex items-center space-x-3">
                <span className={isActive ? 'text-emerald-400' : 'text-slate-400'}>{item.icon}</span>
                <span>{item.label}</span>
              </div>
              {item.badge !== undefined && (
                <span className="px-1.5 py-0.5 text-[11px] font-semibold bg-emerald-500/20 text-emerald-300 rounded border border-emerald-500/30">
                  {item.badge}
                </span>
              )}
            </button>
          );
        })}
      </nav>

      {/* Tech Stack Meta Footer */}
      <div className="p-4 border-t border-[#242d3d] bg-[#0d121c]/60 text-xs space-y-2">
        <div className="flex items-center justify-between text-slate-400 text-[11px]">
          <span>Decision Model:</span>
          <span className="font-mono text-cyan-300 font-semibold">Strands Decider 2B</span>
        </div>
        <div className="flex items-center justify-between text-slate-400 text-[11px]">
          <span>Reasoning Engine:</span>
          <span className="font-mono text-amber-300 font-semibold">Amazon Bedrock</span>
        </div>
        <div className="pt-2 border-t border-[#242d3d]/50 flex items-center justify-between text-[11px] text-slate-400">
          <span>AWS Hackathon 2026</span>
          <a
            href="https://github.com/ASingha165/HeatSheild-AI"
            target="_blank"
            rel="noopener noreferrer"
            className="text-slate-400 hover:text-slate-200 flex items-center space-x-1"
          >
            <span>GitHub</span>
            <ExternalLink className="w-3 h-3" />
          </a>
        </div>
      </div>
    </aside>
  );
};
