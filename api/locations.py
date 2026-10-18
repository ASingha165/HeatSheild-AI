"""
HeatShield AI - Serverless Function for /api/locations
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
from backend.app.routes.locations import get_sample_locations
from backend.app.schemas import LocationsResponse

app = FastAPI(title="HeatShield AI Locations")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/locations", response_model=LocationsResponse)
@app.get("/locations", response_model=LocationsResponse)
@app.get("/", response_model=LocationsResponse)
def locations_endpoint():
    return get_sample_locations()

handler = app
