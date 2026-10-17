"""
Confidence-Aware Tool Selection for Environmental Agents.

A reusable decision pattern using the Strands Decider 2B model for deterministic,
calibrated tool routing in autonomous environmental intelligence agents.
"""

from __future__ import annotations

import logging
import re
import threading
import time
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple
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
    def normalize_measurements(
        raw_context: Optional[Dict[str, Any]],
    ) -> Tuple[Dict[str, Any], List[str]]:
        """
        Validates, normalizes, and extracts structured environmental measurements from context.
        Returns a tuple of (normalized_dict, validation_errors).
        """
        if not raw_context or not isinstance(raw_context, dict):
            return {}, []

        normalized: Dict[str, Any] = {}
        validation_issues: List[str] = []

        # 1. Ambient Temperature (-50°C to 70°C)
        ambient_raw = raw_context.get("ambient_temperature_c")
        if ambient_raw is None:
            ambient_raw = raw_context.get("ambient_temp_c")
        if ambient_raw is not None:
            try:
                ambient_val = float(ambient_raw)
                if -50.0 <= ambient_val <= 70.0:
                    normalized["ambient_temperature_c"] = round(ambient_val, 2)
                else:
                    validation_issues.append(
                        f"ambient_temperature_c value {ambient_val}°C is unphysical (expected between -50°C and 70°C)"
                    )
            except (ValueError, TypeError):
                validation_issues.append(
                    f"ambient_temperature_c value '{ambient_raw}' is not a valid numeric float"
                )

        # 2. Surface Temperature (-50°C to 100°C)
        surface_raw = raw_context.get("surface_temperature_c")
        if surface_raw is None:
            surface_raw = raw_context.get("surface_temp_c")
        if surface_raw is not None:
            try:
                surface_val = float(surface_raw)
                if -50.0 <= surface_val <= 100.0:
                    normalized["surface_temperature_c"] = round(surface_val, 2)
                else:
                    validation_issues.append(
                        f"surface_temperature_c value {surface_val}°C is unphysical (expected between -50°C and 100°C)"
                    )
            except (ValueError, TypeError):
                validation_issues.append(
                    f"surface_temperature_c value '{surface_raw}' is not a valid numeric float"
                )

        # 3. Heat Index (-50°C to 100°C)
        hi_raw = raw_context.get("heat_index_c")
        if hi_raw is None:
            hi_raw = raw_context.get("heat_index")
        if hi_raw is not None:
            try:
                hi_val = float(hi_raw)
                if -50.0 <= hi_val <= 100.0:
                    normalized["heat_index_c"] = round(hi_val, 2)
                else:
                    validation_issues.append(
                        f"heat_index_c value {hi_val}°C is unphysical (expected between -50°C and 100°C)"
                    )
            except (ValueError, TypeError):
                validation_issues.append(
                    f"heat_index_c value '{hi_raw}' is not a valid numeric float"
                )

        # 4. Canopy Coverage Percentage (0.0% to 100.0%)
        canopy_raw = raw_context.get("canopy_coverage_pct")
        if canopy_raw is None:
            canopy_raw = raw_context.get("canopy_pct")
        if canopy_raw is not None:
            try:
                canopy_val = float(canopy_raw)
                if 0.0 <= canopy_val <= 100.0:
                    normalized["canopy_coverage_pct"] = round(canopy_val, 2)
                else:
                    validation_issues.append(
                        f"canopy_coverage_pct value {canopy_val}% is out of valid range [0.0, 100.0]"
                    )
            except (ValueError, TypeError):
                validation_issues.append(
                    f"canopy_coverage_pct value '{canopy_raw}' is not a valid numeric float"
                )

        # 5. NDVI Index (-1.0 to 1.0)
        ndvi_raw = raw_context.get("ndvi_index")
        if ndvi_raw is None:
            ndvi_raw = raw_context.get("ndvi")
        if ndvi_raw is not None:
            try:
                ndvi_val = float(ndvi_raw)
                if -1.0 <= ndvi_val <= 1.0:
                    normalized["ndvi_index"] = round(ndvi_val, 4)
                else:
                    validation_issues.append(
                        f"ndvi_index value {ndvi_val} is out of valid range [-1.0, 1.0]"
                    )
            except (ValueError, TypeError):
                validation_issues.append(
                    f"ndvi_index value '{ndvi_raw}' is not a valid numeric float"
                )

        # 6. Impervious Surface Percentage (0.0% to 100.0%)
        impervious_raw = raw_context.get("impervious_surface_pct")
        if impervious_raw is None:
            impervious_raw = raw_context.get("impervious_pct")
        if impervious_raw is not None:
            try:
                imp_val = float(impervious_raw)
                if 0.0 <= imp_val <= 100.0:
                    normalized["impervious_surface_pct"] = round(imp_val, 2)
                else:
                    validation_issues.append(
                        f"impervious_surface_pct value {imp_val}% is out of valid range [0.0, 100.0]"
                    )
            except (ValueError, TypeError):
                validation_issues.append(
                    f"impervious_surface_pct value '{impervious_raw}' is not a valid numeric float"
                )

        # 7. Daily Transit Commuters (non-negative integer)
        commuters_raw = raw_context.get("daily_transit_commuters")
        if commuters_raw is None:
            commuters_raw = raw_context.get("commuters")
        if commuters_raw is not None:
            try:
                commuters_val = int(commuters_raw)
                if commuters_val >= 0:
                    normalized["daily_transit_commuters"] = commuters_val
                else:
                    validation_issues.append(
                        f"daily_transit_commuters value {commuters_val} must be non-negative"
                    )
            except (ValueError, TypeError):
                validation_issues.append(
                    f"daily_transit_commuters value '{commuters_raw}' is not a valid integer"
                )

        # 8. Transit Stops Count (non-negative integer)
        stops_raw = raw_context.get("transit_stops_count")
        if stops_raw is None:
            stops_raw = raw_context.get("transit_stops")
        if stops_raw is not None:
            try:
                stops_val = int(stops_raw)
                if stops_val >= 0:
                    normalized["transit_stops_count"] = stops_val
                else:
                    validation_issues.append(
                        f"transit_stops_count value {stops_val} must be non-negative"
                    )
            except (ValueError, TypeError):
                validation_issues.append(
                    f"transit_stops_count value '{stops_raw}' is not a valid integer"
                )

        # 9. Unshaded Waiting Areas (non-negative integer)
        unshaded_raw = raw_context.get("unshaded_waiting_areas")
        if unshaded_raw is None:
            unshaded_raw = raw_context.get("unshaded_stops")
        if unshaded_raw is not None:
            try:
                unshaded_val = int(unshaded_raw)
                if unshaded_val >= 0:
                    normalized["unshaded_waiting_areas"] = unshaded_val
                else:
                    validation_issues.append(
                        f"unshaded_waiting_areas value {unshaded_val} must be non-negative"
                    )
            except (ValueError, TypeError):
                validation_issues.append(
                    f"unshaded_waiting_areas value '{unshaded_raw}' is not a valid integer"
                )

        # 10. Vulnerable Facilities (list of dicts)
        facs_raw = raw_context.get("vulnerable_facilities")
        if facs_raw is not None:
            if isinstance(facs_raw, list):
                normalized["vulnerable_facilities"] = facs_raw
            else:
                validation_issues.append("vulnerable_facilities must be a list of facility objects")

        # 11. Metadata / Provenance
        if "data_source" in raw_context and raw_context["data_source"] is not None:
            normalized["data_source"] = str(raw_context["data_source"]).strip()
        if "dataset_label" in raw_context and raw_context["dataset_label"] is not None:
            normalized["dataset_label"] = str(raw_context["dataset_label"]).strip()
        if "purpose" in raw_context and raw_context["purpose"] is not None:
            normalized["purpose"] = str(raw_context["purpose"]).strip()

        return normalized, validation_issues

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
        """Constructs a normalized, truthful environmental state representation for Strands Decider."""
        normalized, validation_issues = EnvironmentalStateBuilder.normalize_measurements(extra_context)
        low_rep = report.lower()

        # Build temperature_observations if not provided
        if temperature_observations is None:
            temp_parts: List[str] = []
            if "ambient_temperature_c" in normalized:
                temp_parts.append(f"Ambient temperature: {normalized['ambient_temperature_c']}°C")
            if "surface_temperature_c" in normalized:
                temp_parts.append(f"Surface temperature: {normalized['surface_temperature_c']}°C")
            if "heat_index_c" in normalized:
                temp_parts.append(f"Heat index: {normalized['heat_index_c']}°C")
            elif "ambient_temperature_c" in normalized and "surface_temperature_c" in normalized:
                derived_hi = round(
                    normalized["ambient_temperature_c"]
                    + max(2.0, (normalized["surface_temperature_c"] - normalized["ambient_temperature_c"]) * 0.25),
                    1,
                )
                temp_parts.append(f"Heat index: {derived_hi}°C (estimated)")

            if temp_parts:
                temperature_observations = "; ".join(temp_parts) + "."
            elif any(k in low_rep for k in ["heat", "hot", "warm", "temperature", "°c", "celsius", "fahrenheit"]):
                temperature_observations = (
                    "Report narrative references elevated thermal conditions; specific calibrated sensor telemetry not provided."
                )
            else:
                temperature_observations = "No sensor telemetry available in report."

        # Build vegetation_indicators if not provided
        if vegetation_indicators is None:
            veg_parts: List[str] = []
            if "canopy_coverage_pct" in normalized:
                veg_parts.append(f"Canopy coverage: {normalized['canopy_coverage_pct']}%")
            if "ndvi_index" in normalized:
                veg_parts.append(f"NDVI: {normalized['ndvi_index']}")
            if "impervious_surface_pct" in normalized:
                veg_parts.append(f"Impervious surface: {normalized['impervious_surface_pct']}%")

            if veg_parts:
                vegetation_indicators = "; ".join(veg_parts) + "."
            elif any(k in low_rep for k in ["tree", "canopy", "shade", "vegetation", "grass", "park"]):
                vegetation_indicators = (
                    "Report narrative references limited tree canopy and vegetation; quantitative coverage metric not provided."
                )
            else:
                vegetation_indicators = "No vegetation metrics provided."

        # Build exposure_indicators if not provided
        if exposure_indicators is None:
            exp_parts: List[str] = []
            if "daily_transit_commuters" in normalized:
                exp_parts.append(f"Daily transit commuters: {normalized['daily_transit_commuters']:,}")
            if "unshaded_waiting_areas" in normalized:
                exp_parts.append(f"Unshaded waiting areas: {normalized['unshaded_waiting_areas']}")
            if "transit_stops_count" in normalized:
                exp_parts.append(f"Transit stops: {normalized['transit_stops_count']}")
            if "vulnerable_facilities" in normalized and normalized["vulnerable_facilities"]:
                exp_parts.append(f"Vulnerable facilities: {len(normalized['vulnerable_facilities'])} nearby")

            if exp_parts:
                exposure_indicators = "; ".join(exp_parts) + "."
            elif any(k in low_rep for k in ["transit", "commuter", "pedestrian", "bus", "waiting", "elderly", "crowd", "school"]):
                exposure_indicators = (
                    "Report narrative indicates pedestrian transit activity; specific commuter counts not provided."
                )
            else:
                exposure_indicators = "No population exposure details provided."

        # Identify inferred missing information if none provided
        if missing_information is None:
            inferred_missing: List[str] = []

            # 1. Temperature: Check normalized measurement or numeric report keyword
            has_ambient = "ambient_temperature_c" in normalized
            has_rep_temp = any(k in low_rep for k in ["°c", "°f", "degrees", "celsius", "fahrenheit"]) or bool(
                re.search(r"\b\d+(\.\d+)?\s*(°\s*[cf]|[cf]\b|deg)", low_rep)
            )
            if not (has_ambient or has_rep_temp):
                if any("ambient_temperature_c" in err for err in validation_issues):
                    inferred_missing.append(
                        "Specific ambient temperature measurement (supplied value was invalid or unphysical)"
                    )
                else:
                    inferred_missing.append("Specific ambient temperature measurement")

            # 2. Vegetation: Check normalized canopy/ndvi or quantitative report keyword
            has_canopy = "canopy_coverage_pct" in normalized or "ndvi_index" in normalized
            has_rep_canopy = any(k in low_rep for k in ["canopy", "ndvi", "vegetation percentage", "tree cover"]) and (
                "%" in low_rep or bool(re.search(r"\b\d+(\.\d+)?\s*(percent|%)", low_rep))
            )
            if not (has_canopy or has_rep_canopy):
                if any("canopy_coverage_pct" in err or "ndvi_index" in err for err in validation_issues):
                    inferred_missing.append("Quantitative canopy coverage metric (supplied value was invalid)")
                else:
                    inferred_missing.append("Quantitative canopy coverage metric")

            # 3. Exposure: Check normalized commuters/stops or quantitative report keyword
            has_exposure = (
                "daily_transit_commuters" in normalized
                or "unshaded_waiting_areas" in normalized
                or "transit_stops_count" in normalized
            )
            has_rep_exposure = any(k in low_rep for k in ["pedestrians", "transit", "population", "commuters", "seniors"]) and (
                bool(re.search(r"\b\d{2,}\b", low_rep))
            )
            if not (has_exposure or has_rep_exposure):
                if any("daily_transit_commuters" in err or "unshaded" in err for err in validation_issues):
                    inferred_missing.append(
                        "Pedestrian density or demographic vulnerability indicators (supplied value was invalid)"
                    )
                else:
                    inferred_missing.append("Pedestrian density or demographic vulnerability indicators")

            missing_information = inferred_missing

        state: Dict[str, Any] = {
            "report": report.strip(),
            "location": location.strip() if location else "Unspecified location",
            "temperature_observations": temperature_observations,
            "vegetation_indicators": vegetation_indicators,
            "exposure_indicators": exposure_indicators,
            "missing_information": missing_information,
            "available_tools": [action.value for action in AnalyticalAction],
        }

        if extra_context:
            state["extra_context"] = extra_context
        state["normalized_measurements"] = normalized
        if validation_issues:
            state["validation_issues"] = validation_issues

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
        self.remote_url = remote_url.strip() if remote_url else None
        self._engine_initialized = engine is not None
        self._init_lock = threading.Lock()
        self._remote_verified: Optional[bool] = None

    @property
    def is_engine_loaded(self) -> bool:
        """Returns True only if in-process model weights are loaded and active."""
        return self._engine is not None

    @property
    def is_ready(self) -> bool:
        """Returns True only if the decision engine (local loaded or verified remote) is ready for inference."""
        if self._engine is not None:
            return True
        if self.remote_url:
            return self._verify_remote_engine()
        return False

    def _verify_remote_engine(self) -> bool:
        """Verifies that the remote Decider HTTP service is reachable and responsive."""
        if not self.remote_url:
            return False
        try:
            import httpx
            url = f"{self.remote_url.rstrip('/')}/health"
            resp = httpx.get(url, timeout=2.0)
            is_ok = resp.status_code == 200
            self._remote_verified = is_ok
            return is_ok
        except Exception as exc:
            logger.debug("Remote Decider verification failed for %s: %s", self.remote_url, exc)
            self._remote_verified = False
            return False

    def initialize_engine(self) -> bool:
        """Loads the local StrandsDeciderModel engine if not already provided, or verifies remote service."""
        if self._engine is not None:
            return True
        if self.remote_url:
            verified = self._verify_remote_engine()
            self._engine_initialized = verified
            return verified

        with self._init_lock:
            if self._engine is not None:
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
