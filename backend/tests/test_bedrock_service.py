"""
Unit tests for the Amazon Bedrock integration service.
Verifies prompt construction, Converse API execution, response parsing, dev-mode fallbacks,
truthful live vs. fallback status reporting, and credential leakage prevention.
Does NOT require real AWS credentials for execution.
"""

import json
from unittest.mock import MagicMock, patch
import pytest
from botocore.exceptions import ClientError, ReadTimeoutError

from backend.services.bedrock_service import (
    BedrockConfigStatus,
    BedrockRecommendation,
    BedrockService,
    classify_aws_error,
    sanitize_text,
)
from scripts.smoke_test_bedrock import run_smoke_test


def test_bedrock_config_status_when_unconfigured():
    """Service should report unconfigured status when no AWS credentials are present."""
    service = BedrockService(region_name="us-east-1")
    with patch("boto3.Session.get_credentials", return_value=None):
        status = service.get_config_status()
        assert isinstance(status, BedrockConfigStatus)
        assert status.is_configured is False
        assert status.auth_mechanism == "unconfigured"
        assert "No AWS credentials detected" in status.status_message


def test_bedrock_config_status_when_configured():
    """Service reports configured status with mechanism and target model."""
    mock_creds = MagicMock()
    mock_creds.method = "env"

    service = BedrockService(region_name="us-east-1", model_id="global.amazon.nova-2-lite-v1:0")
    with patch("boto3.Session.get_credentials", return_value=mock_creds):
        status = service.get_config_status()
        assert status.is_configured is True
        assert status.auth_mechanism == "environment_credentials"
        assert status.region == "us-east-1"
        assert status.model_id == "global.amazon.nova-2-lite-v1:0"
        assert "AWS Bedrock configured" in status.status_message


def test_bedrock_prompt_payload_structure():
    """Prompt payload must contain report, Decider choice, tool output, and synthetic provenance."""
    service = BedrockService(model_id="global.amazon.nova-2-lite-v1:0")
    sample_tool_output = {
        "tool_name": "ANALYZE_HEAT",
        "observed_ambient_temp_c": 38.5,
        "is_synthetic_data": True,
        "data_label": "SYNTHETIC_DEV_DATASET_V1",
        "known_limitations": ["Sensor error +-0.5C"],
    }

    payload_str = service._build_prompt_payload(
        report="High heat recorded near transit stop.",
        decider_action="ANALYZE_HEAT",
        tool_output=sample_tool_output,
        missing_information=["Numeric canopy percentage"],
        location="Downtown Plaza",
    )

    payload = json.loads(payload_str)
    assert payload["decider_selected_action"] == "ANALYZE_HEAT"
    assert payload["data_provenance"]["is_synthetic_dataset"] is True
    assert payload["actual_tool_output"]["observed_ambient_temp_c"] == 38.5
    assert "Numeric canopy percentage" in payload["missing_or_uncertain_information"]
    assert "grounding_requirements" in payload
    assert "required_response_format" in payload


