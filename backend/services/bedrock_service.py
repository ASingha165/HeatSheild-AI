"""
Amazon Bedrock Integration Service for HeatShield AI.

Generates evidence-based, transparent environmental recommendations grounded
exclusively in actual analytical tool results and verified user reports.
Supports AWS IAM role-based authentication and standard credential provider chains.
Uses the boto3 Bedrock Runtime Converse API.
"""

from __future__ import annotations

import json
import logging
import os
import re
import time
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field

import boto3
from botocore.config import Config
from botocore.exceptions import (
    BotoCoreError,
    ClientError,
    ConnectTimeoutError,
    CredentialRetrievalError,
    EndpointConnectionError,
    NoCredentialsError,
    PartialCredentialsError,
    ReadTimeoutError,
)

logger = logging.getLogger("heatshield.services.bedrock")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] [BedrockService] %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

# Regex patterns for scrubbing inadvertent credential leaks in logs/messages
_AWS_KEY_PATTERN = re.compile(r"(?<![A-Za-z0-9/+=])(?:AKIA|ASIA)[0-9A-Z]{16}(?![A-Za-z0-9/+=])")
_AWS_SECRET_PATTERN = re.compile(
    r"(?i)(?:aws_secret_access_key|secret_key|session_token|authorization)[\s:=]+['\"]?([A-Za-z0-9/+=]{16,})['\"]?"
)


def sanitize_text(text: str) -> str:
    """Removes any potential AWS access keys or secret tokens from text."""
    if not text:
        return ""
    cleaned = _AWS_KEY_PATTERN.sub("[REDACTED_AWS_KEY]", text)
    cleaned = _AWS_SECRET_PATTERN.sub(r"aws_credential=[REDACTED_CREDENTIAL]", cleaned)
    return cleaned


def classify_aws_error(err: Exception, model_id: str = "", region_name: str = "") -> Tuple[str, str]:
    """
    Classifies AWS/boto3 errors into sanitized categories without leaking any credentials.
    Returns (category, sanitized_reason).
    Categories:
      - 'missing_credentials'
      - 'expired_credentials'
      - 'access_denied'
      - 'model_or_profile_error'
      - 'throttling_or_service_error'
      - 'network_or_timeout_error'
      - 'client_error'
      - 'unexpected_error'
    """
    if isinstance(err, (NoCredentialsError, PartialCredentialsError, CredentialRetrievalError)):
        return (
            "missing_credentials",
            "No AWS credentials detected in environment, IAM role, or AWS profile.",
        )

    if isinstance(err, (EndpointConnectionError, ConnectTimeoutError, ReadTimeoutError)):
        return (
            "network_or_timeout_error",
            f"Network connection or timeout communicating with Bedrock in region {region_name or 'configured'}.",
        )

    if isinstance(err, ClientError):
        error_dict = err.response.get("Error", {})
        code = str(error_dict.get("Code", "ClientError"))
        msg = str(error_dict.get("Message", ""))
        low_msg = msg.lower()

        # 1. Expired credentials
        if code in ("ExpiredToken", "ExpiredTokenException", "RequestExpired") or "token is expired" in low_msg:
            return (
                "expired_credentials",
                "AWS credentials expired (session token expired; refresh temporary workshop credentials).",
            )

        # 2. Access denied
        if (
            code in ("AccessDeniedException", "AccessDenied", "UnauthorizedException", "AuthFailure")
            or "not authorized" in low_msg
            or "access denied" in low_msg
        ):
            return (
                "access_denied",
                f"AWS Bedrock access denied for model '{model_id}' (verify IAM permissions or model entitlement in {region_name}).",
            )

        # 3. Model or inference-profile errors
        if (
            code in ("ResourceNotFoundException", "ValidationException", "ModelNotReadyException", "UnknownOperationException")
            or "inference profile" in low_msg
            or "model identifier" in low_msg
            or "not found" in low_msg
        ):
            return (
                "model_or_profile_error",
                f"Amazon Bedrock model or inference-profile error: {code}",
            )

        # 4. Throttling and service failures
        if code in (
            "ThrottlingException",
            "ServiceUnavailableException",
            "InternalServerException",
            "ModelErrorException",
            "ModelTimeoutException",
            "TooManyRequestsException",
        ):
            return (
                "throttling_or_service_error",
                f"Amazon Bedrock service failure or rate limit: {code}",
            )

        return (
            "client_error",
            f"Amazon Bedrock client error: {code}",
        )

    return (
        "unexpected_error",
        f"Unexpected error during Bedrock invocation: {type(err).__name__}",
    )


