/**
 * TypeScript API interfaces matching HeatShield AI FastAPI schemas exactly.
 */

export type WorkflowStage =
  | 'DECISION_REJECTED'
  | 'NEEDS_CLARIFICATION'
  | 'TOOL_EXECUTED'
  | 'RECOMMENDATION_GENERATED'
  | 'BEDROCK_UNAVAILABLE';

export type DecisionStatus =
  | 'accepted'
  | 'requires_clarification'
  | 'rejected_invalid'
  | 'unconfigured';

export type ExecutionGate =
  | 'PROCEED_TO_TOOL'
  | 'REQUEST_HUMAN_CLARIFICATION'
  | 'REJECT_INVALID_CHOICE'
  | 'HALT_UNCONFIGURED';

export type AnalyticalAction =
  | 'ANALYZE_HEAT'
  | 'CHECK_VEGETATION'
  | 'CHECK_EXPOSURE'
  | 'COMPARE_INTERVENTIONS'
  | 'REQUEST_MORE_DATA';

export interface NormalizedDecision {
  decision: string;
  confidence: number;
  decision_pattern: string;
  latency_ms: number;
  status: DecisionStatus;
  probabilities: Record<string, number>;
  selected_option_valid: boolean;
  confidence_threshold: number;
  is_above_threshold: boolean;
  execution_gate: ExecutionGate;
  clarification_prompt?: string | null;
  state_summary: Record<string, any>;
  raw_response?: Record<string, any> | null;
}

export interface TraceStep {
  step_number: number;
  name: string;
  status: 'completed' | 'skipped' | 'gated' | 'failed' | string;
  duration_ms: number;
  timestamp: string;
  details: Record<string, any>;
}

export interface ToolExecutionResponse {
  tool_name: string;
  status: 'success' | 'error' | string;
  execution_time_ms: number;
  output: Record<string, any>;
  error_message?: string | null;
}

export interface BedrockRecommendation {
  summary: string;
  recommended_next_step: string;
  supporting_evidence: string[];
  assumptions: string[];
  limitations: string[];
  follow_up_actions: string[];
  model_id: string;
  is_live_bedrock: boolean;
  data_provenance: string;
  latency_ms: number;
  status: 'success' | 'dev_mode_fallback' | 'unconfigured' | string;
}

export interface ReportAnalyzeResponse {
  report_id: string;
  workflow_stage: WorkflowStage;
  timestamp: string;
  original_report: string;
  location: string;
  is_synthetic_dataset: boolean;
  dataset_label: string;
  decision: NormalizedDecision;
  tool_execution?: ToolExecutionResponse | null;
  recommendation?: BedrockRecommendation | null;
  execution_trace: TraceStep[];
  total_latency_ms: number;
}

export interface ReportAnalyzeRequest {
  report: string;
  location?: string | null;
  confidence_threshold?: number | null;
  extra_context?: Record<string, any> | null;
}

export interface HealthResponse {
  status: string;
  version: string;
  timestamp: string;
  decider_status: string;
  bedrock_status: string;
}

export interface BedrockConfigStatus {
  is_configured: boolean;
  region: string;
  model_id: string;
  auth_mechanism: string;
  status_message: string;
}

export interface SystemConfigResponse {
  environment: string;
  decider: {
    checkpoint: string;
    device: string;
    confidence_threshold: number;
    remote_url?: string | null;
    is_engine_loaded: boolean;
  };
  bedrock: BedrockConfigStatus;
  synthetic_dataset: {
    is_synthetic: boolean;
    dataset_label: string;
    disclaimer: string;
    version: string;
  };
}

export interface SampleLocationItem {
  id: string;
  name: string;
  coordinates: {
    lat: number;
    lng: number;
  };
  description: string;
  is_synthetic: boolean;
  synthetic_measurements: {
    ambient_temp_c: number;
    surface_temp_c: number;
    heat_index_c: number;
    canopy_coverage_pct: number;
    ndvi_index: number;
    impervious_surface_pct: number;
    transit_stops_count: number;
    daily_transit_commuters: number;
    vulnerable_facilities?: Array<{ name: string; type: string; distance_m: number }>;
    unshaded_waiting_areas: number;
  };
}

export interface LocationsResponse {
  total: number;
  locations: SampleLocationItem[];
  is_synthetic_dataset: boolean;
  dataset_disclaimer: string;
}
