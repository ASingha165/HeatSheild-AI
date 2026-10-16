"""
Unit tests for HeatShield AI analytical tools and dispatcher.
Validates structured outputs, error handling, and synthetic data labelling.
"""

from unittest.mock import patch
import pytest

from backend.tools.analyze_heat import analyze_heat, HeatAnalysisResult
from backend.tools.check_exposure import check_exposure, ExposureAnalysisResult
from backend.tools.check_vegetation import check_vegetation, VegetationAnalysisResult
from backend.tools.compare_interventions import compare_interventions, InterventionComparisonResult
from backend.tools.request_more_data import request_more_data, ClarificationRequestResult
from backend.tools.dispatcher import dispatch_tool, ToolExecutionResponse


def test_analyze_heat_returns_structured_metrics():
    """ANALYZE_HEAT must return structured thermal metrics and clear synthetic labelling."""
    result = analyze_heat(
        report="High afternoon temperatures observed across the concrete square.",
        location="Downtown Central Transit Plaza",
    )
    assert isinstance(result, HeatAnalysisResult)
    assert result.tool_name == "ANALYZE_HEAT"
    assert result.status == "success"
    assert result.is_synthetic_data is True
    assert "SYNTHETIC" in result.data_label
    assert result.observed_ambient_temp_c > 20.0
    assert result.observed_surface_temp_c >= result.observed_ambient_temp_c
    assert result.heat_severity_level in ["LOW", "MODERATE", "HIGH", "SEVERE", "EXTREME"]
    assert len(result.known_limitations) >= 1


def test_check_vegetation_returns_canopy_metrics():
    """CHECK_VEGETATION must return canopy deficit and cooling potential."""
    result = check_vegetation(
        report="Low tree canopy, wide asphalt streets.",
        location="Eastside Logistics & Industrial Corridor",
    )
    assert isinstance(result, VegetationAnalysisResult)
    assert result.tool_name == "CHECK_VEGETATION"
    assert result.is_synthetic_data is True
    assert result.canopy_coverage_pct >= 0.0
    assert result.target_municipal_canopy_pct == 30.0
    assert result.canopy_deficit_pct >= 0.0
    assert result.estimated_cooling_potential_c > 0.0
    assert len(result.recommended_planting_priorities) >= 1


def test_check_exposure_returns_vulnerability_indicators():
    """CHECK_EXPOSURE must evaluate transit stops and sensitive facilities."""
    result = check_exposure(
        report="Crowded bus stop with unshaded waiting area.",
        location="Downtown Central Transit Plaza",
    )
    assert isinstance(result, ExposureAnalysisResult)
    assert result.tool_name == "CHECK_EXPOSURE"
    assert result.is_synthetic_data is True
    assert result.transit_stops_count > 0
    assert result.daily_transit_commuters > 0
    assert result.overall_exposure_level in ["CRITICAL_EXPOSURE", "ELEVATED_EXPOSURE", "CONTROLLED_EXPOSURE"]
    assert len(result.vulnerable_facilities) >= 1


def test_compare_interventions_evaluates_options():
    """COMPARE_INTERVENTIONS must evaluate 4 distinct cooling interventions with assumptions."""
    result = compare_interventions(
        report="Need actionable cooling strategies for unshaded commuter corridor.",
        location="Southside Open Market & Pedestrian Zone",
    )
    assert isinstance(result, InterventionComparisonResult)
    assert result.tool_name == "COMPARE_INTERVENTIONS"
    assert result.is_synthetic_data is True
    assert len(result.interventions) == 4
    
    categories = [i.category for i in result.interventions]
    assert "Green Infrastructure" in categories
    assert "Physical Infrastructure" in categories
    assert "Materials & Surface Modification" in categories

    for opt in result.interventions:
        assert opt.estimated_cooling_delta_c > 0.0
        assert len(opt.transparent_assumptions) >= 1


def test_request_more_data_identifies_gaps():
    """REQUEST_MORE_DATA must identify missing telemetry and formulate questions."""
    result = request_more_data(
        report="It felt uncomfortably hot.",
        location=None,
    )
    assert isinstance(result, ClarificationRequestResult)
    assert result.tool_name == "REQUEST_MORE_DATA"
    assert result.is_synthetic_data is True
    assert len(result.missing_parameters) >= 1
    assert len(result.suggested_user_questions) >= 1
    assert len(result.suggested_telemetry_sources) >= 1


def test_dispatcher_successful_dispatch():
    """Dispatcher should successfully execute any registered analytical action."""
    for action in [
        "ANALYZE_HEAT",
        "CHECK_VEGETATION",
        "CHECK_EXPOSURE",
        "COMPARE_INTERVENTIONS",
        "REQUEST_MORE_DATA",
    ]:
        resp = dispatch_tool(
            action=action,
            report="Sample urban heat report with bus stops and low canopy.",
            location="Downtown Central Transit Plaza",
        )
        assert isinstance(resp, ToolExecutionResponse)
        assert resp.status == "success"
        assert resp.tool_name == action
        assert resp.output["is_synthetic_data"] is True
        assert resp.execution_time_ms >= 0.0
        assert resp.error_message is None


def test_dispatcher_rejects_invalid_tool():
    """Dispatcher should cleanly reject unknown action names without throwing."""
    resp = dispatch_tool(
        action="FLY_AIRPLANE",
        report="Sample report",
    )
    assert resp.status == "error"
    assert "Unrecognized action" in resp.error_message
    assert resp.output == {}


def test_dispatcher_handles_tool_internal_failure():
    """Dispatcher should catch exceptions raised inside a tool and return structured error."""
    with patch("backend.tools.dispatcher.analyze_heat", side_effect=ValueError("Simulated sensor failure")):
        resp = dispatch_tool(
            action="ANALYZE_HEAT",
            report="Sample report",
        )
        assert resp.status == "error"
        assert "Simulated sensor failure" in resp.error_message
        assert resp.tool_name == "ANALYZE_HEAT"
