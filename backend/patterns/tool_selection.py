"""
Confidence-Aware Tool Selection for Environmental Agents.

A reusable decision pattern using the Strands Decider 2B model for deterministic,
calibrated tool routing in autonomous environmental intelligence agents.
"""

from __future__ import annotations

import logging
import time
from enum import Enum
from typing import Any, Callable, Dict, List, Optional
from pydantic import BaseModel, Field

# Strands Decider official types
from strands_decider.schema import ChoiceQuestion, SystemOneRequest, SystemOneResponse
from strands_decider.infer import SystemOneEngine, load_engine

logger = logging.getLogger("heatshield.patterns.tool_selection")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [ToolSelectionPattern] %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


class AnalyticalAction(str, Enum):
    """The predefined set of 5 allowed analytical actions for the environmental agent."""
    ANALYZE_HEAT = "ANALYZE_HEAT"
    CHECK_VEGETATION = "CHECK_VEGETATION"
    CHECK_EXPOSURE = "CHECK_EXPOSURE"
    COMPARE_INTERVENTIONS = "COMPARE_INTERVENTIONS"
    REQUEST_MORE_DATA = "REQUEST_MORE_DATA"


class DecisionStatus(str, Enum):
    """Normalized application-level decision statuses."""
    ACCEPTED = "accepted"
    REQUIRES_CLARIFICATION = "requires_clarification"
    REJECTED_INVALID = "rejected_invalid"
    UNCONFIGURED = "unconfigured"


class ExecutionGate(str, Enum):
    """Safety gate determining whether automated tool execution is authorized."""
    PROCEED_TO_TOOL = "PROCEED_TO_TOOL"
    REQUEST_HUMAN_CLARIFICATION = "REQUEST_HUMAN_CLARIFICATION"
    REJECT_INVALID_CHOICE = "REJECT_INVALID_CHOICE"
    HALT_UNCONFIGURED = "HALT_UNCONFIGURED"


class NormalizedDecision(BaseModel):
    """Application-level normalized structure for Decider output."""
    decision: str = Field(..., description="Selected action name")
    confidence: float = Field(..., description="Calibrated model confidence [0.0 - 1.0]")
    decision_pattern: str = Field(
        default="confidence-aware-tool-selection",
        description="Name of the reusable decision pattern"
    )
    latency_ms: float = Field(..., description="Forward-pass decision latency in milliseconds")
    status: DecisionStatus = Field(..., description="Application status of the decision")
    probabilities: Dict[str, float] = Field(
        default_factory=dict,
        description="Full probability distribution over allowed actions"
    )
    selected_option_valid: bool = Field(
        ...,
        description="Whether selected action belongs to the predefined allowed set"
    )
    confidence_threshold: float = Field(
        ...,
        description="Configured confidence threshold gating execution"
    )
    is_above_threshold: bool = Field(
        ...,
        description="True if model confidence >= confidence_threshold"
    )
    execution_gate: ExecutionGate = Field(
        ...,
        description="Action authorization policy decision"
    )
    clarification_prompt: Optional[str] = Field(
        default=None,
        description="Prompt generated when confidence is low or data is ambiguous"
    )
    state_summary: Dict[str, Any] = Field(
        default_factory=dict,
        description="Summary of state variables provided to the model"
    )
    raw_response: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Raw output from the decision engine when available"
    )


