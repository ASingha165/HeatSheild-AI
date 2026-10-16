"""HeatShield AI API Route Modules."""

from .health import router as health_router
from .locations import router as locations_router
from .reports import router as reports_router

__all__ = ["health_router", "locations_router", "reports_router"]