class BedrockConfigStatus(BaseModel):
    is_configured: bool = Field(..., description="Whether AWS credentials and Bedrock access are detected")
    region: str = Field(..., description="Configured AWS region")
    model_id: str = Field(..., description="Target Amazon Bedrock foundation model ID or inference profile")
    auth_mechanism: str = Field(..., description="Authentication provider type (iam_role, env_credentials, unconfigured)")
    status_message: str = Field(..., description="Human-readable integration status")


class BedrockRecommendation(BaseModel):
    summary: str = Field(..., description="Concise executive synthesis of findings")
    recommended_next_step: str = Field(..., description="Primary prioritized action or intervention")
    supporting_evidence: List[str] = Field(..., description="Empirical evidence cited directly from tool results")
    assumptions: List[str] = Field(..., description="Transparent operational assumptions distinguishing observations")
    limitations: List[str] = Field(..., description="Data uncertainties, missing measurements, and domain constraints")
    follow_up_actions: List[str] = Field(..., description="Actionable follow-up steps for municipal staff")

    # Metadata & Provenance
    model_id: str
    is_live_bedrock: bool = Field(..., description="True if response was generated by live Amazon Bedrock API")
    data_provenance: str = Field(..., description="Dataset provenance flag")
    latency_ms: float = Field(..., description="Generation latency in milliseconds")
    status: str = Field(..., description="Status: 'success', 'dev_mode_fallback', or 'unconfigured'")
    fallback_reason: Optional[str] = Field(default=None, description="Detailed reason if dev mode fallback was used")


