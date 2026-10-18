export default function handler(req: any, res: any) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Accept');

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  const deciderUrl = (process.env.DECIDER_REMOTE_URL || '').trim();
  const hasBedrockKey = !!(process.env.AWS_ACCESS_KEY_ID && process.env.AWS_SECRET_ACCESS_KEY);

  return res.status(200).json({
    status: 'healthy',
    version: '1.0.0',
    timestamp: new Date().toISOString(),
    decider_status: deciderUrl ? 'ready' : 'standby_unconfigured',
    bedrock_status: hasBedrockKey ? 'configured' : 'unconfigured_dev_mode',
  });
}
