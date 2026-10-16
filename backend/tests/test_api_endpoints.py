"""
API integration and endpoint tests for HeatShield AI.
Uses FastAPI TestClient with dependency injection to verify end-to-end orchestration.
"""

from unittest.mock import MagicMock
import pytest
from fastapi.testclient import TestClient

from backend.app.dependencies import get_bedrock_service, get_tool_selector
from backend.app.main import app
from backend.app.schemas import WorkflowStage
from backend.patterns.tool_selection import (
    ConfidenceAwareToolSelector,
    DecisionStatus,
    ExecutionGate,
    NormalizedDecision,
)
from backend.services.bedrock_service import (
    BedrockConfigStatus,
    BedrockRecommendation,
    BedrockService,
)

client = TestClient(app)


def test_health_endpoint():
    """GET /api/health returns 200 with service health info."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["version"] == "1.0.0"
    assert "decider_status" in data
    assert "bedrock_status" in data


def test_config_status_endpoint_never_exposes_secrets():
    """GET /api/config/status returns non-sensitive system status without credential leaks."""
    response = client.get("/api/config/status")
    assert response.status_code == 200
    data = response.json()
    assert "environment" in data
    assert "decider" in data
    assert "bedrock" in data
    assert "synthetic_dataset" in data

    # Verify no secret keywords leaked in response text
    raw_text = response.text.lower()
    assert "secret" not in raw_text or "secret_access_key" not in raw_text
    assert "aws_secret" not in raw_text


def test_locations_endpoint():
    """GET /api/locations returns sample neighborhoods tagged as synthetic data."""
    response = client.get("/api/locations")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 4
    assert data["is_synthetic_dataset"] is True
    assert len(data["locations"]) >= 4

    first = data["locations"][0]
    assert "coordinates" in first
    assert "lat" in first["coordinates"]
    assert "lng" in first["coordinates"]
    assert first["is_synthetic"] is True


def test_analyze_report_valid_flow_with_mocked_services():
    """POST /api/reports/analyze completes end-to-end workflow when decision is above threshold."""
    # Create mock selector that selects CHECK_EXPOSURE with high confidence
    mock_selector = MagicMock(spec=ConfidenceAwareToolSelector)
    mock_selector.select_action.return_value = NormalizedDecision(
        decision="CHECK_EXPOSURE",
        confidence=0.88,
        latency_ms=45.2,
        status=DecisionStatus.ACCEPTED,
        probabilities={"CHECK_EXPOSURE": 0.88, "ANALYZE_HEAT": 0.05, "CHECK_VEGETATION": 0.07},
        selected_option_valid=True,
        confidence_threshold=0.60,
        is_above_threshold=True,
        execution_gate=ExecutionGate.PROCEED_TO_TOOL,
        clarification_prompt=None,
        state_summary={"report": "Bus stop with seniors"},
    )

    # Create mock Bedrock service
    mock_bedrock = MagicMock(spec=BedrockService)
    mock_bedrock.generate_recommendation.return_value = BedrockRecommendation(
        summary="High commuter exposure identified at transit stops.",
        recommended_next_step="Install engineered solar-reflective bus shelters.",
        supporting_evidence=["8 unshaded stops detected."],
        assumptions=["Assumes standard peak morning/afternoon commute."],
        limitations=["Dataset is synthetic."],
        follow_up_actions=["Submit capital grant application."],
        model_id="anthropic.claude-3-haiku-20240307-v1:0",
        is_live_bedrock=True,
        data_provenance="SYNTHETIC_DEV_DATASET_V1",
        latency_ms=120.5,
        status="success",
    )

    # Override dependencies
    app.dependency_overrides[get_tool_selector] = lambda: mock_selector
    app.dependency_overrides[get_bedrock_service] = lambda: mock_bedrock

    try:
        response = client.post(
            "/api/reports/analyze",
            json={
                "report": "High heat conditions with seniors waiting at an unshaded central bus stop.",
                "location": "Downtown Central Transit Plaza",
            },
        )
        assert response.status_code == 200
        data = response.json()

        assert data["workflow_stage"] == WorkflowStage.RECOMMENDATION_GENERATED.value
        assert data["decision"]["decision"] == "CHECK_EXPOSURE"
        assert data["decision"]["confidence"] == 0.88
        assert data["tool_execution"]["status"] == "success"
        assert data["tool_execution"]["tool_name"] == "CHECK_EXPOSURE"
        assert data["recommendation"]["is_live_bedrock"] is True
        assert len(data["execution_trace"]) >= 4

        # Verify trace step order
        step_names = [s["name"] for s in data["execution_trace"]]
        assert "State Construction" in step_names[0]
        assert "Strands Decider 2B Selection" in step_names[1]
        assert "CHECK_EXPOSURE" in step_names[2]
        assert "Amazon Bedrock Recommendation" in step_names[3]

        report_id = data["report_id"]
        # Verify GET /api/reports/{report_id}
        fetch_resp = client.get(f"/api/reports/{report_id}")
        assert fetch_resp.status_code == 200
        assert fetch_resp.json()["report_id"] == report_id

    finally:
        app.dependency_overrides.clear()


def test_analyze_report_low_confidence_gated_flow():
    """POST /api/reports/analyze halts at confidence gate when confidence < threshold."""
    mock_selector = MagicMock(spec=ConfidenceAwareToolSelector)
    mock_selector.select_action.return_value = NormalizedDecision(
        decision="CHECK_VEGETATION",
        confidence=0.45,  # Below threshold 0.60
        latency_ms=50.1,
        status=DecisionStatus.REQUIRES_CLARIFICATION,
        probabilities={"CHECK_VEGETATION": 0.45, "ANALYZE_HEAT": 0.35},
        selected_option_valid=True,
        confidence_threshold=0.60,
        is_above_threshold=False,
        execution_gate=ExecutionGate.REQUEST_HUMAN_CLARIFICATION,
        clarification_prompt="Confidence 0.45 is below 0.60 threshold. Safe clarification required.",
        state_summary={"report": "Moderate weather"},
    )

    app.dependency_overrides[get_tool_selector] = lambda: mock_selector

    try:
        response = client.post(
            "/api/reports/analyze",
            json={
                "report": "Moderate weather with ambiguous tree cover.",
                "location": "Riverside Parkway",
            },
        )
        assert response.status_code == 200
        data = response.json()

        # Must be in NEEDS_CLARIFICATION stage
        assert data["workflow_stage"] == WorkflowStage.NEEDS_CLARIFICATION.value
        assert data["tool_execution"] is None  # Tool was safely NOT executed
        assert data["recommendation"] is None  # Recommendation was NOT executed
        assert data["decision"]["execution_gate"] == "REQUEST_HUMAN_CLARIFICATION"

        # Execution trace must log gating event
        gate_trace = [s for s in data["execution_trace"] if s["name"] == "Tool Execution Gate"]
        assert len(gate_trace) == 1
        assert gate_trace[0]["status"] == "gated"

    finally:
        app.dependency_overrides.clear()


def test_analyze_report_invalid_choice_rejected_flow():
    """POST /api/reports/analyze marks workflow DECISION_REJECTED if model choice is invalid."""
    mock_selector = MagicMock(spec=ConfidenceAwareToolSelector)
    mock_selector.select_action.return_value = NormalizedDecision(
        decision="INVALID_TOOL",
        confidence=0.99,
        latency_ms=30.0,
        status=DecisionStatus.REJECTED_INVALID,
        probabilities={},
        selected_option_valid=False,
        confidence_threshold=0.60,
        is_above_threshold=False,
        execution_gate=ExecutionGate.REJECT_INVALID_CHOICE,
        clarification_prompt="Action 'INVALID_TOOL' is not allowed.",
        state_summary={},
    )

    app.dependency_overrides[get_tool_selector] = lambda: mock_selector

    try:
        response = client.post(
            "/api/reports/analyze",
            json={"report": "Some report with invalid output."},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["workflow_stage"] == WorkflowStage.DECISION_REJECTED.value
        assert data["tool_execution"] is None

    finally:
        app.dependency_overrides.clear()


def test_analyze_report_validation_errors():
    """POST /api/reports/analyze returns 422 if report is too short or missing."""
    # Report too short (< 5 chars)
    response = client.post("/api/reports/analyze", json={"report": "hi"})
    assert response.status_code == 422

    # Empty payload
    response = client.post("/api/reports/analyze", json={})
    assert response.status_code == 422


def test_get_unknown_report_returns_404():
    """GET /api/reports/non-existent-id returns 404."""
    response = client.get("/api/reports/non-existent-id")
    assert response.status_code == 404