class BedrockService:
    """
    Production-conscious service for Amazon Bedrock generative reasoning.
    Grounds all outputs strictly in actual Decider choices and analytical tool outputs.
    Follows: Environmental Report -> Strands Decider 2B -> Confidence Gate -> Analytical Tool -> Bedrock -> Recommendation.
    """

    SYSTEM_PROMPT = (
        "You are HeatShield AI's Environmental Resilience Reasoner, an expert municipal advisor. "
        "Your task is to synthesize an actionable recommendation based STRICTLY on the actual "
        "analytical tool results and environmental state provided.\n"
        "\nCRITICAL RULES:\n"
        "1. DISTINGUISH OBSERVATIONS FROM ASSUMPTIONS: Ground all empirical claims in the supplied tool output. "
        "Place verified measurements into 'supporting_evidence'. Place operational hypotheses into 'assumptions'.\n"
        "2. IDENTIFY MISSING MEASUREMENTS: Explicitly identify missing sensors, unmeasured parameters, or uncertain fields in 'limitations'.\n"
        "3. EXPLAIN UNCERTAINTY & LIMITATIONS: Note data provenance (e.g., synthetic development data vs live telemetry) "
        "and sensor tolerances.\n"
        "4. AVOID FABRICATION: Never invent environmental measurements or present hypothetical benefits as measured outcomes. "
        "Never claim that an intervention has already been built or implemented.\n"
        "5. PRESERVE HUMAN-REVIEW REQUIREMENTS: Municipal human review and on-the-ground verification are mandatory "
        "before operational dispatch or capital allocation. Reflect this in 'limitations' and 'follow_up_actions'.\n"
        "6. DO NOT EXECUTE OR REPLACE TOOLS: Strands Decider 2B has already selected the analytical action; "
        "your role is synthesis and reasoning, not independent tool dispatch.\n"
        "7. OUTPUT FORMAT: Output valid, raw JSON only matching the requested schema with no markdown ticks or preamble."
    )

    def __init__(
        self,
        region_name: Optional[str] = None,
        model_id: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 1024,
        timeout_seconds: int = 15,
        boto3_client: Optional[Any] = None,
    ):
        # Configure AWS Region: explicit argument -> AWS_REGION -> AWS_DEFAULT_REGION -> us-east-1
        self.region_name = (
            region_name
            or os.getenv("AWS_REGION")
            or os.getenv("AWS_DEFAULT_REGION")
            or "us-east-1"
        )
        # Configure Model ID / Inference Profile:
        # explicit argument -> BEDROCK_MODEL_ID -> global.amazon.nova-2-lite-v1:0
        self.model_id = (
            model_id
            or os.getenv("BEDROCK_MODEL_ID")
            or "global.amazon.nova-2-lite-v1:0"
        )
        self.temperature = float(os.getenv("BEDROCK_TEMPERATURE", str(temperature)))
        self.max_tokens = int(os.getenv("BEDROCK_MAX_TOKENS", str(max_tokens)))
        self.timeout_seconds = int(os.getenv("BEDROCK_TIMEOUT_SECONDS", str(timeout_seconds)))
        self._client = boto3_client

        # Truthful state tracking
        self.last_error_category: Optional[str] = None
        self.last_error_reason: Optional[str] = None
        self.last_inference_successful: Optional[bool] = None

    def _get_client(self) -> Optional[Any]:
        """Initializes or returns cached boto3 bedrock-runtime client using credential provider chain."""
        if self._client is not None:
            return self._client
        try:
            session = boto3.Session(region_name=self.region_name)
            creds = session.get_credentials()
            if creds is None:
                return None

            boto_config = Config(
                connect_timeout=5,
                read_timeout=self.timeout_seconds,
                retries={"max_attempts": 2, "mode": "standard"},
            )
            self._client = session.client("bedrock-runtime", config=boto_config)
            return self._client
        except Exception as exc:
            sanitized = sanitize_text(str(exc))
            logger.warning("Could not initialize boto3 bedrock-runtime client: %s", sanitized)
            return None

    def get_config_status(self) -> BedrockConfigStatus:
        """
        Inspects AWS credential provider chain without exposing secret keys or tokens.
        Reports truthful status reflecting whether credentials exist, are expired, or live inference succeeded.
        """
        try:
            session = boto3.Session(region_name=self.region_name)
            creds = session.get_credentials()
            if creds is None:
                return BedrockConfigStatus(
                    is_configured=False,
                    region=self.region_name,
                    model_id=self.model_id,
                    auth_mechanism="unconfigured",
                    status_message="No AWS credentials detected in environment, IAM role, or AWS profile.",
                )

            # Determine authentication provider type
            method = getattr(creds, "method", "unknown")
            if "iam-role" in method or "instance" in method or "container" in method:
                auth_type = "iam_role"
            elif "env" in method:
                auth_type = "environment_credentials"
            elif "shared" in method or "profile" in method:
                auth_type = "profile_credentials"
            else:
                auth_type = f"provider_{method}"

            # Provide truthful status based on recent inference results
            if self.last_error_category == "expired_credentials":
                status_msg = f"AWS credentials detected ({auth_type}), but session token is expired. Please refresh credentials."
            elif self.last_error_category == "access_denied":
                status_msg = f"AWS credentials detected ({auth_type}), but Bedrock model access denied for '{self.model_id}'."
            elif self.last_error_category == "model_or_profile_error":
                status_msg = f"AWS credentials detected ({auth_type}), but Bedrock model/inference-profile error occurred ({self.model_id})."
            elif self.last_inference_successful:
                status_msg = f"Live Amazon Bedrock inference verified via {auth_type} in {self.region_name} (Model: {self.model_id})."
            else:
                status_msg = f"AWS Bedrock configured via {auth_type} in {self.region_name} (Target model: {self.model_id})."

            return BedrockConfigStatus(
                is_configured=True,
                region=self.region_name,
                model_id=self.model_id,
                auth_mechanism=auth_type,
                status_message=status_msg,
            )
        except Exception as exc:
            sanitized = sanitize_text(str(exc))
            return BedrockConfigStatus(
                is_configured=False,
                region=self.region_name,
                model_id=self.model_id,
                auth_mechanism="error",
                status_message=f"Error inspecting AWS configuration: {sanitized}",
            )

    def _build_prompt_payload(
        self,
        report: str,
        decider_action: str,
        tool_output: Dict[str, Any],
        missing_information: Optional[List[str]] = None,
        location: Optional[str] = None,
    ) -> str:
        """Constructs an evidence-dense prompt payload for Bedrock Converse API."""
        is_synthetic = tool_output.get("is_synthetic_data", True)
        data_label = tool_output.get("data_label", "SYNTHETIC_DEV_DATASET")
        disclaimer = tool_output.get("disclaimer", "Sample development data.")
        known_limitations = tool_output.get("known_limitations", [])

        payload = {
            "task": "Synthesize environmental recommendation based strictly on the provided evidence.",
            "original_user_report": report,
            "reported_location": location or "Not explicitly specified",
            "decider_selected_action": decider_action,
            "data_provenance": {
                "is_synthetic_dataset": is_synthetic,
                "dataset_label": data_label,
                "disclaimer": disclaimer,
            },
            "actual_tool_output": tool_output,
            "missing_or_uncertain_information": missing_information or [],
            "known_limitations": known_limitations,
            "grounding_requirements": {
                "distinguish_observations_vs_assumptions": "Place verified tool numbers into supporting_evidence; operational hypotheses into assumptions.",
                "missing_measurements": "Explicitly identify missing sensors, unmeasured parameters, or uncertain fields in limitations.",
                "human_review_safeguards": "Specify municipal review and sensor ground-truthing in follow_up_actions and limitations.",
                "no_fabrication": "Never invent environmental measurements or present hypothetical benefits as measured outcomes.",
            },
            "required_response_format": {
                "summary": "String (1-2 sentences summarizing verified findings)",
                "recommended_next_step": "String (Single actionable priority step)",
                "supporting_evidence": ["List of strings citing specific tool numbers/findings"],
                "assumptions": ["List of transparent operational assumptions distinguishing observations"],
                "limitations": ["List of data constraints, missing measurements, and synthetic provenance"],
                "follow_up_actions": ["List of 2-3 concrete steps for municipal teams including human review"],
            },
        }
        return json.dumps(payload, indent=2)

    def generate_recommendation(
        self,
        report: str,
        decider_action: str,
        tool_output: Dict[str, Any],
        missing_information: Optional[List[str]] = None,
        location: Optional[str] = None,
    ) -> BedrockRecommendation:
        """
        Invokes Amazon Bedrock Converse API to synthesize evidence into a transparent recommendation.
        If credentials or model access are unavailable, safely falls back to a deterministic,
        clearly labeled development recommendation without fabricating model calls.
        """
        start_time = time.perf_counter()
        config_status = self.get_config_status()

        # If AWS is unconfigured, return transparent labeled dev mode response
        if not config_status.is_configured:
            logger.info("Bedrock is unconfigured. Emitting transparent development synthesis.")
            self.last_error_category = "missing_credentials"
            self.last_error_reason = "Bedrock credentials unconfigured"
            self.last_inference_successful = False
            return self._generate_dev_mode_synthesis(
                report=report,
                decider_action=decider_action,
                tool_output=tool_output,
                missing_information=missing_information,
                location=location,
                start_time=start_time,
                status_reason="Bedrock credentials unconfigured",
                status_category="missing_credentials",
            )

        client = self._get_client()
        if client is None:
            logger.warning("Bedrock client unavailable despite detected credentials. Using dev mode fallback.")
            self.last_error_category = "missing_credentials"
            self.last_error_reason = "Bedrock client initialization failed"
            self.last_inference_successful = False
            return self._generate_dev_mode_synthesis(
                report=report,
                decider_action=decider_action,
                tool_output=tool_output,
                missing_information=missing_information,
                location=location,
                start_time=start_time,
                status_reason="Bedrock client initialization failed",
                status_category="missing_credentials",
            )

        prompt_content = self._build_prompt_payload(
            report=report,
            decider_action=decider_action,
            tool_output=tool_output,
            missing_information=missing_information,
            location=location,
        )

        try:
            logger.info("Invoking Amazon Bedrock model '%s' in %s via Converse API...", self.model_id, self.region_name)

            response = client.converse(
                modelId=self.model_id,
                messages=[
                    {
                        "role": "user",
                        "content": [{"text": prompt_content}],
                    }
                ],
                system=[{"text": self.SYSTEM_PROMPT}],
                inferenceConfig={
                    "maxTokens": self.max_tokens,
                    "temperature": self.temperature,
                },
            )

            latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
            output_msg = response.get("output", {}).get("message", {})
            content_blocks = output_msg.get("content", [])
            raw_text = content_blocks[0].get("text", "") if content_blocks else ""

            # Robust JSON extraction
            cleaned_text = raw_text.strip()
            if cleaned_text.startswith("```json"):
                cleaned_text = cleaned_text[7:]
            elif cleaned_text.startswith("```"):
                cleaned_text = cleaned_text[3:]
            if cleaned_text.endswith("```"):
                cleaned_text = cleaned_text[:-3]
            cleaned_text = cleaned_text.strip()

            try:
                parsed = json.loads(cleaned_text)
            except json.JSONDecodeError:
                # Attempt to extract outermost JSON object { ... }
                start_idx = cleaned_text.find("{")
                end_idx = cleaned_text.rfind("}")
                if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                    parsed = json.loads(cleaned_text[start_idx : end_idx + 1])
                else:
                    raise

            # Grounding and safety checks
            summary = sanitize_text(parsed.get("summary", "Analysis completed."))
            recommended_next_step = sanitize_text(parsed.get("recommended_next_step", "Review tool findings."))
            supporting_evidence = [sanitize_text(s) for s in parsed.get("supporting_evidence", [])]
            assumptions = [sanitize_text(s) for s in parsed.get("assumptions", [])]
            limitations = [sanitize_text(s) for s in parsed.get("limitations", [])]
            follow_up_actions = [sanitize_text(s) for s in parsed.get("follow_up_actions", [])]

            # Enforce human-review safeguard
            if not any("human review" in lim.lower() for lim in limitations):
                limitations.append("Municipal human review required prior to operational dispatch or capital allocation.")

            # Record success
            self.last_inference_successful = True
            self.last_error_category = None
            self.last_error_reason = None

            return BedrockRecommendation(
                summary=summary,
                recommended_next_step=recommended_next_step,
                supporting_evidence=supporting_evidence,
                assumptions=assumptions,
                limitations=limitations,
                follow_up_actions=follow_up_actions,
                model_id=self.model_id,
                is_live_bedrock=True,
                data_provenance=tool_output.get("data_label", "SYNTHETIC_DEV_DATASET"),
                latency_ms=latency_ms,
                status="success",
            )

        except (ClientError, BotoCoreError, EndpointConnectionError, ReadTimeoutError) as aws_err:
            category, reason = classify_aws_error(aws_err, model_id=self.model_id, region_name=self.region_name)
            self.last_error_category = category
            self.last_error_reason = reason
            self.last_inference_successful = False
            logger.error("Bedrock API call failed [%s]: %s", category, reason)

            return self._generate_dev_mode_synthesis(
                report=report,
                decider_action=decider_action,
                tool_output=tool_output,
                missing_information=missing_information,
                location=location,
                start_time=start_time,
                status_reason=reason,
                status_category=category,
            )

        except (json.JSONDecodeError, Exception) as parse_err:
            category = "formatting_error"
            reason = f"Bedrock response formatting error ({type(parse_err).__name__})"
            self.last_error_category = category
            self.last_error_reason = reason
            self.last_inference_successful = False
            logger.error("Failed to parse Bedrock response: %s", sanitize_text(str(parse_err)))

            return self._generate_dev_mode_synthesis(
                report=report,
                decider_action=decider_action,
                tool_output=tool_output,
                missing_information=missing_information,
                location=location,
                start_time=start_time,
                status_reason=reason,
                status_category=category,
            )

    def _generate_dev_mode_synthesis(
        self,
        report: str,
        decider_action: str,
        tool_output: Dict[str, Any],
        missing_information: Optional[List[str]],
        location: Optional[str],
        start_time: float,
        status_reason: str,
        status_category: str = "fallback",
    ) -> BedrockRecommendation:
        """
        Deterministic, transparent synthesis used when Amazon Bedrock is unconfigured or unavailable.
        Clearly labeled as DEV_MODE with is_live_bedrock=False to avoid fabricating LLM outputs.
        Distinguishes supplied observations from assumptions and identifies missing measurements.
        """
        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
        loc = location or tool_output.get("location_name", "Reported Zone")
        tool_summary = tool_output.get("analysis_summary", "")

        evidence: List[str] = []
        assumptions: List[str] = [
            f"Execution conducted in Development Fallback Mode ({status_reason}).",
            "All cited environmental values originate strictly from the selected tool execution.",
        ]
        limitations: List[str] = list(tool_output.get("known_limitations", []))
        limitations.append(
            f"Fallback Reason: {status_reason}. Amazon Bedrock generative inference was not executed; recommendation is structured via deterministic rule-engine."
        )
        limitations.append("Municipal human review and field sensor ground-truthing are required before deployment.")

        if missing_information:
            limitations.append(f"Identified missing measurements: {', '.join(missing_information)}.")

        follow_up: List[str] = [
            f"Configure or refresh AWS credentials / verify Bedrock access ({status_reason}).",
            "Verify ground telemetry with local sensors before municipal deployment.",
        ]

        # Extract specific evidence based on action
        if decider_action == "ANALYZE_HEAT":
            ambient = tool_output.get("observed_ambient_temp_c", "N/A")
            surface = tool_output.get("observed_surface_temp_c", "N/A")
            severity = tool_output.get("heat_severity_level", "N/A")
            evidence.append(f"Measured ambient temperature: {ambient}°C with surface temperature of {surface}°C.")
            evidence.append(f"Thermal severity index evaluated as: {severity}.")
            recommended_step = f"Deploy emergency mobile hydration stations and issue thermal advisory for {loc}."

        elif decider_action == "CHECK_VEGETATION":
            canopy = tool_output.get("canopy_coverage_pct", "N/A")
            deficit = tool_output.get("canopy_deficit_pct", "N/A")
            potential = tool_output.get("estimated_cooling_potential_c", "N/A")
            evidence.append(f"Existing tree canopy coverage is {canopy}% versus municipal target of 30% (deficit: {deficit}%).")
            evidence.append(f"Projected localized cooling benefit from canopy expansion: {potential}°C.")
            recommended_step = f"Prioritize street tree plantings and permeable soil installations across {loc} to address {deficit}% deficit."

        elif decider_action == "CHECK_EXPOSURE":
            stops = tool_output.get("transit_stops_count", 0)
            commuters = tool_output.get("daily_transit_commuters", 0)
            unshaded = tool_output.get("unshaded_waiting_areas", 0)
            evidence.append(f"{stops} transit stops serving ~{commuters:,} daily commuters identified in sector.")
            evidence.append(f"{unshaded} transit boarding areas currently lack physical shade structures.")
            recommended_step = f"Fast-track installation of engineered shade structures across the {unshaded} unshaded transit platforms in {loc}."

        elif decider_action == "COMPARE_INTERVENTIONS":
            fast = tool_output.get("recommended_fast_track_intervention", "Engineered shade structures")
            primary = tool_output.get("recommended_primary_intervention", "Urban tree canopy expansion")
            evidence.append(f"Fast-track mitigation identified: '{fast}'.")
            evidence.append(f"Long-term structural resilience recommendation: '{primary}'.")
            recommended_step = f"Initiate immediate deployment of '{fast}' while funding '{primary}' capital planning."

        elif decider_action == "REQUEST_MORE_DATA":
            gaps = tool_output.get("missing_parameters", [])
            evidence.append(f"Identified {len(gaps)} critical data gaps required for definitive modeling.")
            recommended_step = "Issue structured data request to user and pull automated ASOS weather station observations."
            follow_up.append("Review suggested telemetry sources: NOAA ASOS, USGS Landsat-9, Sentinel-2.")

        else:
            recommended_step = "Review environmental assessment output."

        summary = (
            f"[DEV MODE SYNTHESIS - {status_reason}] {tool_summary} "
            f"Action selected by Strands Decider 2B was '{decider_action}'."
        )

        return BedrockRecommendation(
            summary=sanitize_text(summary),
            recommended_next_step=sanitize_text(recommended_step),
            supporting_evidence=[sanitize_text(e) for e in evidence],
            assumptions=[sanitize_text(a) for a in assumptions],
            limitations=[sanitize_text(l) for l in limitations],
            follow_up_actions=[sanitize_text(f) for f in follow_up],
            model_id=f"{self.model_id} (fallback: {status_category})",
            is_live_bedrock=False,
            data_provenance=tool_output.get("data_label", "SYNTHETIC_DEV_DATASET"),
            latency_ms=elapsed_ms,
            status="dev_mode_fallback",
            fallback_reason=status_reason,
        )
