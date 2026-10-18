"""
HeatShield AI - Vercel Serverless Function Entrypoint for /api.
Adapts the FastAPI application to Vercel Python runtime.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

os.environ.setdefault("ENVIRONMENT", "production")

from backend.app.main import app

handler = app
