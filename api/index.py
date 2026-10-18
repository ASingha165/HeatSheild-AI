"""
HeatShield AI - Vercel Serverless Function Entrypoint.
Adapts the FastAPI application to Vercel Python runtime.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Ensure the repository root directory is on sys.path so that 'backend' package
# imports resolve correctly in Vercel's serverless environment.
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Ensure environment mode
os.environ.setdefault("ENVIRONMENT", "production")

from backend.app.main import app

# Vercel's Python runtime discovers 'app' as the ASGI application entrypoint
