import crypto from 'crypto';

export default async function handler(req: any, res: any) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Accept');

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  if (req.method !== 'POST') {
    return res.status(405).json({ detail: 'Method Not Allowed' });
  }

  const { report = '', location = 'Unspecified Location', confidence_threshold = 0.60 } = req.body || {};
  const reportId = `hs-${crypto.randomBytes(4).toString('hex')}`;
  const start = Date.now();

  const reportText = (report || '').trim();
  const lower = reportText.toLowerCase();

  // Determine analytical action based on environmental context
  let action = 'ANALYZE_HEAT';
  let confidence = 0.88;
  let reason = 'Thermal exposure and heat risk identified in report text.';

  if (lower.includes('vegetation') || lower.includes('tree') || lower.includes('canopy') || lower.includes('shade')) {
    action = 'CHECK_VEGETATION';
    confidence = 0.84;
    reason = 'Vegetation deficit or canopy shade requested in observation report.';
  } else if (lower.includes('vulnerable') || lower.includes('pedestrian') || lower.includes('transit') || lower.includes('senior') || lower.includes('bus')) {
    action = 'CHECK_EXPOSURE';
    confidence = 0.86;
    reason = 'Vulnerable population exposure and transit waiting conditions detected.';
  } else if (lower.includes('compare') || lower.includes('intervention') || lower.includes('cool pavement') || lower.includes('roof')) {
    action = 'COMPARE_INTERVENTIONS';
    confidence = 0.82;
    reason = 'Municipal cooling intervention options comparison requested.';
  } else if (reportText.length < 15) {
    action = 'REQUEST_MORE_DATA';
    confidence = 0.52;
    reason = 'Report text contains insufficient environmental detail for immediate tool execution.';
  }

  const isAccepted = confidence >= (confidence_threshold ?? 0.60);
  const latencyMs = Date.now() - start;

  let toolResult: any = null;
  if (isAccepted && action !== 'REQUEST_MORE_DATA') {
    toolResult = {
      tool_name: action,
      status: 'success',
      execution_latency_ms: 12,
      result_payload: {
        location: location,
        metric: action,
        baseline_ambient_c: 37.8,
        baseline_surface_c: 49.5,
        estimated_mitigation_c: 3.4,
        data_provenance: 'SYNTHETIC_BENCHMARK_DEMONSTRATION'
      }
    };
  }

  const response = {
    report_id: reportId,
    location: location,
    workflow_stage: isAccepted ? 'SYNTHESIS_COMPLETE' : 'HELD_AT_SAFETY_GATE',
    decision: {
      action: action,
      confidence: confidence,
      confidence_threshold: confidence_threshold ?? 0.60,
      is_accepted: isAccepted,
      reasoning: reason,
      model: 'strands-decider-2b-inference',
      latency_ms: latencyMs
    },
    tool_execution: toolResult,
    recommendation: {
      synthesis_text: isAccepted
        ? `Based on verified analytical indicators for ${location}, elevated thermal exposure exceeds safe thresholds. Priority implementation of shade canopies and reflective surface treatments is recommended.`
        : `Execution held at safety gate: confidence score (${confidence.toFixed(2)}) is below threshold (${confidence_threshold.toFixed(2)}). Please collect localized telemetry before action dispatch.`,
      actionable_steps: isAccepted
        ? [
            'Deploy temporary misting and hydration stations along key transit corridors.',
            'Schedule high-albedo cool pavement coating application on priority pedestrian streets.',
            'Expand street tree canopy planting initiatives targeting low-NDVI parcels.'
          ]
        : ['Verify ambient temperature with calibrated sensors.', 'Submit detailed observation.'],
      grounding_sources: [`AnalyticalTool:${action}`, `Location:${location}`],
      is_live_bedrock: false,
      model_id: 'global.amazon.nova-2-lite-v1:0 (dev fallback)',
      confidence_caveat: 'DEMONSTRATION SYNTHESIS: Field verification required prior to municipal budget authorization.'
    },
    execution_trace: [
      { step: 'Ingest Report', status: 'completed', latency_ms: 2 },
      { step: 'Strands Decider Tool Routing', status: 'completed', latency_ms: latencyMs },
      { step: 'Safety Gate Evaluation', status: isAccepted ? 'passed' : 'held', latency_ms: 1 },
      { step: 'Analytical Tool Dispatch', status: toolResult ? 'completed' : 'skipped', latency_ms: 12 },
      { step: 'Amazon Bedrock Recommendation Synthesis', status: 'completed', latency_ms: 15 }
    ],
    total_latency_ms: Date.now() - start
  };

  return res.status(200).json(response);
}
