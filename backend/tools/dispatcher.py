"""
Tool Dispatcher for HeatShield AI.

Dispatches execution to the appropriate analytical tool based on Strands Decider selection.
"""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, Optional, Union
from pydantic import BaseModel

from backend.patterns.tool_selection import AnalyticalAction
from backend.tools.analyze_heat import HeatAnalysisResult, analyze_heat
from backend.tools.check_exposure import ExposureAnalysisResult, check_exposure
from backend.tools.check_vegetation import VegetationAnalysisResult, check_vegetation
from backend.tools.compare_interventions import (
    InterventionComparisonResult,
    compare_interventions,
)
from backend.tools.request_more_data import (
    ClarificationRequestResult,
    request_more_data,
)

logger = logging.getLogger("heatshield.tools.dispatcher")

ToolOutput = Union[
    HeatAnalysisResult,
    VegetationAnalysisResult,
    ExposureAnalysisResult,
    InterventionComparisonResult,
    ClarificationRequestResult,
]


class ToolExecutionResponse(BaseModel):
    tool_name: str
    status: str  # "success" | "error"
    execution_time_ms: float
    output: Dict[str, Any]
    error_message: Optional[str] = None


def dispatch_tool(
    action: str,
    report: str,
    location: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
) -> ToolExecutionResponse:
    """
    Safely executes the requested analytical tool and returns structured results.
    Validates the action name against allowed AnalyticalAction values.
    """
    start_time = time.perf_counter()

    # Tool mapping
    registry = {
        AnalyticalAction.ANALYZE_HEAT.value: analyze_heat,
        AnalyticalAction.CHECK_VEGETATION.value: check_vegetation,
        AnalyticalAction.CHECK_EXPOSURE.value: check_exposure,
        AnalyticalAction.COMPARE_INTERVENTIONS.value: compare_interventions,
        AnalyticalAction.REQUEST_MORE_DATA.value: request_more_data,
    }

    if action not in registry:
        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
        err = f"Unrecognized action '{action}'. Allowed actions: {list(registry.keys())}"
        logger.error(err)
        return ToolExecutionResponse(
            tool_name=action,
            status="error",
            execution_time_ms=elapsed_ms,
            output={},
            error_message=err,
        )

    try:
        tool_fn = registry[action]
        logger.info("Executing analytical tool: %s", action)
        result: ToolOutput = tool_fn(report=report, location=location, context=context)
        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)

        return ToolExecutionResponse(
            tool_name=action,
            status="success",
            execution_time_ms=elapsed_ms,
            output=result.model_dump(),
            error_message=None,
        )

    except Exception as exc:
        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
        err = f"Execution of tool '{action}' failed: {type(exc).__name__}: {str(exc)}"
        logger.error(err)
        return ToolExecutionResponse(
            tool_name=action,
            status="error",
            execution_time_ms=elapsed_ms,
            output={},
            error_message=err,
        )
