"""
HeatShield AI - FastAPI Main Application.
"""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from backend.app.dependencies import get_bedrock_service, get_tool_selector
from backend.app.routes.health import router as health_router
from backend.app.routes.locations import router as locations_router
from backend.app.routes.reports import router as reports_router

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
)
logger = logging.getLogger("heatshield.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info("Initializing HeatShield AI application...")
    
    # Pre-warm selector configuration (defer heavy loading if desired or load in background)
    selector = get_tool_selector()
    bedrock = get_bedrock_service()
    
    logger.info("Decider configured for checkpoint: %s (device: %s, ready: %s)", selector.checkpoint, selector.device, selector.is_ready)
    logger.info("Bedrock configured for region: %s (model: %s)", bedrock.region_name, bedrock.model_id)
    
    yield
    logger.info("Shutting down HeatShield AI application.")


app = FastAPI(
    title="HeatShield AI - Environmental Decision Agent API",
    description=(
        "Production AI decision service leveraging Strands Decider 2B for confidence-aware "
        "analytical tool routing and Amazon Bedrock for generative municipal resilience reasoning."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# CORS configuration for Vite React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Open in development, restrict in production deployment
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global safe exception handler: never exposes stack traces or file paths to client
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled exception processing %s %s: %s", request.method, request.url.path, exc, exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "InternalServerError",
            "message": "An unexpected error occurred during request processing. Please try again later.",
            "path": request.url.path,
        },
    )


# Mount routers under /api and root (guarantees both /api/* and /* resolve in serverless runtimes)
app.include_router(health_router, prefix="/api")
app.include_router(locations_router, prefix="/api")
app.include_router(reports_router, prefix="/api")

app.include_router(health_router)
app.include_router(locations_router)
app.include_router(reports_router)


@app.get("/api")
@app.get("/api/")
def api_root():
    """Root metadata for HeatShield AI API on Vercel."""
    return {
        "name": "HeatShield AI API",
        "version": "1.0.0",
        "status": "online",
        "docs": "/api/docs",
        "endpoints": [
            "/api/health",
            "/api/config/status",
            "/api/locations",
            "/api/reports/analyze",
            "/api/docs",
        ],
    }


@app.get("/docs", include_in_schema=False)
def docs_redirect():
    return RedirectResponse(url="/api/docs")


@app.get("/redoc", include_in_schema=False)
def redoc_redirect():
    return RedirectResponse(url="/api/redoc")


FRONTEND_DIST_DIR = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"

if FRONTEND_DIST_DIR.exists() and (FRONTEND_DIST_DIR / "index.html").exists():
    logger.info("Serving compiled production frontend from: %s", FRONTEND_DIST_DIR)
    if (FRONTEND_DIST_DIR / "assets").exists():
        app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIST_DIR / "assets")), name="frontend_assets")

    @app.get("/")
    def serve_frontend_root():
        return FileResponse(str(FRONTEND_DIST_DIR / "index.html"))

    @app.get("/{full_path:path}")
    def serve_frontend_spa(full_path: str):
        if full_path.startswith("api/") or full_path in ("api", "docs", "redoc", "openapi.json"):
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"error": "NotFound", "detail": f"Route /{full_path} not found"}
            )
        file_path = FRONTEND_DIST_DIR / full_path
        if file_path.is_file():
            return FileResponse(str(file_path))
        return FileResponse(str(FRONTEND_DIST_DIR / "index.html"))
else:
    @app.get("/")
    def root():
        return {
            "name": "HeatShield AI API",
            "version": "1.0.0",
            "status": "online",
            "docs": "/docs",
            "endpoints": [
                "/api/health",
                "/api/config/status",
                "/api/locations",
                "/api/reports/analyze",
            ],
        }


if __name__ == "__main__":
    import uvicorn
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("backend.app.main:app", host=host, port=port, reload=True)
