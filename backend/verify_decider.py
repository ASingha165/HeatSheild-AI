"""
Standalone verification script for Strands Decider 2B integration.

Executes a real typed choice decision using the official strands_decider package
for the sample environmental report specified in the challenge requirements.
"""

import os
import sys
import time
import json
from typing import Any

# Ensure project root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from strands_decider.schema import ChoiceQuestion, SystemOneRequest, SystemOneResponse
from strands_decider.infer import load_engine, EngineConfig, SystemOneEngine
from strands_decider.modeling import StrandsDeciderModel


def build_verification_payload() -> tuple[dict[str, Any], ChoiceQuestion]:
    """Constructs the structured state and typed question for environmental analysis."""
    
    state = {
        "report": "The neighborhood has high afternoon temperatures, low vegetation coverage, and a crowded bus stop.",
        "location": "Urban neighborhood (unspecified coordinates)",
        "reported_factors": [
            "high afternoon temperatures",
            "low vegetation coverage",
            "crowded bus stop"
        ],
        "temperature_observations": "Reported high afternoon temperatures; no sensor telemetry yet.",
        "vegetation_indicators": "Reported low canopy cover; satellite NDVI unconfirmed.",
        "exposure_indicators": "Crowded bus stop with public transit commuters exposed to sun/heat.",
        "missing_information": [
            "Exact ambient temperature (°C/°F)",
            "Quantitative tree canopy percentage",
            "Commuter exposure dwell duration"
        ],
        "available_tools": [
            "ANALYZE_HEAT",
            "CHECK_VEGETATION",
            "CHECK_EXPOSURE",
            "COMPARE_INTERVENTIONS",
            "REQUEST_MORE_DATA"
        ]
    }

    question = ChoiceQuestion(
        type="choice",
        instructions="Given the current environmental report and available evidence, which single analytical action should the agent execute next?",
        criteria={
            "ANALYZE_HEAT": "Analyze available temperature observations and explicitly identified heat-risk indicators.",
            "CHECK_VEGETATION": "Analyze available vegetation coverage and canopy deficit information.",
            "CHECK_EXPOSURE": "Evaluate indicators of human exposure such as nearby schools, crowded transit stops, and shaded public spaces.",
            "COMPARE_INTERVENTIONS": "Compare tree planting, shade structures, cool roofs, and shaded pedestrian routes using transparent assumptions.",
            "REQUEST_MORE_DATA": "Identify missing information and generate a structured clarification request when data is too sparse to evaluate."
        }
    )

    return state, question


def main() -> int:
    checkpoint = os.getenv("DECIDER_MODEL_CHECKPOINT", "StrandsAgents/strands-decider-2B-hobson-v21")
    device = os.getenv("DECIDER_DEVICE", "cpu")
    
    print("=" * 70)
    print("HeatShield AI - Strands Decider 2B Verification")
    print("=" * 70)
    print(f"Target Checkpoint: {checkpoint}")
    print(f"Target Device:     {device}")
    
    state, question = build_verification_payload()
    print("\nState Prepared:")
    print(json.dumps(state, indent=2))
    print("\nTyped Question:")
    print(f"Instructions: {question.instructions}")
    print("Allowed Action Options:")
    for opt, desc in question.criteria.items():
        print(f"  - {opt}: {desc}")
    
    print("\nAttempting to load real Strands Decider 2B model...")
    start_load = time.perf_counter()
    
    try:
        # Load engine using official load_engine from strands_decider.infer
        engine = load_engine(
            checkpoint=checkpoint,
            device=device,
            use_prefix_cache=True
        )
        load_time_s = time.perf_counter() - start_load
        print(f"Model loaded successfully in {load_time_s:.2f} seconds.")
        
        # Execute decision
        print("\nInvoking decision forward pass...")
        start_eval = time.perf_counter()
        
        response: SystemOneResponse = engine.ask(
            state=state,
            questions={"tool_selection": question}
        )
        eval_time_ms = (time.perf_counter() - start_eval) * 1000
        
        answer = response.answers.get("tool_selection")
        print("\n--- ACTUAL MODEL DECISION RESULT ---")
        print(f"Selected Choice:   {answer.choice}")
        print(f"Confidence:        {answer.confidence:.4f}")
        print(f"Latency:           {eval_time_ms:.2f} ms")
        print(f"Input Tokens:      {response.usage.input_tokens}")
        print(f"Output Decisions:  {response.usage.output_tokens}")
        print("\nPer-Option Probabilities:")
        for opt, prob in answer.probabilities.items():
            print(f"  {opt:24s}: {prob:.4f}")
            
        print("\nVerification status: SUCCESS (Real model inference verified)")
        return 0

    except Exception as exc:
        load_time_s = time.perf_counter() - start_load
        print(f"\n[REAL MODEL EXECUTION NOTICE]")
        print(f"Execution failed or halted after {load_time_s:.2f}s.")
        print(f"Error Type: {type(exc).__name__}")
        print(f"Details:    {exc}")
        print("\nDiagnostics:")
        print("1. If download failed, check network access or HF_TOKEN for Hugging Face Hub.")
        print("2. If out of memory, verify at least 8 GB of free system memory is available.")
        print("3. In accordance with project requirements, mock data is NOT substituted for the model.")
        print("Verification status: UNCONFIGURED_OR_DOWNLOAD_REQUIRED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
