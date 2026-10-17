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
  const [apiLatency, setApiLatency] = useState<number | null>(null);
  const [isMobileNavOpen, setIsMobileNavOpen] = useState<boolean>(false);

  // Load backend telemetry and measure round-trip latency
  const fetchSubsystemStatus = async (silent: boolean = false) => {
    if (!silent) {
      setIsLoadingStatus(true);
      setApiError(null);
    }
    const start = performance.now();
    try {
      const [healthData, configData, locationsData] = await Promise.all([
        api.getHealth(),
        api.getConfigStatus(),
        api.getLocations(),
      ]);
      const measuredLatency = Math.round(performance.now() - start);
      setApiLatency(measuredLatency);
      setHealth(healthData);
      setConfig(configData);
      setLocations(locationsData.locations || []);
    } catch (err: any) {
      if (!silent) {
        setApiError(
          `Backend API connection error: ${err.message}. Ensure backend is running at http://127.0.0.1:8000.`
        );
      }
    } finally {
      if (!silent) {
        setIsLoadingStatus(false);
      }
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

      // If user submitted from 'map', switch to 'analyze'
      if (activeTab === 'map') {
        setActiveTab('analyze');
      }
    } catch (err: any) {
      setApiError(`Decision Agent Execution Error: ${err.message}`);
    } finally {
      setIsSubmitting(false);
      // Immediately refresh subsystem telemetry (Decider readiness & Bedrock status)
      // to reflect post-inference state on both success and error paths
      fetchSubsystemStatus(true);
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
        return {
          title: 'Urban Climate & Heat Risk Operations',
          subtitle: 'Real-time urban heat indicators and active decision session metrics',
        };
      case 'map':
        return {
          title: 'Spatial Microclimate Map Canvas',
          subtitle: 'Interactive heat-risk sensor locations and sample neighborhood zones',
        };
      case 'analyze':
        return {
          title: 'Decision Agent Workflow Deck',
          subtitle: 'Submit urban environmental reports for Strands Decider 2B routing and Bedrock reasoning',
        };
      case 'history':
        return {
          title: 'Session Decision Audit History',
          subtitle: 'Chronological execution log of reports evaluated during this session',
        };
      case 'about':
        return {
          title: 'Decider Pattern & Architecture',
          subtitle: 'Technical documentation on Strands Decider 2B and confidence-aware tool selection',
        };
    }
  };

  const meta = getPageMeta();

  return (
    <div className="flex min-h-screen bg-surface text-on-surface font-body overflow-x-hidden">
      {/* Responsive Sidebar (Fixed desktop, Drawer on tablet/mobile) */}
      <Sidebar
        activeTab={activeTab}
        onSelectTab={setActiveTab}
        reportCount={analyzedReports.length}
        isOpenMobile={isMobileNavOpen}
        onCloseMobile={() => setIsMobileNavOpen(false)}
        health={health}
        config={config}
        locationsCount={locations.length}
      />

      {/* Main Content Area with responsive desktop offset (lg:pl-64 xl:pl-72, pl-0 on mobile/tablet) */}
      <div className="lg:pl-64 xl:pl-72 flex-1 flex flex-col min-w-0 w-full overflow-x-hidden">
        <Header
          title={meta.title}
          subtitle={meta.subtitle}
          health={health}
          config={config}
          apiLatencyMs={apiLatency}
          isLoading={isLoadingStatus}
          onRefresh={fetchSubsystemStatus}
          onOpenMobileNav={() => setIsMobileNavOpen(true)}
        />

        <main className="flex-1 p-4 sm:p-6 space-y-6 overflow-y-auto max-w-7xl w-full mx-auto pb-16">
          {/* Global API Connection Error Banner */}
          {apiError && (
            <div className="p-4 rounded-xl bg-error-container/20 border border-error/40 flex items-start gap-3 text-xs text-error font-body-sm shadow-sm">
              <AlertCircle className="w-5 h-5 text-error shrink-0 mt-0.5" />
              <div className="space-y-1">
                <span className="font-bold text-error">System Communication Notice</span>
                <p className="leading-relaxed text-on-surface-variant">{apiError}</p>
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

              {/* Dual Column: Quick Map & Quick Report Form (Stacks on < xl for maximum readability) */}
              <div className="grid grid-cols-1 xl:grid-cols-12 gap-6">
                <div className="xl:col-span-7 space-y-3 min-w-0">
                  <div className="flex items-center justify-between text-xs font-label-mono-sm text-outline">
                    <span className="flex items-center gap-1.5 text-secondary">
                      <Layers className="w-4 h-4 text-secondary" />
                      <span>Monitored Thermal Canvas</span>
                    </span>
                    <button
                      type="button"
                      onClick={() => setActiveTab('map')}
                      className="text-secondary hover:underline cursor-pointer"
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

                <div className="xl:col-span-5 space-y-3 min-w-0">
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
                <div className="space-y-6 pt-4 border-t border-outline-variant/30">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                    <h3 className="font-headline-sm text-on-surface font-bold flex items-center gap-2 text-base sm:text-lg">
                      <FileCheck className="w-5 h-5 text-primary shrink-0" />
                      <span>Latest Decision Pipeline Result: {currentReport.report_id}</span>
                    </h3>
                    <span className="font-label-mono-sm px-2.5 py-1 rounded bg-surface-container-high border border-outline-variant/30 text-secondary self-start sm:self-auto text-xs">
                      Terminal Stage: {currentReport.workflow_stage}
                    </span>
                  </div>

                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <DeciderPanel decision={currentReport.decision} />
                    {currentReport.tool_execution ? (
                      <ToolExecutionPanel toolExecution={currentReport.tool_execution} />
                    ) : (
                      <div className="bg-surface-container-low/90 backdrop-blur-md border border-outline-variant/30 rounded-xl p-6 flex flex-col justify-center items-center text-center space-y-2 text-xs">
                        <span className="text-tertiary font-bold font-label-mono-sm uppercase">
                          Tool Execution Held at Safety Gate
                        </span>
                        <p className="text-on-surface-variant max-w-sm font-body-sm">
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

          {/* TAB 2: ENVIRONMENTAL MAP */}
          {activeTab === 'map' && (
            <div className="space-y-4">
              <EnvironmentalMap
                locations={locations}
                selectedLocationId={selectedLocation?.id}
                onSelectLocation={setSelectedLocation}
                onPreloadReport={handlePreloadLocation}
              />
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
                      <div className="bg-surface-container-low/90 backdrop-blur-md border border-outline-variant/30 rounded-xl p-6 flex flex-col justify-center items-center text-center space-y-2 text-xs">
                        <span className="text-tertiary font-bold font-label-mono-sm uppercase">
                          Tool Execution Held at Safety Gate
                        </span>
                        <p className="text-on-surface-variant max-w-sm font-body-sm">
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
