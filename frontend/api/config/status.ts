export default function handler(req: any, res: any) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Accept');

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  const deciderUrl = (process.env.DECIDER_REMOTE_URL || '').trim();
  const region = process.env.AWS_REGION || process.env.AWS_DEFAULT_REGION || 'us-east-1';
  const modelId = process.env.BEDROCK_MODEL_ID || 'global.amazon.nova-2-lite-v1:0';
  const hasBedrockKey = !!(process.env.AWS_ACCESS_KEY_ID && process.env.AWS_SECRET_ACCESS_KEY);

  return res.status(200).json({
    environment: process.env.ENVIRONMENT || 'production',
    decider: {
      checkpoint: 'StrandsAgents/strands-decider-2B-hobson-v21',
      device: 'cpu',
      confidence_threshold: 0.60,
      remote_url: deciderUrl || null,
      is_engine_loaded: !!deciderUrl,
      is_ready: !!deciderUrl,
    },
    bedrock: {
      is_configured: hasBedrockKey,
      region_name: region,
      model_id: modelId,
      temperature: 0.2,
      auth_mode: hasBedrockKey ? 'iam_role_or_key' : 'transparent_dev_mode',
      credentials_available: hasBedrockKey,
    },
    synthetic_dataset: {
      is_synthetic: true,
      dataset_label: "SYNTHETIC_DEV_DATASET_V1",
      disclaimer: "DEMONSTRATION ONLY: All metrics are synthetic benchmark samples.",
      version: "1.0.0"
    }
  });
}
