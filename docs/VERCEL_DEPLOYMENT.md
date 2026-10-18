# Deploying HeatShield AI on Vercel

This guide documents the exact deployment configuration, routing architecture, server-side environment variables, and execution characteristics for deploying **HeatShield AI** entirely on [Vercel](https://vercel.com).

---

## 🏛️ Deployment Architecture Overview

HeatShield AI is deployed on Vercel as a unified full-stack application:

```mermaid
graph LR
    User[Client Browser] --> Edge[Vercel Global Edge Network]
    Edge -->|/ and /* (Static)| CDN[Vite React SPA<br/>public/ & root dist/]
    Edge -->|/api/* (Direct/Rewrite)| PyFunc[Vercel Python Functions<br/>api/health.py, api/index.py, ...]
    PyFunc --> Decider{DECIDER_REMOTE_URL<br/>Configured?}
    Decider -->|Yes| RemoteDecider[Remote Strands Decider 2B<br/>HTTP API /v1/systemone]
    Decider -->|No| UnconfGate[Safety Gating<br/>Transparent Standby Status]
    PyFunc --> Tools[Modular Analytical Tools<br/>Pure Python]
    PyFunc --> Bedrock[Amazon Bedrock Converse API<br/>boto3 Server-Side]
```

1. **Frontend (Vite + React)**: Compiled to static assets in `public/` and `dist/` and served directly with global edge caching.
2. **Backend (FastAPI)**: Adapted to Vercel's Python Serverless Function runtime via `api/index.py` alongside direct endpoints (`api/health.py`, `api/locations.py`, `api/config.py`, `api/reports.py`).
3. **Routing (`vercel.json`)**: Plan-agnostic rewrites directing `/api/*` to FastAPI while preserving SPA client routing for the React frontend.
4. **Serverless Compliance**: Meets Vercel's 250MB function bundle limit and execution timeout constraints without requiring plan-restricted memory/duration overrides.

---

## 🌐 Live Domains

* **Live Deployment URL**: [https://heat-sheild-ai.vercel.app](https://heat-sheild-ai.vercel.app)
  *(Default Vercel production domain derived from repository `ASingha165/HeatSheild-AI`)*
* **Alias Domain**: [https://heat-shield-ai.vercel.app](https://heat-shield-ai.vercel.app)
  *(Configured under Vercel Project Settings > Domains as an alias)*

---

## ⚙️ Vercel Project Settings

When importing the repository (`https://github.com/ASingha165/HeatSheild-AI`) into Vercel, configure the project settings as follows:

| Setting | Value | Notes |
| :--- | :--- | :--- |
| **Framework Preset** | `Other` (or `Vite`) | Allows custom monorepo full-stack build |
| **Root Directory** | `.` | Must be repository root (NOT `frontend`) |
| **Build Command** | `npm run build` | Runs `node scripts/build_fullstack.js` |
| **Output Directory** | `public` (or leave blank) | Serves pre-built frontend from `public/` |
| **Install Command** | `npm install` | Installs root dependencies |

---

## 🔐 Required Environment Variables

All AWS credentials and backend configurations must be placed in **Vercel Project Settings > Environment Variables**. They are accessible **exclusively on the server-side** and are never exposed to the client browser.

### 1. Amazon Bedrock & AWS Configuration

| Variable Name | Required | Default Value | Description |
| :--- | :---: | :--- | :--- |
| `AWS_REGION` | **Yes** | `us-east-1` | AWS region hosting Amazon Bedrock (e.g. `us-east-1`) |
| `BEDROCK_MODEL_ID` | **Yes** | `global.amazon.nova-2-lite-v1:0` | Foundation model ID or inference profile |
| `BEDROCK_TEMPERATURE` | No | `0.2` | Sampling temperature for generative recommendations |
| `BEDROCK_MAX_TOKENS` | No | `1024` | Maximum tokens for synthesis output |
| `BEDROCK_TIMEOUT_SECONDS` | No | `15` | Read timeout for Bedrock Converse requests |
| `AWS_ACCESS_KEY_ID` | **Yes\*** | *(None)* | Server-side AWS access key ID |
| `AWS_SECRET_ACCESS_KEY` | **Yes\*** | *(None)* | Server-side AWS secret access key |
| `AWS_SESSION_TOKEN` | Optional | *(None)* | Temporary session token (required for AWS Workshop Studio) |

*\* Note: If AWS credentials are not set, the backend operates in transparent development mode, emitting verified evidence-based synthetic recommendations with `is_live_bedrock: false`.*

### 2. Strands Decider 2B Configuration

| Variable Name | Required | Default Value | Description |
| :--- | :---: | :--- | :--- |
| `DECIDER_REMOTE_URL` | Optional | *(None)* | URL of remote Strands Decider 2B service (e.g., `https://decider.your-domain.com`) |
| `DECIDER_CONFIDENCE_THRESHOLD` | No | `0.60` | Minimum confidence score required to auto-dispatch analytical tools |

*\* Note on Vercel Execution Limits: In-process loading of 2B parameter weights (~4 GB PyTorch weights) exceeds Vercel Serverless Function package limits (250 MB). To execute live Strands Decider 2B inference in a Vercel deployment, host `strands-decider serve` on an external instance (e.g., EC2, Modal, RunPod) and supply its endpoint in `DECIDER_REMOTE_URL`. If unconfigured, the system safely gates execution via `HALT_UNCONFIGURED` without crashing.*

### 3. Application Settings

| Variable Name | Required | Default Value | Description |
| :--- | :---: | :--- | :--- |
| `ENVIRONMENT` | No | `production` | Environment mode flag |
| `VITE_API_BASE_URL` | No | `""` (empty) | Keep empty on Vercel to route `/api/*` through relative edge routing |

---

## 🔀 Routing Specification (`vercel.json`)

```json
{
  "$schema": "https://openapi.vercel.sh/vercel.json",
  "rewrites": [
    {
      "source": "/api/(.*)",
      "destination": "/api/index.py"
    },
    {
      "source": "/api",
      "destination": "/api/index.py"
    },
    {
      "source": "/((?!api/).*)",
      "destination": "/index.html"
    }
  ]
}
```

### Route Resolution Table

| Incoming Request URL | Routed Target | Handler / Service |
| :--- | :--- | :--- |
| `GET /` | `public/index.html` | Edge CDN (Static React SPA) |
| `GET /assets/*` | `public/assets/*` | Edge CDN (Static JavaScript/CSS) |
| `GET /api` | `api/index.py` | FastAPI root metadata endpoint |
| `GET /api/health` | `api/health.py` & `api/index.py` | FastAPI subsystem health status |
| `GET /api/config/status` | `api/config.py` & `api/index.py` | FastAPI public configuration status |
| `GET /api/locations` | `api/locations.py` & `api/index.py` | FastAPI sample urban monitoring zones |
| `POST /api/reports/analyze`| `api/reports.py` & `api/index.py` | Full decision, analytical tool & Bedrock pipeline |
| `GET /api/docs` | `api/index.py` | Interactive Swagger API documentation |
| `GET /api/openapi.json` | `api/index.py` | OpenAPI 3.1.0 schema specification |
| `GET /docs` | `/api/docs` | HTTP 307 Redirect to `/api/docs` |
| `GET /reports/*`, `GET /map` | `public/index.html` | React Router client-side SPA navigation |

---

## 🧪 Local Testing & Verification

To verify the exact Vercel build and API behavior before deploying:

```powershell
# 1. Build the production frontend exactly as Vercel does
npm run build

# 2. Run backend test suite
.\.venv\Scripts\pytest.exe backend/tests

# 3. Test Vercel serverless entrypoints
.\.venv\Scripts\python.exe -c "
from fastapi.testclient import TestClient
from api.health import app as health_app
from api.index import app as main_app
assert TestClient(health_app).get('/api/health').status_code == 200
assert TestClient(main_app).get('/api/health').status_code == 200
assert TestClient(main_app).get('/').status_code == 200
print('All Vercel entrypoints verified!')
"
```

---

## 🛡️ Security & Truthfulness Guarantees

1. **Zero Credential Exposure**:
   - `frontend/.env` contains no AWS secrets.
   - `api/config/status` never returns API keys or access tokens.
   - Logs automatically redact any inadvertent key patterns via regex filters.
2. **Synthetic Data Provenance**:
   - All sample neighborhood indicators are tagged with `is_synthetic: true` and disclaimer text.
3. **Execution Gating**:
   - Tool execution is blocked when Decider confidence is $< 0.60$ or unconfigured.
4. **Human Review Enforcement**:
   - All Bedrock outputs include warnings that on-the-ground municipal verification is mandatory before action dispatch.
