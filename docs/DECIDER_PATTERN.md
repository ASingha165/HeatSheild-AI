# Confidence-Aware Tool Selection for Environmental Agents

**Pattern Name:** `Confidence-Aware Tool Selection for Environmental Agents`  
**Model:** Strands Decider 2B (`StrandsAgents/strands-decider-2B-hobson-v21` or `strands-decider-2B-qwen3.5-v1-2610`)  
**Package:** `strands-decider` (System One API)  
**Author:** HeatShield AI Engineering Team

---

## 1. Overview

Traditional generative Large Language Models (LLMs) used for tool routing rely on autoregressive token generation. This causes high latency (500ms - 3000ms), high inference token costs, non-deterministic formatting failures, and uncalibrated hallucinations when selecting tools under high uncertainty.

The **Confidence-Aware Tool Selection** pattern solves this by using **Strands Decider 2B**—a specialized 2B parameter decision model with a pointer readout head. It performs a single causal forward pass across discrete action candidates, returning:
1. An argmax action choice.
2. A strict probability distribution over all allowed actions.
3. An analytical, calibrated confidence metric $C \in [0.0, 1.0]$.
4. Sub-second decision latency on standard hardware.

---

## 2. Core Specification

### A. Allowed Action Options

The decision domain consists of 5 mutually exclusive analytical tools:

| Action Name | Purpose | Decision Criteria |
| :--- | :--- | :--- |
| `ANALYZE_HEAT` | Microclimate Heat Risk | Analyze available temperature observations and explicitly identified heat-risk indicators. |
| `CHECK_VEGETATION` | Canopy & NDVI Analysis | Analyze available vegetation coverage and canopy deficit information. |
| `CHECK_EXPOSURE` | Vulnerable Populations | Evaluate indicators of human exposure such as nearby schools, crowded transit stops, and shaded public spaces. |
| `COMPARE_INTERVENTIONS` | Cooling Strategy Comparison | Compare tree planting, shade structures, cool roofs, and shaded pedestrian routes using transparent assumptions. |
| `REQUEST_MORE_DATA` | Uncertainty Resolution | Identify missing information and generate a structured clarification request when data is too sparse to evaluate. |

### B. Typed Question

The question asked to the pointer head is structured using the official `ChoiceQuestion` schema:

```python
from strands_decider.schema import ChoiceQuestion

question = ChoiceQuestion(
    type="choice",
    instructions=(
        "Given the current environmental report and available evidence, "
        "which single analytical action should the agent execute next?"
    ),
    criteria={
        "ANALYZE_HEAT": "Analyze available temperature observations and explicitly identified heat-risk indicators.",
        "CHECK_VEGETATION": "Analyze available vegetation coverage and canopy deficit information.",
        "CHECK_EXPOSURE": "Evaluate indicators of human exposure such as nearby schools, crowded transit stops, and shaded public spaces.",
        "COMPARE_INTERVENTIONS": "Compare tree planting, shade structures, cool roofs, and shaded pedestrian routes using transparent assumptions.",
        "REQUEST_MORE_DATA": "Identify missing information and generate a structured clarification request when data is too sparse to evaluate.",
    }
)
```

### C. State Preparation

The state is formatted deterministically to highlight evidence and missing parameters:

```python
state = {
    "report": "The neighborhood has high afternoon temperatures, low vegetation coverage, and a crowded bus stop.",
    "location": "Downtown transit corridor",
    "temperature_observations": "Reported extreme heat; sensor data pending.",
    "vegetation_indicators": "Low tree canopy reported.",
    "exposure_indicators": "Crowded public transit shelter with unshaded waiting queue.",
    "missing_information": [
        "Exact ambient temperature (°C/°F)",
        "Quantitative canopy percentage"
    ],
    "available_tools": [
        "ANALYZE_HEAT",
        "CHECK_VEGETATION",
        "CHECK_EXPOSURE",
        "COMPARE_INTERVENTIONS",
        "REQUEST_MORE_DATA"
    ]
}
```

