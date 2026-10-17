"""
Unit tests for the Confidence-Aware Tool Selection decision pattern.
Uses controlled mocks to isolate pattern invariants from heavy model downloading.
"""

from unittest.mock import MagicMock
import pytest
from pydantic import BaseModel

from backend.patterns.tool_selection import (
    AnalyticalAction,
    ConfidenceAwareToolSelector,
    DecisionStatus,
    EnvironmentalStateBuilder,
    ExecutionGate,
    NormalizedDecision,
)
from strands_decider.schema import ChoiceAnswer, SystemOneResponse, Usage


class MockEngine:
    """Mock engine simulating Strands Decider SystemOneEngine responses."""
    def __init__(self, choice: str, confidence: float, probabilities: dict[str, float]):
        self.choice = choice
        self.confidence = confidence
        self.probabilities = probabilities

    def ask(self, state, questions):
        answer = ChoiceAnswer(
            type="choice",
            choice=self.choice,
            probabilities=self.probabilities,
            confidence=self.confidence,
        )
        return SystemOneResponse(
            model="strands-decider-mock",
            answers={"action_choice": answer},
            usage=Usage(input_tokens=150, output_tokens=1),
        )


def test_state_builder_with_missing_information_inference():
    """State builder should identify missing numeric indicators from sparse reports."""
    sparse_report = "The street is very hot and there is a crowded bus stop."
    state = EnvironmentalStateBuilder.build_state(
        report=sparse_report,
        location="Market St",
    )
    
    assert state["report"] == sparse_report
    assert state["location"] == "Market St"
    assert "Specific ambient temperature measurement" in state["missing_information"]
    assert "Quantitative canopy coverage metric" in state["missing_information"]
    assert len(state["available_tools"]) == 5


def test_valid_decision_above_threshold():
    """A valid choice above confidence threshold should be ACCEPTED and authorized to PROCEED."""
    mock_engine = MockEngine(
        choice="CHECK_EXPOSURE",
        confidence=0.82,
        probabilities={
            "ANALYZE_HEAT": 0.05,
            "CHECK_VEGETATION": 0.05,
            "CHECK_EXPOSURE": 0.85,
            "COMPARE_INTERVENTIONS": 0.02,
            "REQUEST_MORE_DATA": 0.03,
        }
    )
    
    selector = ConfidenceAwareToolSelector(
        confidence_threshold=0.60,
        engine=mock_engine,
    )
    state = {"report": "Crowded bus stop with elderly waiting in sun."}
    decision = selector.select_action(state)

    assert decision.decision == "CHECK_EXPOSURE"
    assert decision.confidence == 0.82
    assert decision.status == DecisionStatus.ACCEPTED
    assert decision.selected_option_valid is True
    assert decision.is_above_threshold is True
    assert decision.execution_gate == ExecutionGate.PROCEED_TO_TOOL
    assert decision.clarification_prompt is None
    assert decision.latency_ms >= 0.0


def test_low_confidence_decision_requires_clarification():
    """When confidence is below threshold, tool execution must be BLOCKED and clarification requested."""
    mock_engine = MockEngine(
        choice="CHECK_VEGETATION",
        confidence=0.42,  # Below threshold 0.60
        probabilities={
            "ANALYZE_HEAT": 0.25,
            "CHECK_VEGETATION": 0.45,
            "CHECK_EXPOSURE": 0.20,
            "COMPARE_INTERVENTIONS": 0.05,
            "REQUEST_MORE_DATA": 0.05,
        }
    )
    
    selector = ConfidenceAwareToolSelector(
        confidence_threshold=0.60,
        engine=mock_engine,
    )
    state = {"report": "Sparse trees and moderate afternoon sun."}
    decision = selector.select_action(state)

    assert decision.decision == "CHECK_VEGETATION"
    assert decision.confidence == 0.42
    assert decision.status == DecisionStatus.REQUIRES_CLARIFICATION
    assert decision.selected_option_valid is True
    assert decision.is_above_threshold is False
    assert decision.execution_gate == ExecutionGate.REQUEST_HUMAN_CLARIFICATION
    assert decision.clarification_prompt is not None
    assert "below the required threshold" in decision.clarification_prompt


