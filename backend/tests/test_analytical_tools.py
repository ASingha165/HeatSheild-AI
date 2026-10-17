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


def test_analytical_tools_consume_context_measurements():
    """All analytical tools must consume structured measurements passed in context instead of default sample values."""
    custom_context = {
        "data_source": "CUSTOM_SENSOR_NETWORK",
        "dataset_label": "CUSTOM_TEST_DATASET_V2",
        "ambient_temperature_c": 41.5,
        "surface_temperature_c": 56.2,
        "heat_index_c": 44.8,
        "canopy_coverage_pct": 4.5,
        "ndvi_index": 0.07,
        "impervious_surface_pct": 92.0,
        "daily_transit_commuters": 22000,
        "transit_stops_count": 12,
        "unshaded_waiting_areas": 7,
    }

    # 1. analyze_heat
    heat_res = analyze_heat(
        report="High radiant heat test",
        location="Zone B",
        context=custom_context,
    )
    assert heat_res.observed_ambient_temp_c == 41.5
    assert heat_res.observed_surface_temp_c == 56.2
    assert heat_res.heat_index_c == 44.8
    assert heat_res.heat_severity_level == "EXTREME"
    assert heat_res.location_name == "Zone B"
    assert heat_res.data_label == "CUSTOM_TEST_DATASET_V2"

    # 2. check_vegetation
    veg_res = check_vegetation(
        report="Canopy check",
        location="Zone B",
        context=custom_context,
    )
    assert veg_res.canopy_coverage_pct == 4.5
    assert veg_res.canopy_deficit_pct == 25.5
    assert veg_res.ndvi_index == 0.07
    assert veg_res.impervious_surface_pct == 92.0
    assert veg_res.deficit_classification == "CRITICAL_DEFICIT"
    assert veg_res.data_label == "CUSTOM_TEST_DATASET_V2"

    # 3. check_exposure
    exp_res = check_exposure(
        report="Exposure test",
        location="Zone B",
        context=custom_context,
    )
    assert exp_res.daily_transit_commuters == 22000
    assert exp_res.unshaded_waiting_areas == 7
    assert exp_res.transit_stops_count == 12
    assert exp_res.overall_exposure_level == "CRITICAL_EXPOSURE"
    assert exp_res.data_label == "CUSTOM_TEST_DATASET_V2"

    # 4. compare_interventions
    comp_res = compare_interventions(
        report="Intervention test",
        location="Zone B",
        context=custom_context,
    )
    assert comp_res.location_name == "Zone B"
    assert comp_res.data_label == "CUSTOM_TEST_DATASET_V2"
    assert "Engineered Shade Structures" in comp_res.recommended_fast_track_intervention


def test_request_more_data_reconciles_context_measurements():
    """request_more_data must recognize supplied context measurements and only request remaining gaps."""
    # Complete context: should NOT request ambient_temperature_reading or canopy_coverage_metric
    complete_context = {
        "ambient_temperature_c": 38.5,
        "canopy_coverage_pct": 8.0,
        "daily_transit_commuters": 12000,
    }
    result_complete = request_more_data(
        report="General report without text specifics.",
        location="Transit Plaza",
        context=complete_context,
    )
    param_names = [p.parameter_name for p in result_complete.missing_parameters]
    assert "ambient_temperature_reading" not in param_names
    assert "canopy_coverage_metric" not in param_names
    assert "pedestrian_exposure_density" not in param_names
    # Advanced microclimate gap is recommended instead
    assert "diurnal_temperature_profile" in param_names

    # Incomplete context: missing ambient temperature
    partial_context = {
        "canopy_coverage_pct": 8.0,
        "daily_transit_commuters": 12000,
    }
    result_partial = request_more_data(
        report="No temperature mentions.",
        location="Transit Plaza",
        context=partial_context,
    )
    partial_params = [p.parameter_name for p in result_partial.missing_parameters]
    assert "ambient_temperature_reading" in partial_params
    assert "canopy_coverage_metric" not in partial_params
    assert "pedestrian_exposure_density" not in partial_params
