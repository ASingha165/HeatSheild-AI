"""
API integration and endpoint tests for HeatShield AI.
Uses FastAPI TestClient with dependency injection to verify end-to-end orchestration,
all five analytical actions, error handling, confidence gating, and status consistency.
"""

from unittest.mock import MagicMock, patch
import pytest
from fastapi.testclient import TestClient

from backend.app.dependencies import get_bedrock_service, get_tool_selector
from backend.app.main import app
from backend.app.schemas import WorkflowStage
from backend.patterns.tool_selection import (
    AnalyticalAction,
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
from backend.tools.dispatcher import ToolExecutionResponse

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
    assert "secret_access_key" not in raw_text
    assert "aws_secret" not in raw_text


def test_health_and_config_status_consistency():
    """Confirms /api/health and /api/config/status report consistent decider readiness."""
    health_resp = client.get("/api/health")
    config_resp = client.get("/api/config/status")
    assert health_resp.status_code == 200
    assert config_resp.status_code == 200

    h_data = health_resp.json()
    c_data = config_resp.json()

    # If decider is reported ready in health, config must report is_engine_loaded=true, and vice versa
    is_ready_in_health = h_data["decider_status"] == "ready"
    is_loaded_in_config = c_data["decider"]["is_engine_loaded"]
    assert is_ready_in_health == is_loaded_in_config


def test_decider_status_before_and_after_initialization():
    """Confirms is_engine_loaded and decider_status accurately transition upon engine initialization."""
    # Create clean uninitialized selector
    selector = ConfidenceAwareToolSelector(
        checkpoint="test-checkpoint",
        device="cpu",
        confidence_threshold=0.60,
    )
    assert selector.is_ready is False
    assert selector.is_engine_loaded is False

    app.dependency_overrides[get_tool_selector] = lambda: selector
    try:
        # Before initialization: must report unloaded / false
        h_resp = client.get("/api/health")
        c_resp = client.get("/api/config/status")
        assert h_resp.json()["decider_status"] == "unloaded"
        assert c_resp.json()["decider"]["is_engine_loaded"] is False

        # Simulate engine initialization
        selector._engine = MagicMock()
        selector._engine_initialized = True
        assert selector.is_ready is True
        assert selector.is_engine_loaded is True

        # After initialization: must report ready / true
        h_resp = client.get("/api/health")
        c_resp = client.get("/api/config/status")
        assert h_resp.json()["decider_status"] == "ready"
        assert c_resp.json()["decider"]["is_engine_loaded"] is True
    finally:
        app.dependency_overrides.clear()


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


@pytest.mark.parametrize(
    "action",
    [
        AnalyticalAction.ANALYZE_HEAT.value,
        AnalyticalAction.CHECK_VEGETATION.value,
        AnalyticalAction.CHECK_EXPOSURE.value,
        AnalyticalAction.COMPARE_INTERVENTIONS.value,
        AnalyticalAction.REQUEST_MORE_DATA.value,
    ],
)
def test_analyze_report_valid_flow_for_all_five_actions(action: str):
    """POST /api/reports/analyze completes end-to-end workflow for all 5 analytical actions."""
    mock_selector = MagicMock(spec=ConfidenceAwareToolSelector)
    mock_selector.select_action.return_value = NormalizedDecision(
        decision=action,
        confidence=0.85,
        latency_ms=35.0,
        status=DecisionStatus.ACCEPTED,
        probabilities={action: 0.85},
        selected_option_valid=True,
        confidence_threshold=0.60,
        is_above_threshold=True,
        execution_gate=ExecutionGate.PROCEED_TO_TOOL,
        clarification_prompt=None,
        state_summary={"report": f"Testing action {action}"},
    )

    mock_bedrock = MagicMock(spec=BedrockService)
    mock_bedrock.generate_recommendation.return_value = BedrockRecommendation(
        summary=f"Synthesized evidence for action {action}.",
        recommended_next_step=f"Prioritize actionable step for {action}.",
        supporting_evidence=[f"Empirical evidence for {action}."],
        assumptions=["Standard operational assumptions."],
        limitations=["Municipal human review required."],
        follow_up_actions=["Review field telemetry."],
        model_id="global.amazon.nova-2-lite-v1:0",
        is_live_bedrock=True,
        data_provenance="SYNTHETIC_DEV_DATASET_V1",
        latency_ms=115.0,
        status="success",
    )

    app.dependency_overrides[get_tool_selector] = lambda: mock_selector
    app.dependency_overrides[get_bedrock_service] = lambda: mock_bedrock

    try:
        response = client.post(
            "/api/reports/analyze",
            json={
                "report": f"Detailed environmental report triggering {action}.",
                "location": "Downtown Central Transit Plaza",
            },
        )
        assert response.status_code == 200
        data = response.json()

        # 1. Workflow stage
        assert data["workflow_stage"] == WorkflowStage.RECOMMENDATION_GENERATED.value

        # 2. Decider decision
        assert data["decision"]["decision"] == action
        assert data["decision"]["confidence"] == 0.85
        assert data["decision"]["execution_gate"] == "PROCEED_TO_TOOL"

        # 3. Tool execution output matches action
        assert data["tool_execution"] is not None
        assert data["tool_execution"]["status"] == "success"
        assert data["tool_execution"]["tool_name"] == action
        tool_out = data["tool_execution"]["output"]
        assert tool_out["is_synthetic_data"] is True

        # Action-specific output invariant checks
        if action == "ANALYZE_HEAT":
            assert "observed_ambient_temp_c" in tool_out
            assert "observed_surface_temp_c" in tool_out
            assert "heat_severity_level" in tool_out
        elif action == "CHECK_VEGETATION":
            assert "canopy_coverage_pct" in tool_out
            assert "canopy_deficit_pct" in tool_out
            assert "deficit_classification" in tool_out
        elif action == "CHECK_EXPOSURE":
            assert "transit_stops_count" in tool_out
            assert "daily_transit_commuters" in tool_out
            assert "overall_exposure_level" in tool_out
        elif action == "COMPARE_INTERVENTIONS":
            assert "interventions" in tool_out
            assert len(tool_out["interventions"]) == 4
            assert "recommended_primary_intervention" in tool_out
        elif action == "REQUEST_MORE_DATA":
            assert "missing_parameters" in tool_out
            assert "suggested_user_questions" in tool_out

        # 4. Bedrock recommendation received actual tool output
        assert data["recommendation"] is not None
        assert data["recommendation"]["is_live_bedrock"] is True
        assert data["recommendation"]["status"] == "success"

        # 5. Execution trace
        assert len(data["execution_trace"]) >= 4
        step_names = [s["name"] for s in data["execution_trace"]]
        assert any("State Construction" in s for s in step_names)
        assert any("Strands Decider 2B" in s for s in step_names)
        assert any(action in s for s in step_names)
        assert any("Amazon Bedrock" in s for s in step_names)

        # 6. History lookup works
        report_id = data["report_id"]
        hist_resp = client.get(f"/api/reports/{report_id}")
        assert hist_resp.status_code == 200
        assert hist_resp.json()["report_id"] == report_id

    finally:
        app.dependency_overrides.clear()


def test_analyze_report_tool_failure_workflow():
    """When analytical tool execution fails, Bedrock is safely bypassed and status is TOOL_EXECUTED."""
    mock_selector = MagicMock(spec=ConfidenceAwareToolSelector)
    mock_selector.select_action.return_value = NormalizedDecision(
        decision="ANALYZE_HEAT",
        confidence=0.91,
        latency_ms=25.0,
        status=DecisionStatus.ACCEPTED,
        probabilities={"ANALYZE_HEAT": 0.91},
        selected_option_valid=True,
        confidence_threshold=0.60,
        is_above_threshold=True,
        execution_gate=ExecutionGate.PROCEED_TO_TOOL,
        clarification_prompt=None,
        state_summary={},
    )

    mock_bedrock = MagicMock(spec=BedrockService)

    app.dependency_overrides[get_tool_selector] = lambda: mock_selector
    app.dependency_overrides[get_bedrock_service] = lambda: mock_bedrock

    # Patch dispatch_tool to simulate tool failure
    failed_tool_resp = ToolExecutionResponse(
        tool_name="ANALYZE_HEAT",
        status="error",
        execution_time_ms=8.0,
        output={},
        error_message="Sensor telemetry offline; reading failed.",
    )

    with patch("backend.app.routes.reports.dispatch_tool", return_value=failed_tool_resp):
        try:
            response = client.post(
                "/api/reports/analyze",
                json={"report": "High heat conditions near sensor."},
            )
            assert response.status_code == 200
            data = response.json()

            # Workflow halted at TOOL_EXECUTED
            assert data["workflow_stage"] == WorkflowStage.TOOL_EXECUTED.value
            assert data["tool_execution"]["status"] == "error"
            assert data["tool_execution"]["error_message"] == "Sensor telemetry offline; reading failed."

            # Bedrock was safely NOT invoked
            assert data["recommendation"] is None
            mock_bedrock.generate_recommendation.assert_not_called()

            # Trace logs tool failure
            tool_trace = [s for s in data["execution_trace"] if "Analytical Tool" in s["name"]]
            assert len(tool_trace) == 1
            assert tool_trace[0]["status"] == "failed"

        finally:
            app.dependency_overrides.clear()


def test_analyze_report_unconfigured_decider_gate():
    """HALT_UNCONFIGURED gate safely rejects decision without executing tools or Bedrock."""
    mock_selector = MagicMock(spec=ConfidenceAwareToolSelector)
    mock_selector.select_action.return_value = NormalizedDecision(
        decision="NONE",
        confidence=0.0,
        latency_ms=0.0,
        status=DecisionStatus.UNCONFIGURED,
        probabilities={},
        selected_option_valid=False,
        confidence_threshold=0.60,
        is_above_threshold=False,
        execution_gate=ExecutionGate.HALT_UNCONFIGURED,
        clarification_prompt="Decider model weights unconfigured.",
        state_summary={},
    )

    mock_bedrock = MagicMock(spec=BedrockService)
    app.dependency_overrides[get_tool_selector] = lambda: mock_selector
    app.dependency_overrides[get_bedrock_service] = lambda: mock_bedrock

    try:
        response = client.post(
            "/api/reports/analyze",
            json={"report": "Sample report for unconfigured decider."},
        )
        assert response.status_code == 200
        data = response.json()

        assert data["workflow_stage"] == WorkflowStage.DECISION_REJECTED.value
        assert data["tool_execution"] is None
        assert data["recommendation"] is None
        mock_bedrock.generate_recommendation.assert_not_called()

        gate_trace = [s for s in data["execution_trace"] if s["name"] == "Tool Execution Gate"]
        assert len(gate_trace) == 1
        assert gate_trace[0]["status"] == "failed"
        assert gate_trace[0]["details"]["reason"] == "Decider model is unconfigured"

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


def test_analyze_report_with_structured_extra_context_measurements():
    """POST /api/reports/analyze must accurately ingest, normalize, and propagate structured measurements."""
    extra = {
        "data_source": "SYNTHETIC_DEMO",
        "dataset_label": "SYNTHETIC_DEV_DATASET_V1",
        "ambient_temperature_c": 38.2,
        "surface_temperature_c": 51.0,
        "canopy_coverage_pct": 6.5,
        "ndvi_index": 0.12,
        "impervious_surface_pct": 88.0,
        "daily_transit_commuters": 14500,
        "transit_stops_count": 8,
        "unshaded_waiting_areas": 5,
    }
    payload = {
        "report": "Demonstration scenario: Transit plaza has high pavement heat, low canopy, and high commuter exposure.",
        "location": "Downtown Central Transit Plaza",
        "confidence_threshold": 0.60,
        "extra_context": extra,
    }

    response = client.post("/api/reports/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()

    # 1. State construction audit
    state_summary = data["decision"]["state_summary"]
    assert "38.2°C" in state_summary["temperature_observations"]
    assert "51.0°C" in state_summary["temperature_observations"]
    assert "No sensor telemetry available in report" not in state_summary["temperature_observations"]

    assert "6.5%" in state_summary["vegetation_indicators"]
    assert "0.12" in state_summary["vegetation_indicators"]
    assert "No vegetation metrics provided" not in state_summary["vegetation_indicators"]

    assert "14,500" in state_summary["exposure_indicators"]
    assert "No population exposure details provided" not in state_summary["exposure_indicators"]

    # 2. Reconciled missing information
    assert state_summary["missing_information"] == []

    # 3. Execution trace confirms state construction
    trace_steps = {s["name"]: s for s in data["execution_trace"]}
    assert "State Construction" in trace_steps
    assert trace_steps["State Construction"]["status"] == "completed"

    # 4. If an analytical tool executed, verify it consumed normalized measurements
    if data["tool_execution"] and data["tool_execution"]["status"] == "success":
        tool_out = data["tool_execution"]["output"]
        if data["decision"]["decision"] == "ANALYZE_HEAT":
            assert tool_out["observed_ambient_temp_c"] == 38.2
            assert tool_out["observed_surface_temp_c"] == 51.0
        elif data["decision"]["decision"] == "CHECK_VEGETATION":
            assert tool_out["canopy_coverage_pct"] == 6.5
            assert tool_out["ndvi_index"] == 0.12
        elif data["decision"]["decision"] == "CHECK_EXPOSURE":
            assert tool_out["daily_transit_commuters"] == 14500