def test_bedrock_successful_mocked_converse_call():
    """Validates parsing of live Bedrock converse API response."""
    mock_client = MagicMock()
    mock_bedrock_response = {
        "output": {
            "message": {
                "role": "assistant",
                "content": [
                    {
                        "text": json.dumps({
                            "summary": "Severe urban heat island conditions detected in Downtown Plaza.",
                            "recommended_next_step": "Deploy mobile misting tents and issue heat health warning.",
                            "supporting_evidence": ["Ambient temperature reached 38.5°C."],
                            "assumptions": ["Assumes daytime pedestrian transit peak."],
                            "limitations": [
                                "Data sourced from synthetic development telemetry.",
                                "Municipal human review required prior to operational dispatch.",
                            ],
                            "follow_up_actions": ["Dispatch municipal outreach staff."],
                        })
                    }
                ],
            }
        }
    }
    mock_client.converse.return_value = mock_bedrock_response

    service = BedrockService(
        model_id="global.amazon.nova-2-lite-v1:0",
        boto3_client=mock_client,
    )
    with patch.object(
        service,
        "get_config_status",
        return_value=BedrockConfigStatus(
            is_configured=True,
            region="us-east-1",
            model_id="global.amazon.nova-2-lite-v1:0",
            auth_mechanism="iam_role",
            status_message="OK",
        ),
    ):
        rec = service.generate_recommendation(
            report="Very hot outside",
            decider_action="ANALYZE_HEAT",
            tool_output={"tool_name": "ANALYZE_HEAT", "observed_ambient_temp_c": 38.5},
        )

        assert isinstance(rec, BedrockRecommendation)
        assert rec.is_live_bedrock is True
        assert rec.status == "success"
        assert rec.model_id == "global.amazon.nova-2-lite-v1:0"
        assert "Severe urban heat island" in rec.summary
        assert "Deploy mobile misting tents" in rec.recommended_next_step
        assert len(rec.supporting_evidence) == 1
        assert rec.latency_ms >= 0.0
        # Service should record success
        assert service.last_inference_successful is True


def test_bedrock_robust_json_parsing_with_markdown_ticks():
    """Converse responses wrapped in ```json markdown code fences are cleanly parsed."""
    mock_client = MagicMock()
    inner_json = json.dumps({
        "summary": "High exposure at bus transit hub.",
        "recommended_next_step": "Install shade structures.",
        "supporting_evidence": ["3 unshaded stops."],
        "assumptions": ["Observations distinct from assumptions."],
        "limitations": ["Municipal human review required."],
        "follow_up_actions": ["Dispatch field inspection."],
    })
    mock_client.converse.return_value = {
        "output": {
            "message": {
                "role": "assistant",
                "content": [{"text": f"```json\n{inner_json}\n```"}],
            }
        }
    }

    service = BedrockService(boto3_client=mock_client)
    with patch.object(
        service,
        "get_config_status",
        return_value=BedrockConfigStatus(
            is_configured=True,
            region="us-east-1",
            model_id="global.amazon.nova-2-lite-v1:0",
            auth_mechanism="environment_credentials",
            status_message="OK",
        ),
    ):
        rec = service.generate_recommendation(
            report="Transit stop report",
            decider_action="CHECK_EXPOSURE",
            tool_output={"tool_name": "CHECK_EXPOSURE"},
        )
        assert rec.is_live_bedrock is True
        assert rec.status == "success"
        assert rec.summary == "High exposure at bus transit hub."


def test_bedrock_dev_mode_fallback_when_unconfigured():
    """When unconfigured, service should generate a transparent deterministic synthesis."""
    service = BedrockService()
    with patch.object(
        service,
        "get_config_status",
        return_value=BedrockConfigStatus(
            is_configured=False,
            region="us-east-1",
            model_id="global.amazon.nova-2-lite-v1:0",
            auth_mechanism="unconfigured",
            status_message="No creds",
        ),
    ):
        rec = service.generate_recommendation(
            report="Crowded bus stop with no shade.",
            decider_action="CHECK_EXPOSURE",
            tool_output={
                "tool_name": "CHECK_EXPOSURE",
                "location_name": "Market Plaza",
                "transit_stops_count": 5,
                "daily_transit_commuters": 8000,
                "unshaded_waiting_areas": 3,
                "known_limitations": ["Sample data"],
            },
        )

        assert isinstance(rec, BedrockRecommendation)
        assert rec.is_live_bedrock is False
        assert rec.status == "dev_mode_fallback"
        assert "DEV MODE SYNTHESIS" in rec.summary
        assert "Engineered shade" in rec.recommended_next_step or "shade structures" in rec.recommended_next_step
        assert any("transit" in ev.lower() for ev in rec.supporting_evidence)
        assert service.last_inference_successful is False


