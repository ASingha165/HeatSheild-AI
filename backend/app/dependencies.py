"""
FastAPI dependency injection providers for HeatShield AI.
Allows clean override of Decider selector, Tool Dispatcher, and Bedrock Service in tests.
"""

from __future__ import annotations

import os
from typing import Optional

from backend.patterns.tool_selection import ConfidenceAwareToolSelector
from backend.services.bedrock_service import BedrockService

# Global singletons for production lifecycle
_tool_selector: Optional[ConfidenceAwareToolSelector] = None
_bedrock_service: Optional[BedrockService] = None


def get_tool_selector() -> ConfidenceAwareToolSelector:
    """Dependency provider returning the ConfidenceAwareToolSelector instance."""
    global _tool_selector
    if _tool_selector is None:
        checkpoint = os.getenv("DECIDER_MODEL_CHECKPOINT", "StrandsAgents/strands-decider-2B-hobson-v21")
        device = os.getenv("DECIDER_DEVICE", "cpu")
        threshold = float(os.getenv("DECIDER_CONFIDENCE_THRESHOLD", "0.60"))
        remote_url = os.getenv("DECIDER_REMOTE_URL", "").strip() or None

        _tool_selector = ConfidenceAwareToolSelector(
            checkpoint=checkpoint,
            device=device,
            confidence_threshold=threshold,
            remote_url=remote_url,
        )
    return _tool_selector


def set_tool_selector(selector: ConfidenceAwareToolSelector) -> None:
    """Setter allowing tests or app startup to inject a customized selector."""
    global _tool_selector
    _tool_selector = selector


def get_bedrock_service() -> BedrockService:
    """Dependency provider returning the BedrockService instance."""
    global _bedrock_service
    if _bedrock_service is None:
        region = os.getenv("AWS_REGION", "us-east-1")
        model_id = os.getenv("BEDROCK_MODEL_ID", "anthropic.claude-3-haiku-20240307-v1:0")
        _bedrock_service = BedrockService(region_name=region, model_id=model_id)
    return _bedrock_service


def set_bedrock_service(service: BedrockService) -> None:
    """Setter allowing tests or app startup to inject a customized Bedrock service."""
    global _bedrock_service
    _bedrock_service = service
