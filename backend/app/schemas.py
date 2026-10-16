"""
Pydantic Request and Response Schemas for HeatShield AI API.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from backend.patterns.tool_selection import NormalizedDecision
from backend.services.bedrock_service import BedrockConfigStatus, BedrockRecommendation
from backend.tools.dispatcher import ToolExecutionResponse


class WorkflowStage(str, Enum):
    """The explicit state of the decision-driven analytical workflow."""
    DECISION_REJECTED = "DECISION_REJECTED"
    NEEDS_CLARIFICATION = "NEEDS_CLARIFICATION"
    TOOL_EXECUTED = "TOOL_EXECUTED"
    RECOMMENDATION_GENERATED = "RECOMMENDATION_GENERATED"
    BEDROCK_UNAVAILABLE = "BEDROCK_UNAVAILABLE"


class ReportAnalyzeRequest(BaseModel):
    """Payload for submitting an urban heat or environmental report."""
    report: str = Field(
        ...,
        min_length=5,
        max_length=2500,
        description="Environmental report narrative submitted by user or community sensor.",
        json_schema_extra={"example": "The neighborhood has high afternoon temperatures, low vegetation coverage, and a crowded bus stop."}
    )
    location: Optional[str] = Field(
        default=None,
        max_length=200,
        description="Optional municipal zone, neighborhood, or street intersection.",
        json_schema_extra={"example": "Downtown Central Transit Plaza"}
    )
    confidence_threshold: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Optional threshold override gating tool execution [0.0 - 1.0]."
    )
    extra_context: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional structured metadata (e.g., weather alert codes, sensor IDs)."
    )


class TraceStep(BaseModel):
    """Single audit step within the transparent execution trace."""
    step_number: int
    name: str
    status: str  # "completed", "skipped", "gated", "failed"
    duration_ms: float
    timestamp: str
    details: Dict[str, Any] = Field(default_factory=dict)


class ReportAnalyzeResponse(BaseModel):
    """Complete transparent response covering Decider routing, tool output, and generative recommendation."""
    report_id: str
    workflow_stage: WorkflowStage
    timestamp: str
    original_report: str
    location: str
    is_synthetic_dataset: bool = True
    dataset_label: str
    
    # 1. Decider Decision
    decision: NormalizedDecision
    
    # 2. Analytical Tool Execution (None if decision was gated)
    tool_execution: Optional[ToolExecutionResponse] = None
    
    # 3. Recommendation (None if tool execution was skipped/gated)
    recommendation: Optional[BedrockRecommendation] = None
    
    # 4. Transparent Audit Trace
    execution_trace: List[TraceStep]
    total_latency_ms: float


class HealthResponse(BaseModel):
    status: str = "healthy"
    version: str = "1.0.0"
    timestamp: str
    decider_status: str
    bedrock_status: str


class SystemConfigResponse(BaseModel):
    environment: str
    decider: Dict[str, Any]
    bedrock: BedrockConfigStatus
    synthetic_dataset: Dict[str, Any]


class SampleLocationItem(BaseModel):
    id: str
    name: str
    coordinates: Dict[str, float]
    description: str
    is_synthetic: bool = True
    synthetic_measurements: Dict[str, Any]


class LocationsResponse(BaseModel):
    total: int
    locations: List[SampleLocationItem]
    is_synthetic_dataset: bool = True
    dataset_disclaimer: str