def test_bedrock_expired_credentials_fallback():
    """Expired credentials raise ExpiredTokenException, triggering safe fallback with truthful status."""
    mock_client = MagicMock()
    mock_client.converse.side_effect = ClientError(
        {"Error": {"Code": "ExpiredTokenException", "Message": "The security token included in the request is expired"}},
        "Converse",
    )

    mock_creds = MagicMock()
    mock_creds.method = "env"

    service = BedrockService(boto3_client=mock_client)
    with patch("boto3.Session.get_credentials", return_value=mock_creds):
        rec = service.generate_recommendation(
            report="Very hot outside",
            decider_action="ANALYZE_HEAT",
            tool_output={"tool_name": "ANALYZE_HEAT", "observed_ambient_temp_c": 36.0},
        )

        # Fallback verification
        assert isinstance(rec, BedrockRecommendation)
        assert rec.is_live_bedrock is False
        assert rec.status == "dev_mode_fallback"
        assert "expired" in (rec.fallback_reason or "").lower()
        assert "DEV MODE SYNTHESIS" in rec.summary
        assert service.last_error_category == "expired_credentials"
        assert service.last_inference_successful is False

        # Status check reflects expired credentials
        cfg = service.get_config_status()
        assert "expired" in cfg.status_message.lower()


def test_bedrock_access_denied_fallback():
    """AccessDeniedException triggers fallback and explains IAM/entitlement issue."""
    mock_client = MagicMock()
    mock_client.converse.side_effect = ClientError(
        {"Error": {"Code": "AccessDeniedException", "Message": "User is not authorized to perform: bedrock:InvokeModel"}},
        "Converse",
    )

    mock_creds = MagicMock()
    mock_creds.method = "iam-role"

    service = BedrockService(boto3_client=mock_client)
    with patch("boto3.Session.get_credentials", return_value=mock_creds):
        rec = service.generate_recommendation(
            report="Need canopy analysis",
            decider_action="CHECK_VEGETATION",
            tool_output={"tool_name": "CHECK_VEGETATION", "canopy_coverage_pct": 14.5, "canopy_deficit_pct": 15.5},
        )

        assert rec.is_live_bedrock is False
        assert rec.status == "dev_mode_fallback"
        assert "access denied" in (rec.fallback_reason or "").lower()
        assert service.last_error_category == "access_denied"

        cfg = service.get_config_status()
        assert "access denied" in cfg.status_message.lower()


def test_bedrock_model_or_inference_profile_error_fallback():
    """ValidationException for model ID triggers fallback with model/profile error category."""
    mock_client = MagicMock()
    mock_client.converse.side_effect = ClientError(
        {"Error": {"Code": "ValidationException", "Message": "The provided model identifier is invalid."}},
        "Converse",
    )

    mock_creds = MagicMock()
    mock_creds.method = "env"

    service = BedrockService(boto3_client=mock_client)
    with patch("boto3.Session.get_credentials", return_value=mock_creds):
        rec = service.generate_recommendation(
            report="Compare heat mitigation options",
            decider_action="COMPARE_INTERVENTIONS",
            tool_output={"tool_name": "COMPARE_INTERVENTIONS"},
        )

        assert rec.is_live_bedrock is False
        assert rec.status == "dev_mode_fallback"
        assert "model or inference-profile error" in (rec.fallback_reason or "").lower()
        assert service.last_error_category == "model_or_profile_error"


def test_bedrock_throttling_and_service_failures_fallback():
    """ThrottlingException is caught and handled with safe fallback."""
    mock_client = MagicMock()
    mock_client.converse.side_effect = ClientError(
        {"Error": {"Code": "ThrottlingException", "Message": "Rate exceeded"}},
        "Converse",
    )

    mock_creds = MagicMock()
    mock_creds.method = "env"

    service = BedrockService(boto3_client=mock_client)
    with patch("boto3.Session.get_credentials", return_value=mock_creds):
        rec = service.generate_recommendation(
            report="Heat spike",
            decider_action="ANALYZE_HEAT",
            tool_output={"tool_name": "ANALYZE_HEAT", "observed_ambient_temp_c": 40.0},
        )

        assert rec.is_live_bedrock is False
        assert rec.status == "dev_mode_fallback"
        assert "rate limit" in (rec.fallback_reason or "").lower() or "service failure" in (rec.fallback_reason or "").lower()
        assert service.last_error_category == "throttling_or_service_error"


