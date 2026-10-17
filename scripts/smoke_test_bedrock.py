"""
Amazon Bedrock Converse Manual Smoke Test for HeatShield AI.

Manually invoked diagnostic script that verifies live Bedrock Converse API connectivity
using the same configuration and credential provider chain as the main application.
Does NOT run automatically at startup and NEVER logs secrets or tokens.
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from typing import Optional

# Ensure project root is on sys.path so backend imports work
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError

from backend.services.bedrock_service import classify_aws_error, sanitize_text


def run_smoke_test(
    region: Optional[str] = None,
    model_id: Optional[str] = None,
    timeout_seconds: int = 15,
) -> int:
    """
    Executes a minimal test request against Amazon Bedrock Converse API.
    Returns 0 on success, 1 on failure.
    """
    target_region = (
        region
        or os.getenv("AWS_REGION")
        or os.getenv("AWS_DEFAULT_REGION")
        or "us-east-1"
    )
    target_model_id = (
        model_id
        or os.getenv("BEDROCK_MODEL_ID")
        or "global.amazon.nova-2-lite-v1:0"
    )

    print("=" * 65)
    print(" HeatShield AI - Amazon Bedrock Converse Smoke Test")
    print("=" * 65)
    print(f" Target Region : {target_region}")
    print(f" Target Model  : {target_model_id}")

    # Inspect credential provider chain without exposing secret values
    try:
        session = boto3.Session(region_name=target_region)
        creds = session.get_credentials()
    except Exception as exc:
        print("\n[SMOKE TEST FAILED] Error inspecting AWS credentials:")
        print(f"  {sanitize_text(str(exc))}")
        return 1

    if creds is None:
        print("\n[SMOKE TEST FAILED] No AWS credentials detected in environment.")
        print("  The standard AWS credential provider chain was inspected:")
        print("  - Environment variables (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_SESSION_TOKEN)")
        print("  - AWS Shared Credentials file (~/.aws/credentials)")
        print("  - AWS SSO / IAM Role / EC2 Instance Metadata")
        print("\nTo test with temporary AWS Workshop Studio credentials in PowerShell, run:")
        print("  $env:AWS_DEFAULT_REGION = \"us-east-1\"")
        print("  $env:AWS_REGION = \"us-east-1\"")
        print("  $env:BEDROCK_MODEL_ID = \"global.amazon.nova-2-lite-v1:0\"")
        print("  $env:AWS_ACCESS_KEY_ID = \"<YOUR_ACCESS_KEY_ID>\"")
        print("  $env:AWS_SECRET_ACCESS_KEY = \"<YOUR_SECRET_ACCESS_KEY>\"")
        print("  $env:AWS_SESSION_TOKEN = \"<YOUR_SESSION_TOKEN>\"")
        print("  python scripts/smoke_test_bedrock.py")
        print("\nNote: Never commit credentials to Git or save them into source files.")
        return 1

    method = getattr(creds, "method", "unknown")
    if "iam-role" in method or "instance" in method or "container" in method:
        auth_type = "IAM Role / Instance Profile"
    elif "env" in method:
        auth_type = "Environment Variables (Temporary Session or Access Key)"
    elif "shared" in method or "profile" in method:
        auth_type = "AWS Profile (~/.aws/credentials)"
    else:
        auth_type = f"Provider: {method}"

    print(f" Auth Provider : {auth_type}")
    print("-" * 65)
    print(" Invoking Bedrock Converse API with prompt: 'Respond with HEATSHIELD_BEDROCK_OK only.'")

    boto_config = Config(
        connect_timeout=5,
        read_timeout=timeout_seconds,
        retries={"max_attempts": 2, "mode": "standard"},
    )

    start_time = time.perf_counter()
    try:
        client = session.client("bedrock-runtime", config=boto_config)
        response = client.converse(
            modelId=target_model_id,
            messages=[
                {
                    "role": "user",
                    "content": [{"text": "Respond with HEATSHIELD_BEDROCK_OK only."}],
                }
            ],
            inferenceConfig={
                "maxTokens": 32,
                "temperature": 0.0,
            },
        )
        latency_ms = (time.perf_counter() - start_time) * 1000

        output_msg = response.get("output", {}).get("message", {})
        content_blocks = output_msg.get("content", [])
        raw_text = content_blocks[0].get("text", "") if content_blocks else ""
        cleaned_text = sanitize_text(raw_text.strip())

        print("\n" + "=" * 65)
        print(" [SUCCESS] Amazon Bedrock Converse Live Inference Verified!")
        print("=" * 65)
        print(f" Model Response : {cleaned_text}")
        print(f" Roundtrip Time : {latency_ms:.2f} ms")
        print(f" Status         : LIVE_BEDROCK_OPERATIONAL")
        print("=" * 65)
        return 0

    except (ClientError, BotoCoreError, Exception) as err:
        latency_ms = (time.perf_counter() - start_time) * 1000
        category, reason = classify_aws_error(err, model_id=target_model_id, region_name=target_region)

        print("\n" + "=" * 65)
        print(f" [SMOKE TEST FAILED] Bedrock invocation failed ({category})")
        print("=" * 65)
        print(f" Reason         : {reason}")
        print(f" Elapsed Time   : {latency_ms:.2f} ms")

        # Specific actionable troubleshooting advice without exposing secrets
        if category == "expired_credentials":
            print("\nTroubleshooting Guidance:")
            print("  Your AWS temporary credentials / session token have expired.")
            print("  1. Return to your AWS Workshop Studio portal.")
            print("  2. Copy fresh temporary credentials (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_SESSION_TOKEN).")
            print("  3. Set them in your current terminal session and re-run.")
        elif category == "access_denied":
            print("\nTroubleshooting Guidance:")
            print(f"  Access was denied when attempting to invoke model '{target_model_id}'.")
            print("  1. Verify your IAM identity has 'bedrock:InvokeModel' permission.")
            print("  2. In the AWS Bedrock Console, verify model access is requested/enabled for Amazon Nova 2 Lite.")
            print("  3. If using an inference profile, try the US inference profile: 'us.amazon.nova-2-lite-v1:0'.")
        elif category == "model_or_profile_error":
            print("\nTroubleshooting Guidance:")
            print(f"  The model ID or inference profile '{target_model_id}' was not recognized in '{target_region}'.")
            print("  Options for Amazon Nova 2 Lite in us-east-1:")
            print("  - Global inference profile: global.amazon.nova-2-lite-v1:0")
            print("  - US regional inference profile: us.amazon.nova-2-lite-v1:0")
            print("  - Regional model ID: amazon.nova-lite-v1:0")
        elif category == "throttling_or_service_error":
            print("\nTroubleshooting Guidance:")
            print("  Bedrock rate limits or service throttling occurred. Retry in a few seconds.")

        print("=" * 65)
        return 1


def main() -> int:
    parser = argparse.ArgumentParser(
        description="HeatShield AI Amazon Bedrock Converse Smoke Test",
    )
    parser.add_argument(
        "--region",
        default=None,
        help="AWS region (defaults to AWS_REGION or 'us-east-1')",
    )
    parser.add_argument(
        "--model-id",
        default=None,
        help="Bedrock model ID or inference profile (defaults to BEDROCK_MODEL_ID or 'global.amazon.nova-2-lite-v1:0')",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=15,
        help="Timeout in seconds (default: 15)",
    )
    args = parser.parse_args()
    return run_smoke_test(region=args.region, model_id=args.model_id, timeout_seconds=args.timeout)


if __name__ == "__main__":
    sys.exit(main())