class EnvironmentalStateBuilder:
    """Constructs structured state for Strands Decider from unstructured reports and observations."""

    @staticmethod
    def build_state(
        report: str,
        location: Optional[str] = None,
        temperature_observations: Optional[str] = None,
        vegetation_indicators: Optional[str] = None,
        exposure_indicators: Optional[str] = None,
        missing_information: Optional[List[str]] = None,
        extra_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Constructs an environmental state representation."""
        state: Dict[str, Any] = {
            "report": report.strip(),
            "location": location.strip() if location else "Unspecified location",
            "temperature_observations": temperature_observations or "No sensor telemetry available in report.",
            "vegetation_indicators": vegetation_indicators or "No vegetation metrics provided.",
            "exposure_indicators": exposure_indicators or "No population exposure details provided.",
            "missing_information": missing_information or [],
            "available_tools": [action.value for action in AnalyticalAction],
        }

        if extra_context:
            state["extra_context"] = extra_context

        # Identify inferred missing information if none provided
        if not missing_information:
            inferred_missing: List[str] = []
            low_rep = report.lower()
            if not any(k in low_rep for k in ["°c", "°f", "degrees", "celsius", "fahrenheit"]):
                inferred_missing.append("Specific ambient temperature measurement")
            if not any(k in low_rep for k in ["canopy", "ndvi", "vegetation percentage", "tree cover"]):
                inferred_missing.append("Quantitative canopy coverage metric")
            if not any(k in low_rep for k in ["pedestrians", "transit", "population", "commuters", "seniors"]):
                inferred_missing.append("Pedestrian density or demographic vulnerability indicators")
            state["missing_information"] = inferred_missing

        return state


class ConfidenceAwareToolSelector:
    """
    Reusable pattern: Confidence-Aware Tool Selection for Environmental Agents.
    
    Uses Strands Decider 2B to pick one of 5 analytical actions:
      - ANALYZE_HEAT
      - CHECK_VEGETATION
      - CHECK_EXPOSURE
      - COMPARE_INTERVENTIONS
      - REQUEST_MORE_DATA
      
    Gates tool execution through a configurable confidence threshold.
    """

    TYPED_QUESTION_INSTRUCTIONS = (
        "Given the current environmental report and available evidence, "
        "which single analytical action should the agent execute next?"
    )

    ACTION_CRITERIA: Dict[str, str] = {
        AnalyticalAction.ANALYZE_HEAT.value: (
            "Analyze available temperature observations and explicitly identified heat-risk indicators."
        ),
        AnalyticalAction.CHECK_VEGETATION.value: (
            "Analyze available vegetation coverage and canopy deficit information."
        ),
        AnalyticalAction.CHECK_EXPOSURE.value: (
            "Evaluate indicators of human exposure such as nearby schools, crowded transit stops, and shaded public spaces."
        ),
        AnalyticalAction.COMPARE_INTERVENTIONS.value: (
            "Compare tree planting, shade structures, cool roofs, and shaded pedestrian routes using transparent assumptions."
        ),
        AnalyticalAction.REQUEST_MORE_DATA.value: (
            "Identify missing information and generate a structured clarification request when data is too sparse to evaluate."
        ),
    }

    def __init__(
        self,
        checkpoint: str = "StrandsAgents/strands-decider-2B-hobson-v21",
        device: str = "cpu",
        confidence_threshold: float = 0.60,
        engine: Optional[SystemOneEngine] = None,
        remote_url: Optional[str] = None,
    ):
        self.checkpoint = checkpoint
        self.device = device
        self.confidence_threshold = confidence_threshold
        self._engine: Optional[SystemOneEngine] = engine
        self.remote_url = remote_url
        self._engine_initialized = engine is not None

    def initialize_engine(self) -> bool:
        """Loads the local StrandsDeciderModel engine if not already provided."""
        if self._engine is not None:
            return True
        if self.remote_url:
            # When remote URL is set, we use HTTP requests rather than in-process weights
            return True
            
        try:
            logger.info("Initializing Strands Decider engine with checkpoint: %s on %s", self.checkpoint, self.device)
            self._engine = load_engine(
                checkpoint=self.checkpoint,
                device=self.device,
                use_prefix_cache=True,
            )
            self._engine_initialized = True
            logger.info("Strands Decider engine successfully loaded.")
            return True
        except Exception as exc:
            logger.error("Failed to load Strands Decider engine: %s", exc)
            self._engine = None
            self._engine_initialized = False
            return False

    def create_choice_question(self) -> ChoiceQuestion:
        """Constructs the typed ChoiceQuestion according to the official schema."""
        return ChoiceQuestion(
            type="choice",
            instructions=self.TYPED_QUESTION_INSTRUCTIONS,
            criteria=self.ACTION_CRITERIA,
        )

    def select_action(
        self,
        state: Dict[str, Any],
        confidence_threshold_override: Optional[float] = None,
    ) -> NormalizedDecision:
        """
        Executes actual Strands Decider model inference, normalizes output,
        validates the action against allowed options, and enforces confidence gating.
        """
        threshold = (
            confidence_threshold_override
            if confidence_threshold_override is not None
            else self.confidence_threshold
        )
        question = self.create_choice_question()

        # Check if engine or remote service is available
        if self._engine is None and not self.remote_url:
            initialized = self.initialize_engine()
            if not initialized:
                logger.warning("Decider engine unconfigured or unavailable. Emitting unconfigured decision state.")
                return NormalizedDecision(
                    decision="NONE",
                    confidence=0.0,
                    latency_ms=0.0,
                    status=DecisionStatus.UNCONFIGURED,
                    probabilities={},
                    selected_option_valid=False,
                    confidence_threshold=threshold,
                    is_above_threshold=False,
                    execution_gate=ExecutionGate.HALT_UNCONFIGURED,
                    clarification_prompt=(
                        "Strands Decider 2B model weights or remote service are unconfigured. "
                        "Please configure DECIDER_MODEL_CHECKPOINT or DECIDER_REMOTE_URL."
                    ),
                    state_summary=state,
                )

        start_time = time.perf_counter()
        raw_output: Dict[str, Any] = {}
        chosen_action: str = ""
        probabilities: Dict[str, float] = {}
        model_confidence: float = 0.0

        try:
            if self.remote_url:
                # Query remote HTTP server (strands-decider serve)
                import httpx
                payload = {
                    "state": state,
                    "questions": {"action_choice": question.model_dump()},
                }
                resp = httpx.post(f"{self.remote_url.rstrip('/')}/v1/systemone", json=payload, timeout=30.0)
                resp.raise_for_status()
                data = resp.json()
                raw_output = data
                answer = data.get("answers", {}).get("action_choice", {})
                chosen_action = answer.get("choice", "")
                probabilities = answer.get("probabilities", {})
                model_confidence = float(answer.get("confidence", 0.0))
            else:
                # Local in-process inference
                system_one_resp: SystemOneResponse = self._engine.ask(
                    state=state,
                    questions={"action_choice": question},
                )
                raw_output = system_one_resp.model_dump()
                answer = system_one_resp.answers.get("action_choice")
                if answer is None:
                    raise RuntimeError("Decider model returned response without 'action_choice' answer.")
                chosen_action = answer.choice
                probabilities = {k: round(v, 4) for k, v in answer.probabilities.items()}
                model_confidence = round(float(answer.confidence), 4)

            latency_ms = round((time.perf_counter() - start_time) * 1000, 2)

        except Exception as exc:
            latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
            logger.error("Error during Decider model inference: %s", exc)
            return NormalizedDecision(
                decision="ERROR",
                confidence=0.0,
                latency_ms=latency_ms,
                status=DecisionStatus.REJECTED_INVALID,
                probabilities={},
                selected_option_valid=False,
                confidence_threshold=threshold,
                is_above_threshold=False,
                execution_gate=ExecutionGate.REJECT_INVALID_CHOICE,
                clarification_prompt=f"Inference execution failed: {type(exc).__name__}: {str(exc)}",
                state_summary=state,
                raw_response={"error": str(exc)},
            )

        # 1. Validate that the selected action belongs to the allowed option set
        allowed_keys = set(self.ACTION_CRITERIA.keys())
        is_valid_option = chosen_action in allowed_keys

        if not is_valid_option:
            logger.warning("Decider selected invalid option '%s' not in allowed set.", chosen_action)
            return NormalizedDecision(
                decision=chosen_action or "UNKNOWN",
                confidence=model_confidence,
                latency_ms=latency_ms,
                status=DecisionStatus.REJECTED_INVALID,
                probabilities=probabilities,
                selected_option_valid=False,
                confidence_threshold=threshold,
                is_above_threshold=False,
                execution_gate=ExecutionGate.REJECT_INVALID_CHOICE,
                clarification_prompt=(
                    f"Model choice '{chosen_action}' is invalid. Allowed actions are: "
                    f"{', '.join(sorted(allowed_keys))}."
                ),
                state_summary=state,
                raw_response=raw_output,
            )

        # 2. Check confidence threshold
        is_above_threshold = model_confidence >= threshold

        if not is_above_threshold:
            # Sorted competing options to explain the ambiguity
            sorted_probs = sorted(probabilities.items(), key=lambda kv: kv[1], reverse=True)
            top_two = sorted_probs[:2]
            diff_text = ""
            if len(top_two) == 2:
                diff_text = f" (Runner-up: {top_two[1][0]} at {top_two[1][1]:.2%})"
            
            clarification = (
                f"Model selected '{chosen_action}' with confidence {model_confidence:.2f}, "
                f"which is below the required threshold of {threshold:.2f}{diff_text}. "
                "Safe human review or report clarification is required before tool execution."
            )
            logger.info("Decision gated: confidence %.4f < threshold %.4f. Requesting clarification.", model_confidence, threshold)

            return NormalizedDecision(
                decision=chosen_action,
                confidence=model_confidence,
                latency_ms=latency_ms,
                status=DecisionStatus.REQUIRES_CLARIFICATION,
                probabilities=probabilities,
                selected_option_valid=True,
                confidence_threshold=threshold,
                is_above_threshold=False,
                execution_gate=ExecutionGate.REQUEST_HUMAN_CLARIFICATION,
                clarification_prompt=clarification,
                state_summary=state,
                raw_response=raw_output,
            )

        # 3. Accepted decision above threshold
        logger.info(
            "Decision accepted: '%s' with confidence %.4f (threshold: %.4f, latency: %.2f ms)",
            chosen_action, model_confidence, threshold, latency_ms
        )
        return NormalizedDecision(
            decision=chosen_action,
            confidence=model_confidence,
            latency_ms=latency_ms,
            status=DecisionStatus.ACCEPTED,
            probabilities=probabilities,
            selected_option_valid=True,
            confidence_threshold=threshold,
            is_above_threshold=True,
            execution_gate=ExecutionGate.PROCEED_TO_TOOL,
            clarification_prompt=None,
            state_summary=state,
            raw_response=raw_output,
        )
