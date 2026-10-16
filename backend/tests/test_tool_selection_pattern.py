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
