"""
Integration tests executing real Strands Decider 2B model inference.
Requires local model weights or network access to Hugging Face Hub.
"""

import os
import pytest

from backend.patterns.tool_selection import (
    AnalyticalAction,
    ConfidenceAwareToolSelector,
    EnvironmentalStateBuilder,
    ExecutionGate,
)


@pytest.mark.integration
def test_real_strands_decider_inference_execution():
    """Executes a real forward pass through Strands Decider 2B."""
    selector = ConfidenceAwareToolSelector(
        checkpoint=os.getenv("DECIDER_MODEL_CHECKPOINT", "StrandsAgents/strands-decider-2B-hobson-v21"),
        device="cpu",
        confidence_threshold=0.60,
    )

    state = EnvironmentalStateBuilder.build_state(
        report="Extreme afternoon radiant heat radiating off black asphalt, no tree canopy, and senior transit users waiting at unshaded bus stop.",
        location="Downtown Central Transit Plaza",
    )

    decision = selector.select_action(state)

    # Invariants on real model execution:
    assert decision.selected_option_valid is True
    assert decision.decision in [action.value for action in AnalyticalAction]
    assert 0.0 <= decision.confidence <= 1.0
    assert decision.latency_ms > 0.0
    assert len(decision.probabilities) == 5
    # Sum of probabilities across the 5 options should be ~1.0
    prob_sum = sum(decision.probabilities.values())
    assert 0.98 <= prob_sum <= 1.02

    # Verification of gating logic based on confidence threshold
    if decision.confidence >= 0.60:
        assert decision.is_above_threshold is True
        assert decision.execution_gate == ExecutionGate.PROCEED_TO_TOOL
    else:
        assert decision.is_above_threshold is False
        assert decision.execution_gate == ExecutionGate.REQUEST_HUMAN_CLARIFICATION
        assert decision.clarification_prompt is not None