def test_invalid_action_rejection():
    """If the model returns an invalid or invented action name, it must be rejected."""
    mock_engine = MockEngine(
        choice="NON_EXISTENT_TOOL",
        confidence=0.95,
        probabilities={"NON_EXISTENT_TOOL": 1.0}
    )
    
    selector = ConfidenceAwareToolSelector(
        confidence_threshold=0.60,
        engine=mock_engine,
    )
    state = {"report": "General report"}
    decision = selector.select_action(state)

    assert decision.decision == "NON_EXISTENT_TOOL"
    assert decision.status == DecisionStatus.REJECTED_INVALID
    assert decision.selected_option_valid is False
    assert decision.execution_gate == ExecutionGate.REJECT_INVALID_CHOICE
    assert "invalid" in decision.clarification_prompt.lower()


def test_unconfigured_engine_safe_handling():
    """When engine is None and cannot load, should emit UNCONFIGURED status without crashing."""
    selector = ConfidenceAwareToolSelector(
        checkpoint="non-existent-checkpoint-path",
        device="cpu",
        confidence_threshold=0.60,
    )
    # Mock initialize_engine to return False
    selector.initialize_engine = MagicMock(return_value=False)

    decision = selector.select_action({"report": "Sample"})
    assert decision.status == DecisionStatus.UNCONFIGURED
    assert decision.execution_gate == ExecutionGate.HALT_UNCONFIGURED
    assert decision.confidence == 0.0


def test_confidence_threshold_override():
    """Per-call confidence threshold override must take precedence."""
    mock_engine = MockEngine(
        choice="ANALYZE_HEAT",
        confidence=0.65,
        probabilities={"ANALYZE_HEAT": 0.70}
    )
    selector = ConfidenceAwareToolSelector(
        confidence_threshold=0.60,
        engine=mock_engine,
    )
    
    # At default 0.60, 0.65 is above threshold -> ACCEPTED
    d1 = selector.select_action({"report": "heat"})
    assert d1.status == DecisionStatus.ACCEPTED
    
    # Overriding to 0.75 makes 0.65 below threshold -> REQUIRES_CLARIFICATION
    d2 = selector.select_action({"report": "heat"}, confidence_threshold_override=0.75)
    assert d2.status == DecisionStatus.REQUIRES_CLARIFICATION
    assert d2.execution_gate == ExecutionGate.REQUEST_HUMAN_CLARIFICATION


def test_state_builder_complete_synthetic_measurements():
    """State builder must recognize structured extra_context measurements and populate state correctly."""
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
    report = (
        "SYNTHETIC DEMONSTRATION: Transit corridor with hot pavement, low canopy, and high transit rider density. "
        "Assess environmental conditions and mitigation options."
    )
    state = EnvironmentalStateBuilder.build_state(
        report=report,
        location="Downtown Central Transit Plaza",
        extra_context=extra,
    )

    # Core measurements must be in normalized dictionary
    assert state["normalized_measurements"]["ambient_temperature_c"] == 38.2
    assert state["normalized_measurements"]["surface_temperature_c"] == 51.0
    assert state["normalized_measurements"]["canopy_coverage_pct"] == 6.5
    assert state["normalized_measurements"]["ndvi_index"] == 0.12
    assert state["normalized_measurements"]["impervious_surface_pct"] == 88.0
    assert state["normalized_measurements"]["daily_transit_commuters"] == 14500

    # Typed state strings must reflect actual normalized values
    assert "38.2°C" in state["temperature_observations"]
    assert "51.0°C" in state["temperature_observations"]
    assert "No sensor telemetry available in report" not in state["temperature_observations"]

    assert "6.5%" in state["vegetation_indicators"]
    assert "0.12" in state["vegetation_indicators"]
    assert "88.0%" in state["vegetation_indicators"]
    assert "No vegetation metrics provided" not in state["vegetation_indicators"]

    assert "14,500" in state["exposure_indicators"]
    assert "5" in state["exposure_indicators"]
    assert "No population exposure details provided" not in state["exposure_indicators"]

    # No core telemetry gaps should be flagged as missing
    assert state["missing_information"] == []


