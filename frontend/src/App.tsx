import React, { useEffect, useState } from 'react';
import { Sidebar, type NavTab } from './components/layout/Sidebar';
import { Header } from './components/layout/Header';
import { OverviewCards } from './components/dashboard/OverviewCards';
import { EnvironmentalMap } from './components/map/EnvironmentalMap';
import { ReportForm } from './components/reports/ReportForm';
import { DeciderPanel } from './components/decisions/DeciderPanel';
import { ToolExecutionPanel } from './components/tools/ToolExecutionPanel';
import { RecommendationPanel } from './components/recommendations/RecommendationPanel';
import { ExecutionTrace } from './components/trace/ExecutionTrace';
import { DecisionHistory } from './components/history/DecisionHistory';
import { AboutView } from './components/about/AboutModal';
import { api } from './services/api';
import type {
  HealthResponse,
  ReportAnalyzeResponse,
  SampleLocationItem,
  SystemConfigResponse,
} from './types/api';
import { AlertCircle, FileCheck, Layers } from 'lucide-react';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<NavTab>('overview');
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [config, setConfig] = useState<SystemConfigResponse | null>(null);
  const [locations, setLocations] = useState<SampleLocationItem[]>([]);
  const [analyzedReports, setAnalyzedReports] = useState<ReportAnalyzeResponse[]>([]);
  const [currentReport, setCurrentReport] = useState<ReportAnalyzeResponse | null>(null);
  const [selectedLocation, setSelectedLocation] = useState<SampleLocationItem | null>(null);
  const [preloadedLocation, setPreloadedLocation] = useState<SampleLocationItem | null>(null);

  const [isLoadingStatus, setIsLoadingStatus] = useState<boolean>(false);
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [apiError, setApiError] = useState<string | null>(null);

  // Load initial backend telemetry
  const fetchSubsystemStatus = async () => {
    setIsLoadingStatus(true);
    setApiError(null);
    try {
      const [healthData, configData, locationsData] = await Promise.all([
        api.getHealth(),
        api.getConfigStatus(),
        api.getLocations(),
      ]);
      setHealth(healthData);
      setConfig(configData);
      setLocations(locationsData.locations || []);
    } catch (err: any) {
      setApiError(
        `Backend API connection error: ${err.message}. Ensure backend is running at http://127.0.0.1:8000.`
      );
    } finally {
      setIsLoadingStatus(false);
    }
  };

  useEffect(() => {
    fetchSubsystemStatus();
  }, []);

  // Handle report submission
  const handleSubmitReport = async (
    reportText: string,
    locationStr: string | null,
    threshold: number | null
  ) => {
    setIsSubmitting(true);
    setApiError(null);
    try {
      const result = await api.analyzeReport({
        report: reportText,
        location: locationStr,
        confidence_threshold: threshold,
      });

      setCurrentReport(result);
      setAnalyzedReports((prev) => [result, ...prev]);

      // If user submitted from 'overview' or 'analyze', stay or view result
      if (activeTab === 'map') {
        setActiveTab('analyze');
      }
    } catch (err: any) {
      setApiError(`Decision Agent Execution Error: ${err.message}`);
    } finally {
      setIsSubmitting(false);
    }
  };

  // Pre-load a sample location from Map into Report Form
  const handlePreloadLocation = (loc: SampleLocationItem) => {
    setSelectedLocation(loc);
    setPreloadedLocation(loc);
    setActiveTab('analyze');
  };

  const getPageMeta = () => {
    switch (activeTab) {
      case 'overview':
        return { title: 'Environmental Intelligence Overview', subtitle: 'Real-time urban heat indicators and active decision session metrics' };
      case 'map':
        return { title: 'Spatial Microclimate Map', subtitle: 'Interactive heat-risk sensor locations and sample neighborhood zones' };
      case 'analyze':
        return { title: 'Decision Agent Workflow', subtitle: 'Submit urban environmental reports for Strands Decider 2B routing and Bedrock reasoning' };
      case 'history':
        return { title: 'Session Decision Audit History', subtitle: 'Chronological execution log of reports evaluated during this session' };
      case 'about':
        return { title: 'Decider Pattern & Architecture', subtitle: 'Documentation on Strands Decider 2B and confidence-aware tool selection' };
    }
  };

  const meta = getPageMeta();

  return (
    <div className="flex min-h-screen bg-[#0a0d12] text-slate-100 font-sans">
      {/* Left Navigation Sidebar */}
      <Sidebar
        activeTab={activeTab}
        onSelectTab={setActiveTab}
        reportCount={analyzedReports.length}
      />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0">
        <Header
          title={meta.title}
          subtitle={meta.subtitle}
          health={health}
          config={config}
          isLoading={isLoadingStatus}
          onRefresh={fetchSubsystemStatus}
        />

        <main className="flex-1 p-6 space-y-6 overflow-y-auto max-w-7xl w-full mx-auto">
          {/* Global API Connection Error Banner */}
          {apiError && (
            <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 flex items-start space-x-3 text-xs text-rose-300">
              <AlertCircle className="w-5 h-5 text-rose-400 shrink-0 mt-0.5" />
              <div className="space-y-1">
                <span className="font-bold text-rose-200">System Communication Notice</span>
                <p className="leading-relaxed">{apiError}</p>
              </div>
            </div>
          )}

          {/* TAB 1: OVERVIEW */}
          {activeTab === 'overview' && (
            <div className="space-y-6">
              <OverviewCards
                totalLocations={locations.length}
                analyzedReports={analyzedReports}
              />

              {/* Dual Column: Quick Map & Quick Report Form */}
              <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
                <div className="lg:col-span-7 space-y-3">
                  <div className="flex items-center justify-between text-xs text-slate-300 font-semibold">
                    <span className="flex items-center space-x-1.5">
                      <Layers className="w-4 h-4 text-cyan-400" />
                      <span>Monitored Thermal Zones</span>
                    </span>
                    <button
                      onClick={() => setActiveTab('map')}
                      className="text-cyan-400 hover:text-cyan-300 font-medium"
                    >
                      Open Full Map &rarr;
                    </button>
                  </div>
                  <EnvironmentalMap
                    locations={locations}
                    selectedLocationId={selectedLocation?.id}
                    onSelectLocation={setSelectedLocation}
                    onPreloadReport={handlePreloadLocation}
                  />
                </div>

                <div className="lg:col-span-5 space-y-3">
                  <ReportForm
                    locations={locations}
                    onSubmit={handleSubmitReport}
                    isSubmitting={isSubmitting}
                    preloadedLocation={preloadedLocation}
                  />
                </div>
              </div>

              {/* Show Latest Decision Results if available */}
              {currentReport && (
                <div className="space-y-6 pt-4 border-t border-[#242d3d]">
                  <h3 className="text-base font-bold text-slate-100 flex items-center space-x-2">
                    <FileCheck className="w-5 h-5 text-emerald-400" />
                    <span>Latest Analysis: {currentReport.report_id}</span>
                  </h3>
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <DeciderPanel decision={currentReport.decision} />
                    {currentReport.tool_execution && (
                      <ToolExecutionPanel toolExecution={currentReport.tool_execution} />
                    )}
                  </div>
                  {currentReport.recommendation && (
                    <RecommendationPanel recommendation={currentReport.recommendation} />
                  )}
                  <ExecutionTrace
                    steps={currentReport.execution_trace}
                    totalLatencyMs={currentReport.total_latency_ms}
                    workflowStage={currentReport.workflow_stage}
                  />
                </div>
              )}
            </div>
          )}

          {/* TAB 2: ENVIRONMENTAL MAP */}
          {activeTab === 'map' && (
            <div className="space-y-4">
              <EnvironmentalMap
                locations={locations}
                selectedLocationId={selectedLocation?.id}
                onSelectLocation={setSelectedLocation}
                onPreloadReport={handlePreloadLocation}
              />

              {/* Location details card when a location is selected */}
              {selectedLocation && (
                <div className="p-4 rounded-xl bg-[#161c28] border border-cyan-500/30 flex flex-col sm:flex-row sm:items-center justify-between gap-4 text-xs">
                  <div>
                    <h4 className="font-bold text-slate-100 text-sm">{selectedLocation.name}</h4>
                    <p className="text-slate-400 mt-0.5">{selectedLocation.description}</p>
                    <div className="flex items-center space-x-3 mt-2 font-mono text-[11px]">
                      <span className="text-rose-400">
                        Heat Index: {selectedLocation.synthetic_measurements.heat_index_c}°C
                      </span>
                      <span className="text-emerald-400">
                        Canopy: {selectedLocation.synthetic_measurements.canopy_coverage_pct}%
                      </span>
                      <span className="text-cyan-400">
                        Transit Stops: {selectedLocation.synthetic_measurements.transit_stops_count}
                      </span>
                    </div>
                  </div>
                  <button
                    onClick={() => handlePreloadLocation(selectedLocation)}
                    className="px-4 py-2 rounded-lg bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-semibold transition-colors shrink-0"
                  >
                    Load into Report Form &rarr;
                  </button>
                </div>
              )}
            </div>
          )}

          {/* TAB 3: ANALYZE REPORT */}
          {activeTab === 'analyze' && (
            <div className="space-y-6">
              <ReportForm
                locations={locations}
                onSubmit={handleSubmitReport}
                isSubmitting={isSubmitting}
                preloadedLocation={preloadedLocation}
              />

              {currentReport && (
                <div className="space-y-6">
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <DeciderPanel decision={currentReport.decision} />
                    {currentReport.tool_execution ? (
                      <ToolExecutionPanel toolExecution={currentReport.tool_execution} />
                    ) : (
                      <div className="bg-[#161c28] border border-[#242d3d] rounded-xl p-6 flex flex-col justify-center items-center text-center space-y-2 text-xs">
                        <span className="text-amber-400 font-semibold">Tool Execution Held at Safety Gate</span>
                        <p className="text-slate-400 max-w-sm">
                          Because model confidence was below the configured threshold, no tool was executed automatically.
                        </p>
                      </div>
                    )}
                  </div>

                  {currentReport.recommendation && (
                    <RecommendationPanel recommendation={currentReport.recommendation} />
                  )}

                  <ExecutionTrace
                    steps={currentReport.execution_trace}
                    totalLatencyMs={currentReport.total_latency_ms}
                    workflowStage={currentReport.workflow_stage}
                  />
                </div>
              )}
            </div>
          )}

          {/* TAB 4: DECISION HISTORY */}
          {activeTab === 'history' && (
            <div className="space-y-6">
              <DecisionHistory
                reports={analyzedReports}
                selectedReportId={currentReport?.report_id}
                onSelectReport={(rep) => {
                  setCurrentReport(rep);
                  setActiveTab('analyze');
                }}
              />
            </div>
          )}

          {/* TAB 5: ABOUT & DOCS */}
          {activeTab === 'about' && <AboutView />}
        </main>
      </div>
    </div>
  );
};

export default App;