---

## 3. Normalized Application Schema

The pattern maps the model's raw output into a strict application schema:

```json
{
  "decision": "CHECK_EXPOSURE",
  "confidence": 0.8742,
  "decision_pattern": "confidence-aware-tool-selection",
  "latency_ms": 115.4,
  "status": "accepted",
  "probabilities": {
    "ANALYZE_HEAT": 0.0512,
    "CHECK_VEGETATION": 0.0421,
    "CHECK_EXPOSURE": 0.8845,
    "COMPARE_INTERVENTIONS": 0.0101,
    "REQUEST_MORE_DATA": 0.0121
  },
  "selected_option_valid": true,
  "confidence_threshold": 0.60,
  "is_above_threshold": true,
  "execution_gate": "PROCEED_TO_TOOL",
  "clarification_prompt": null,
  "state_summary": { ... }
}
```

---

## 4. Confidence Gating & Safety Invariants

### Invariant 1: Action Validation
The model's choice is strictly checked against the predefined set of allowed keys. If an unknown action is emitted, `execution_gate` becomes `REJECT_INVALID_CHOICE` and tool execution is blocked.

### Invariant 2: Calibrated Confidence Gate
Confidence is calculated by Strands Decider using the normalized max-probability formula:
$$C = \frac{N \cdot p_{\max} - 1}{N - 1}$$
Where $N = 5$ options.

* When $p_{\max} = 0.20$ (uniform spread across 5 choices), $C = 0.0$.
* When $p_{\max} = 1.00$ (one-hot certainty), $C = 1.0$.

When $C < \text{threshold}$ (default `0.60`):
1. **Tool dispatch is halted.**
2. `status` is set to `requires_clarification`.
3. `execution_gate` is set to `REQUEST_HUMAN_CLARIFICATION`.
4. A structured clarification prompt is generated detailing the ambiguity and competing options.

---

## 5. Standalone Usage Example

```python
from backend.patterns.tool_selection import (
    ConfidenceAwareToolSelector,
    EnvironmentalStateBuilder,
    ExecutionGate,
)

# 1. Initialize pattern with configurable threshold
selector = ConfidenceAwareToolSelector(
    checkpoint="StrandsAgents/strands-decider-2B-hobson-v21",
    device="cpu",
    confidence_threshold=0.60,
)

# 2. Build structured environmental state
state = EnvironmentalStateBuilder.build_state(
    report="Dense senior community center near arterial road with 38°C heat advisory and no tree canopy.",
    location="Oakwood District",
    temperature_observations="38°C heat advisory issued by regional weather bureau.",
    exposure_indicators="High concentration of elderly residents.",
)

# 3. Execute decision
decision = selector.select_action(state)

print(f"Action:     {decision.decision}")
print(f"Confidence: {decision.confidence:.4f}")
print(f"Gate:       {decision.execution_gate}")

# 4. Enforce execution gate
if decision.execution_gate == ExecutionGate.PROCEED_TO_TOOL:
    print(f"Dispatching tool: {decision.decision}...")
else:
    print(f"Execution halted. Clarification: {decision.clarification_prompt}")
```

---

## 6. Adapting the Pattern to Another Agent

To adapt this pattern to any other agent (e.g., Financial Fraud Router, Customer Support Triager, Medical Triage):

1. **Subclass or update `AnalyticalAction`**: Replace the 5 environmental actions with your agent's domain actions.
2. **Define `ACTION_CRITERIA`**: Provide crisp 1-2 sentence discriminator criteria for each choice.
3. **Format the state via your StateBuilder**: Ensure the state includes raw user input, available evidence, and explicit missing parameters.
4. **Tune `confidence_threshold`**:
   - `0.50` - Permissive: dispatches tools unless model is genuinely confused.
   - `0.65` - Balanced: recommended for municipal decision making.
   - `0.80` - High-assurance: requires clear evidence before autonomous action.