def test_state_builder_missing_ambient_temperature():
    """When ambient temperature is not supplied in extra_context or report, it must be flagged."""
    extra = {
        "canopy_coverage_pct": 12.0,
        "daily_transit_commuters": 4000,
    }
    report = "The commercial avenue has several bus stops and limited tree canopy."
    state = EnvironmentalStateBuilder.build_state(
        report=report,
        location="Commercial Ave",
        extra_context=extra,
    )

    assert "Specific ambient temperature measurement" in state["missing_information"]
    assert "Quantitative canopy coverage metric" not in state["missing_information"]
    assert "Pedestrian density or demographic vulnerability indicators" not in state["missing_information"]
    assert "No sensor telemetry available in report" in state["temperature_observations"]
    assert "12.0%" in state["vegetation_indicators"]
    assert "4,000" in state["exposure_indicators"]


def test_state_builder_missing_vegetation_measurements():
    """When vegetation indicators are omitted, canopy metrics must be flagged as missing."""
    extra = {
        "ambient_temperature_c": 36.5,
        "daily_transit_commuters": 6500,
    }
    report = "High temperatures observed near transit stop."
    state = EnvironmentalStateBuilder.build_state(
        report=report,
        location="Suburban Hub",
        extra_context=extra,
    )

    assert "Quantitative canopy coverage metric" in state["missing_information"]
    assert "Specific ambient temperature measurement" not in state["missing_information"]
    assert "Pedestrian density or demographic vulnerability indicators" not in state["missing_information"]
    assert "36.5°C" in state["temperature_observations"]
    assert "No vegetation metrics provided" in state["vegetation_indicators"]
    assert "6,500" in state["exposure_indicators"]


def test_state_builder_missing_exposure_indicators():
    """When commuter and transit density are omitted, exposure indicators must be flagged as missing."""
    extra = {
        "ambient_temperature_c": 39.0,
        "canopy_coverage_pct": 5.0,
    }
    report = "High surface temperatures observed in open industrial parking."
    state = EnvironmentalStateBuilder.build_state(
        report=report,
        location="Industrial Park",
        extra_context=extra,
    )

    assert "Pedestrian density or demographic vulnerability indicators" in state["missing_information"]
    assert "Specific ambient temperature measurement" not in state["missing_information"]
    assert "Quantitative canopy coverage metric" not in state["missing_information"]
    assert "39.0°C" in state["temperature_observations"]
    assert "5.0%" in state["vegetation_indicators"]
    assert "No population exposure details provided" in state["exposure_indicators"]


def test_state_builder_invalid_numeric_values():
    """Invalid numeric values must be flagged in validation_issues and missing_information without crashing."""
    extra = {
        "ambient_temperature_c": "not_a_valid_number",
        "surface_temperature_c": 999.0,  # Unphysical (> 100°C)
        "canopy_coverage_pct": 175.0,    # Out of range (> 100%)
        "daily_transit_commuters": -250, # Negative count
    }
    report = "Sensor node transmission."
    state = EnvironmentalStateBuilder.build_state(
        report=report,
        location="Test Station",
        extra_context=extra,
    )

    # Invalid values must not be accepted into normalized measurements
    assert "ambient_temperature_c" not in state["normalized_measurements"]
    assert "surface_temperature_c" not in state["normalized_measurements"]
    assert "canopy_coverage_pct" not in state["normalized_measurements"]
    assert "daily_transit_commuters" not in state["normalized_measurements"]

    # Issues must be catalogued
    assert len(state["validation_issues"]) == 4

    # Corresponding missing indicators must be flagged with invalid notes
    missing = state["missing_information"]
    assert any("Specific ambient temperature measurement" in m for m in missing)
    assert any("Quantitative canopy coverage metric" in m for m in missing)
    assert any("Pedestrian density" in m for m in missing)


def test_state_builder_explicit_synthetic_provenance():
    """Explicit synthetic metadata in extra_context must be preserved for compliance and auditability."""
    extra = {
        "data_source": "SYNTHETIC_DEMO",
        "dataset_label": "SYNTHETIC_DEV_DATASET_V1",
        "purpose": "Post-integration test",
        "ambient_temperature_c": 35.0,
    }
    state = EnvironmentalStateBuilder.build_state(
        report="Synthetic test scenario.",
        location="Downtown Plaza",
        extra_context=extra,
    )

    assert state["normalized_measurements"]["data_source"] == "SYNTHETIC_DEMO"
    assert state["normalized_measurements"]["dataset_label"] == "SYNTHETIC_DEV_DATASET_V1"
    assert state["normalized_measurements"]["purpose"] == "Post-integration test"
