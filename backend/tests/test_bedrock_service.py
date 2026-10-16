"""
Unit tests for the Amazon Bedrock integration service.
Verifies prompt construction, response parsing, dev-mode fallbacks, and error handling.
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
)


def test_bedrock_config_status_when_unconfigured():
    """Service should report unconfigured status when no AWS credentials are present."""
    service = BedrockService(region_name="us-east-1")
    # Patch session to return no credentials
    with patch("boto3.Session.get_credentials", return_value=None):
        status = service.get_config_status()
        assert isinstance(status, BedrockConfigStatus)
        assert status.is_configured is False
        assert status.auth_mechanism == "unconfigured"
        assert "No AWS credentials detected" in status.status_message


def test_bedrock_prompt_payload_structure():
    """Prompt payload must contain report, Decider choice, tool output, and synthetic provenance."""
    service = BedrockService()
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
                            "limitations": ["Data sourced from synthetic development telemetry."],
                            "follow_up_actions": ["Dispatch municipal outreach staff."]
                        })
                    }
                ]
            }
        }
    }
    mock_client.converse.return_value = mock_bedrock_response

    # Force service to use our mock client
    service = BedrockService(boto3_client=mock_client)
    with patch.object(service, "get_config_status", return_value=BedrockConfigStatus(
        is_configured=True, region="us-east-1", model_id="test-model", auth_mechanism="iam_role", status_message="OK"
    )):
        rec = service.generate_recommendation(
            report="Very hot outside",
            decider_action="ANALYZE_HEAT",
            tool_output={"tool_name": "ANALYZE_HEAT", "observed_ambient_temp_c": 38.5},
        )

        assert isinstance(rec, BedrockRecommendation)
        assert rec.is_live_bedrock is True
        assert rec.status == "success"
        assert "Severe urban heat island" in rec.summary
        assert "Deploy mobile misting tents" in rec.recommended_next_step
        assert len(rec.supporting_evidence) == 1
        assert rec.latency_ms >= 0.0


def test_bedrock_dev_mode_fallback_when_unconfigured():
    """When unconfigured, service should generate a transparent deterministic synthesis."""
    service = BedrockService()
    with patch.object(service, "get_config_status", return_value=BedrockConfigStatus(
        is_configured=False, region="us-east-1", model_id="test-model", auth_mechanism="unconfigured", status_message="No creds"
    )):
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


def test_bedrock_error_handling_fallback():
    """Client error or timeout should gracefully fall back to dev mode synthesis without crashing."""
    mock_client = MagicMock()
    mock_client.converse.side_effect = ReadTimeoutError(endpoint_url="https://bedrock.us-east-1.amazonaws.com")

    service = BedrockService(boto3_client=mock_client)
    with patch.object(service, "get_config_status", return_value=BedrockConfigStatus(
        is_configured=True, region="us-east-1", model_id="test-model", auth_mechanism="iam_role", status_message="OK"
    )):
        rec = service.generate_recommendation(
            report="Very hot outside",
            decider_action="ANALYZE_HEAT",
            tool_output={"tool_name": "ANALYZE_HEAT", "observed_ambient_temp_c": 36.0},
        )

        assert isinstance(rec, BedrockRecommendation)
        assert rec.is_live_bedrock is False
        assert rec.status == "dev_mode_fallback"
        assert "DEV MODE SYNTHESIS" in rec.summary