def test_bedrock_network_timeout_fallback():
    """ReadTimeoutError gracefully falls back to dev mode synthesis without crashing."""
    mock_client = MagicMock()
    mock_client.converse.side_effect = ReadTimeoutError(endpoint_url="https://bedrock-runtime.us-east-1.amazonaws.com")

    service = BedrockService(boto3_client=mock_client)
    with patch.object(
        service,
        "get_config_status",
        return_value=BedrockConfigStatus(
            is_configured=True,
            region="us-east-1",
            model_id="global.amazon.nova-2-lite-v1:0",
            auth_mechanism="iam_role",
            status_message="OK",
        ),
    ):
        rec = service.generate_recommendation(
            report="Very hot outside",
            decider_action="ANALYZE_HEAT",
            tool_output={"tool_name": "ANALYZE_HEAT", "observed_ambient_temp_c": 36.0},
        )

        assert isinstance(rec, BedrockRecommendation)
        assert rec.is_live_bedrock is False
        assert rec.status == "dev_mode_fallback"
        assert "DEV MODE SYNTHESIS" in rec.summary
        assert "timeout" in (rec.fallback_reason or "").lower()


def test_bedrock_truthful_live_vs_fallback_status():
    """Live inference status is strictly False whenever an exception occurs; never mislabeled."""
    mock_client = MagicMock()
    mock_client.converse.side_effect = RuntimeError("Fatal network error")

    service = BedrockService(boto3_client=mock_client)
    with patch.object(
        service,
        "get_config_status",
        return_value=BedrockConfigStatus(
            is_configured=True,
            region="us-east-1",
            model_id="global.amazon.nova-2-lite-v1:0",
            auth_mechanism="iam_role",
            status_message="OK",
        ),
    ):
        rec = service.generate_recommendation(
            report="Need more data",
            decider_action="REQUEST_MORE_DATA",
            tool_output={"tool_name": "REQUEST_MORE_DATA", "missing_parameters": ["sensor_id"]},
        )
        assert rec.is_live_bedrock is False
        assert rec.status != "success"
        assert rec.status == "dev_mode_fallback"


def test_bedrock_credential_leakage_prevention():
    """Confirms access keys and secrets are scrubbed and never appear in outputs or status messages."""
    fake_key = "AKIAIOSFODNN7EXAMPLE"
    fake_secret = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"

    dirty_text = f"Failed request with key {fake_key} and aws_secret_access_key='{fake_secret}'"
    cleaned = sanitize_text(dirty_text)

    assert fake_key not in cleaned
    assert fake_secret not in cleaned
    assert "[REDACTED_AWS_KEY]" in cleaned
    assert "[REDACTED_CREDENTIAL]" in cleaned

    # Test error classifier scrubs credentials
    category, reason = classify_aws_error(
        Exception(f"Error accessing with {fake_key}"),
        model_id="global.amazon.nova-2-lite-v1:0",
        region_name="us-east-1",
    )
    assert fake_key not in reason


def test_smoke_test_script_execution_without_credentials():
    """Smoke test script exits with returncode 1 when no credentials are present."""
    with patch("boto3.Session.get_credentials", return_value=None):
        code = run_smoke_test(region="us-east-1", model_id="global.amazon.nova-2-lite-v1:0")
        assert code == 1


def test_smoke_test_script_execution_successful():
    """Smoke test script exits with returncode 0 when Converse responds."""
    mock_client = MagicMock()
    mock_client.converse.return_value = {
        "output": {
            "message": {
                "role": "assistant",
                "content": [{"text": "HEATSHIELD_BEDROCK_OK"}],
            }
        }
    }
    mock_creds = MagicMock()
    mock_creds.method = "env"

    with patch("boto3.Session.get_credentials", return_value=mock_creds), patch(
        "boto3.Session.client", return_value=mock_client
    ):
        code = run_smoke_test(region="us-east-1", model_id="global.amazon.nova-2-lite-v1:0")
        assert code == 0


