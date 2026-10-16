"""
Health and System Configuration endpoints for HeatShield AI.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from fastapi import APIRouter, Depends

from backend.app.dependencies import get_bedrock_service, get_tool_selector
from backend.app.schemas import HealthResponse, SystemConfigResponse
from backend.data.sample_dataset import DATASET_METADATA
from backend.patterns.tool_selection import ConfidenceAwareToolSelector
from backend.services.bedrock_service import BedrockService

router = APIRouter(tags=["System Health & Config"])


@router.get("/health", response_model=HealthResponse)
def get_health(
    selector: ConfidenceAwareToolSelector = Depends(get_tool_selector),
    bedrock: BedrockService = Depends(get_bedrock_service),
) -> HealthResponse:
    """Returns application health and subsystem statuses."""
    decider_status = "ready" if selector._engine_initialized or selector.remote_url else "unloaded"
    bedrock_cfg = bedrock.get_config_status()
    bedrock_status = "configured" if bedrock_cfg.is_configured else "unconfigured_dev_mode"

    return HealthResponse(
        status="healthy",
        version="1.0.0",
        timestamp=datetime.now(timezone.utc).isoformat(),
        decider_status=decider_status,
        bedrock_status=bedrock_status,
    )


@router.get("/config/status", response_model=SystemConfigResponse)
def get_config_status(
    selector: ConfidenceAwareToolSelector = Depends(get_tool_selector),
    bedrock: BedrockService = Depends(get_bedrock_service),
) -> SystemConfigResponse:
    """
    Returns public non-sensitive configuration status for Strands Decider and Bedrock.
    Never exposes API secrets, tokens, or local credentials.
    """
    env = os.getenv("ENVIRONMENT", "development")
    decider_info = {
        "checkpoint": selector.checkpoint,
        "device": selector.device,
        "confidence_threshold": selector.confidence_threshold,
        "remote_url": selector.remote_url,
        "is_engine_loaded": selector._engine_initialized,
    }
    bedrock_info = bedrock.get_config_status()

    return SystemConfigResponse(
        environment=env,
        decider=decider_info,
        bedrock=bedrock_info,
        synthetic_dataset=DATASET_METADATA,
    )
