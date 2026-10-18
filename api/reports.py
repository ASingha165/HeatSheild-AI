"""
HeatShield AI - Dedicated Vercel Serverless Function for /api/reports.
Handles /api/reports/analyze and /api/reports/{report_id}.
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
from backend.app.routes.reports import router as reports_router

app = FastAPI(title="HeatShield AI Reports")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(reports_router, prefix="/api")
app.include_router(reports_router)
