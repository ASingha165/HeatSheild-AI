"""
Reports API: Handles environmental report submission, Strands Decider routing,
tool execution, and Amazon Bedrock evidence-based recommendation generation.
"""

from __future__ import annotations

import logging
import time
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status

from backend.app.dependencies import get_bedrock_service, get_tool_selector
from backend.app.schemas import (
    ReportAnalyzeRequest,
    ReportAnalyzeResponse,
    TraceStep,
    WorkflowStage,
)
from backend.data.sample_dataset import DATASET_METADATA
from backend.patterns.tool_selection import (
    ConfidenceAwareToolSelector,
    EnvironmentalStateBuilder,
    ExecutionGate,
)
from backend.services.bedrock_service import BedrockService
from backend.tools.dispatcher import dispatch_tool

logger = logging.getLogger("heatshield.routes.reports")
router = APIRouter(prefix="/reports", tags=["Report Analysis"])

# Simple in-memory history cache for GET /api/reports/{report_id}
_REPORT_HISTORY: Dict[str, ReportAnalyzeResponse] = {}


@router.post("/analyze", response_model=ReportAnalyzeResponse, status_code=status.HTTP_200_OK)
def analyze_report(
    payload: ReportAnalyzeRequest,
    selector: ConfidenceAwareToolSelector = Depends(get_tool_selector),
    bedrock: BedrockService = Depends(get_bedrock_service),
) -> ReportAnalyzeResponse:
    """
    Executes the full confidence-aware environmental decision workflow:
    1. Validates the input report.
    2. Builds structured environmental state.
    3. Invokes Strands Decider 2B for typed analytical tool routing.
    4. Evaluates the confidence safety gate.
    5. Executes the selected analytical tool if accepted.
    6. Synthesizes final recommendation via Amazon Bedrock based strictly on tool results.
    7. Emits a transparent audit execution trace.
    """
    total_start = time.perf_counter()
    report_id = f"hs-{uuid.uuid4().hex[:8]}"
    trace: List[TraceStep] = []
    location_str = (payload.location or "").strip() or "Unspecified Location"

    # Step 1: Ingest Report & Build State
    step_start = time.perf_counter()
    state = EnvironmentalStateBuilder.build_state(
        report=payload.report,
        location=payload.location,
        extra_context=payload.extra_context,
    )
    step1_duration = round((time.perf_counter() - step_start) * 1000, 2)
    trace.append(
        TraceStep(
            step_number=1,
            name="State Construction",
            status="completed",
            duration_ms=step1_duration,
            timestamp=datetime.now(timezone.utc).isoformat(),
            details={
                "report_chars": len(payload.report),
                "location": location_str,
                "inferred_missing_fields": state.get("missing_information", []),
            },
        )
    )

    # Step 2: Invoke Strands Decider 2B
    step_start = time.perf_counter()
    decision = selector.select_action(
        state=state,
        confidence_threshold_override=payload.confidence_threshold,
    )
    step2_duration = round((time.perf_counter() - step_start) * 1000, 2)
    trace.append(
        TraceStep(
            step_number=2,
            name="Strands Decider 2B Selection",
            status="completed" if decision.selected_option_valid else "failed",
            duration_ms=step2_duration,
            timestamp=datetime.now(timezone.utc).isoformat(),
            details={
                "selected_action": decision.decision,
                "confidence": decision.confidence,
                "confidence_threshold": decision.confidence_threshold,
                "execution_gate": decision.execution_gate.value,
                "probabilities": decision.probabilities,
            },
        )
    )

    # Step 3: Enforce Execution Gate
    if decision.execution_gate == ExecutionGate.REJECT_INVALID_CHOICE:
        total_latency = round((time.perf_counter() - total_start) * 1000, 2)
        trace.append(
            TraceStep(
                step_number=3,
                name="Tool Execution Gate",
                status="failed",
                duration_ms=0.0,
                timestamp=datetime.now(timezone.utc).isoformat(),
                details={"reason": "Invalid action choice rejected by validator"},
            )
        )
        response = ReportAnalyzeResponse(
            report_id=report_id,
            workflow_stage=WorkflowStage.DECISION_REJECTED,
            timestamp=datetime.now(timezone.utc).isoformat(),
            original_report=payload.report,
            location=location_str,
            is_synthetic_dataset=True,
            dataset_label=DATASET_METADATA["dataset_label"],
            decision=decision,
            tool_execution=None,
            recommendation=None,
            execution_trace=trace,
            total_latency_ms=total_latency,
        )
        _REPORT_HISTORY[report_id] = response
        return response

    if decision.execution_gate == ExecutionGate.REQUEST_HUMAN_CLARIFICATION:
        total_latency = round((time.perf_counter() - total_start) * 1000, 2)
        trace.append(
            TraceStep(
                step_number=3,
                name="Tool Execution Gate",
                status="gated",
                duration_ms=0.0,
                timestamp=datetime.now(timezone.utc).isoformat(),
                details={
                    "gate": "REQUEST_HUMAN_CLARIFICATION",
                    "reason": "Model confidence below configured threshold; tool execution withheld for safety.",
                    "clarification_prompt": decision.clarification_prompt,
                },
            )
        )
        response = ReportAnalyzeResponse(
            report_id=report_id,
            workflow_stage=WorkflowStage.NEEDS_CLARIFICATION,
            timestamp=datetime.now(timezone.utc).isoformat(),
            original_report=payload.report,
            location=location_str,
            is_synthetic_dataset=True,
            dataset_label=DATASET_METADATA["dataset_label"],
            decision=decision,
            tool_execution=None,
            recommendation=None,
            execution_trace=trace,
            total_latency_ms=total_latency,
        )
        _REPORT_HISTORY[report_id] = response
        return response

    if decision.execution_gate == ExecutionGate.HALT_UNCONFIGURED:
        total_latency = round((time.perf_counter() - total_start) * 1000, 2)
        trace.append(
            TraceStep(
                step_number=3,
                name="Tool Execution Gate",
                status="failed",
                duration_ms=0.0,
                timestamp=datetime.now(timezone.utc).isoformat(),
                details={"reason": "Decider model is unconfigured"},
            )
        )
        response = ReportAnalyzeResponse(
            report_id=report_id,
            workflow_stage=WorkflowStage.DECISION_REJECTED,
            timestamp=datetime.now(timezone.utc).isoformat(),
            original_report=payload.report,
            location=location_str,
            is_synthetic_dataset=True,
            dataset_label=DATASET_METADATA["dataset_label"],
            decision=decision,
            tool_execution=None,
            recommendation=None,
            execution_trace=trace,
            total_latency_ms=total_latency,
        )
        _REPORT_HISTORY[report_id] = response
        return response

    # Step 4: Execute Selected Analytical Tool (Gate: PROCEED_TO_TOOL)
    step_start = time.perf_counter()
    tool_resp = dispatch_tool(
        action=decision.decision,
        report=payload.report,
        location=payload.location,
        context=payload.extra_context,
    )
    step4_duration = round((time.perf_counter() - step_start) * 1000, 2)
    trace.append(
        TraceStep(
            step_number=4,
            name=f"Analytical Tool: {decision.decision}",
            status="completed" if tool_resp.status == "success" else "failed",
            duration_ms=step4_duration,
            timestamp=datetime.now(timezone.utc).isoformat(),
            details={
                "tool_name": tool_resp.tool_name,
                "status": tool_resp.status,
                "error": tool_resp.error_message,
            },
        )
    )

    if tool_resp.status != "success":
        total_latency = round((time.perf_counter() - total_start) * 1000, 2)
        response = ReportAnalyzeResponse(
            report_id=report_id,
            workflow_stage=WorkflowStage.TOOL_EXECUTED,
            timestamp=datetime.now(timezone.utc).isoformat(),
            original_report=payload.report,
            location=location_str,
            is_synthetic_dataset=True,
            dataset_label=DATASET_METADATA["dataset_label"],
            decision=decision,
            tool_execution=tool_resp,
            recommendation=None,
            execution_trace=trace,
            total_latency_ms=total_latency,
        )
        _REPORT_HISTORY[report_id] = response
        return response

    # Step 5: Synthesize Recommendation via Amazon Bedrock
    step_start = time.perf_counter()
    recommendation = bedrock.generate_recommendation(
        report=payload.report,
        decider_action=decision.decision,
        tool_output=tool_resp.output,
        missing_information=state.get("missing_information", []),
        location=payload.location,
    )
    step5_duration = round((time.perf_counter() - step_start) * 1000, 2)
    
    stage = (
        WorkflowStage.RECOMMENDATION_GENERATED
        if recommendation.is_live_bedrock
        else WorkflowStage.BEDROCK_UNAVAILABLE
    )

    trace.append(
        TraceStep(
            step_number=5,
            name="Amazon Bedrock Recommendation",
            status="completed",
            duration_ms=step5_duration,
            timestamp=datetime.now(timezone.utc).isoformat(),
            details={
                "model_id": recommendation.model_id,
                "is_live_bedrock": recommendation.is_live_bedrock,
                "status": recommendation.status,
                "recommended_step": recommendation.recommended_next_step,
            },
        )
    )

    total_latency = round((time.perf_counter() - total_start) * 1000, 2)

    response = ReportAnalyzeResponse(
        report_id=report_id,
        workflow_stage=stage,
        timestamp=datetime.now(timezone.utc).isoformat(),
        original_report=payload.report,
        location=location_str,
        is_synthetic_dataset=True,
        dataset_label=DATASET_METADATA["dataset_label"],
        decision=decision,
        tool_execution=tool_resp,
        recommendation=recommendation,
        execution_trace=trace,
        total_latency_ms=total_latency,
    )
    _REPORT_HISTORY[report_id] = response
    return response


@router.get("/{report_id}", response_model=ReportAnalyzeResponse)
def get_report_by_id(report_id: str) -> ReportAnalyzeResponse:
    """Retrieves a previously analyzed report by ID."""
    if report_id not in _REPORT_HISTORY:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report with ID '{report_id}' not found.",
        )
    return _REPORT_HISTORY[report_id]