@pytest.mark.parametrize(
    "action,tool_output,expected_step_keyword,expected_evidence_keyword",
    [
        (
            "ANALYZE_HEAT",
            {
                "tool_name": "ANALYZE_HEAT",
                "location_name": "Downtown Central Plaza",
                "observed_ambient_temp_c": 37.5,
                "observed_surface_temp_c": 45.0,
                "heat_severity_level": "SEVERE",
                "analysis_summary": "Severe thermal conditions detected.",
            },
            "hydration",
            "37.5",
        ),
        (
            "CHECK_VEGETATION",
            {
                "tool_name": "CHECK_VEGETATION",
                "location_name": "Eastside Logistics Corridor",
                "canopy_coverage_pct": 12.5,
                "canopy_deficit_pct": 17.5,
                "estimated_cooling_potential_c": 2.2,
                "analysis_summary": "Canopy deficit detected.",
            },
            "tree plantings",
            "12.5%",
        ),
        (
            "CHECK_EXPOSURE",
            {
                "tool_name": "CHECK_EXPOSURE",
                "location_name": "Transit Center",
                "transit_stops_count": 8,
                "daily_transit_commuters": 12000,
                "unshaded_waiting_areas": 4,
                "analysis_summary": "High passenger exposure detected.",
            },
            "shade structures",
            "12,000",
        ),
        (
            "COMPARE_INTERVENTIONS",
            {
                "tool_name": "COMPARE_INTERVENTIONS",
                "location_name": "Civic Center",
                "recommended_fast_track_intervention": "Engineered shade structures",
                "recommended_primary_intervention": "Urban tree canopy expansion",
                "analysis_summary": "Comparative interventions ranked.",
            },
            "Engineered shade structures",
            "Engineered shade structures",
        ),
        (
            "REQUEST_MORE_DATA",
            {
                "tool_name": "REQUEST_MORE_DATA",
                "location_name": "Suburban Sector",
                "missing_parameters": ["ambient_temperature", "canopy_pct"],
                "analysis_summary": "Data gaps identified.",
            },
            "data request",
            "2 critical data gaps",
        ),
    ],
)
def test_bedrock_dev_mode_fallback_for_all_five_actions(
    action: str,
    tool_output: dict,
    expected_step_keyword: str,
    expected_evidence_keyword: str,
):
    """Verifies that development mode synthesis properly tailors recommendations for all 5 actions."""
    service = BedrockService(model_id="global.amazon.nova-2-lite-v1:0")
    rec = service._generate_dev_mode_synthesis(
        report="Environmental test narrative for fallback synthesis.",
        decider_action=action,
        tool_output=tool_output,
        missing_information=["Specific sensor ID"],
        location=tool_output.get("location_name"),
        start_time=0.0,
        status_reason="AWS credentials unconfigured",
        status_category="missing_credentials",
    )

    # Invariants for fallback mode
    assert isinstance(rec, BedrockRecommendation)
    assert rec.is_live_bedrock is False
    assert rec.status == "dev_mode_fallback"
    assert rec.fallback_reason == "AWS credentials unconfigured"
    assert rec.model_id == "global.amazon.nova-2-lite-v1:0 (fallback: missing_credentials)"

    # Summary
    assert "[DEV MODE SYNTHESIS - AWS credentials unconfigured]" in rec.summary
    assert action in rec.summary

    # Action-specific recommendation step
    assert expected_step_keyword.lower() in rec.recommended_next_step.lower()

    # Action-specific empirical evidence
    assert any(expected_evidence_keyword.lower() in ev.lower() for ev in rec.supporting_evidence)

    # Transparent assumptions and limitations
    assert any("Development Fallback Mode" in a for a in rec.assumptions)
    assert any("human review" in lim.lower() for lim in rec.limitations)
    assert any("missing measurements" in lim.lower() for lim in rec.limitations)
    assert len(rec.follow_up_actions) >= 2
