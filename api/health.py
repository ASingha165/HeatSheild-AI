"""
HeatShield AI - Dedicated Vercel Serverless Function for /api/health.
Guarantees a healthy response whether path is /api/health, /health, or /.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

os.environ.setdefault("ENVIRONMENT", "production")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.dependencies import get_bedrock_service, get_tool_selector
from backend.app.routes.health import get_health, get_config_status
from backend.app.schemas import HealthResponse, SystemConfigResponse

app = FastAPI(title="HeatShield AI Health Check")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health", response_model=HealthResponse)
@app.get("/health", response_model=HealthResponse)
@app.get("/", response_model=HealthResponse)
def health_endpoint():
    selector = get_tool_selector()
    bedrock = get_bedrock_service()
    return get_health(selector=selector, bedrock=bedrock)

@app.get("/api/config/status", response_model=SystemConfigResponse)
@app.get("/config/status", response_model=SystemConfigResponse)
def config_status_endpoint():
    selector = get_tool_selector()
    bedrock = get_bedrock_service()
    return get_config_status(selector=selector, bedrock=bedrock)
