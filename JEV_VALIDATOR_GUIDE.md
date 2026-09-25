# Jev Validator - OpenClaw Verification System

A verification layer for OpenClaw that uses Jev to validate tool calls and decisions before execution.

## Overview

The Jev Validator acts as a gatekeeper for OpenClaw operations by:

1. **Intercepting tool calls** — Before OpenClaw executes any tool
2. **Analyzing decisions** — Before OpenClaw commits to major decisions
3. **Returning validation results** — APPROVED, UNCERTAIN, or REJECTED
4. **Providing confidence scores** — How certain Jev is in its assessment

## Architecture

```
OpenClaw → [Tool Call/Decision] → Jev Validator → [Validation Result] → Execute or Block
```

## Key Features

### ✅ Tool Call Validation
- Checks if tool is safe to execute
- Verifies appropriateness for the context
- Assesses risk level (low/medium/high)
- Returns confidence scores

### 📋 Decision Validation
- Validates high-level decisions
- Compares against alternatives
- Recommends: approve, review, or reject
- Provides soundness assessment

### 🎯 Validation Levels

| Level | Meaning | Action |
|-------|---------|--------|
| **APPROVED** | Safe and appropriate | Execute immediately |
| **UNCERTAIN** | Some concerns exist | Flag for review or log |
| **REJECTED** | High risk detected | Block execution, alert user |

## Installation

```bash
# Files already created:
# - jev_validator.py          (Main validator class)
# - test_jev_validator.py     (Test harness with examples)
```

## Quick Start

### Basic Tool Call Validation

```python
from jev_validator import JevValidator, ToolCall

validator = JevValidator()

# Create a tool call
tool_call = ToolCall(
    tool_name="send_email",
    parameters={
        "to": "user@example.com",
        "subject": "Hello",
        "body": "Test message"
    },
    context="Automated notification email"
)

# Validate
result = validator.validate_tool_call(tool_call)

# Check result
if result.validation_level.value == "approved":
    # Execute the tool
    execute_tool(tool_call)
elif result.validation_level.value == "uncertain":
    # Log and ask for confirmation
    log_uncertain_action(result)
else:
    # Reject and alert
    alert_user(f"Tool call blocked: {result.reasoning}")
```

### Decision Validation

```python
# Validate a decision
result = validator.validate_decision(
    decision_context="Customer refund request for 60-day-old purchase",
    decision_made="Grant full refund",
    alternatives=[
        "Deny refund",
        "Offer store credit",
        "Partial refund"
    ]
)

# Act on result
if result.validation_level.value == "approved":
    proceed_with_decision()
elif result.validation_level.value == "uncertain":
    escalate_for_review()
else:
    reconsider_alternatives()
```

## Integration with OpenClaw

### 1. Middleware Approach

Wrap OpenClaw's tool execution:

```python
class ValidatedOpenClaw:
    def __init__(self, openclaw_instance):
        self.openclaw = openclaw_instance
        self.validator = JevValidator()
    
    def execute_tool(self, tool_name, parameters, context):
        """Execute tool with Jev validation"""
        tool_call = ToolCall(
            tool_name=tool_name,
            parameters=parameters,
            context=context
        )
        
        result = self.validator.validate_tool_call(tool_call)
        
        if result.validation_level.value == "approved":
            return self.openclaw.execute(tool_name, parameters)
        elif result.validation_level.value == "uncertain":
            # Log with warning
            log_warning(f"Uncertain validation: {result.reasoning}")
            return self.openclaw.execute(tool_name, parameters)
        else:
            raise ValueError(f"Tool blocked by validator: {result.reasoning}")
```

### 2. Hook Approach

Register Jev as a pre-execution hook:

```python
openclaw.register_hook("pre_tool_execute", validate_with_jev)

def validate_with_jev(tool_name, parameters, context):
    """Hook that runs before tool execution"""
    validator = JevValidator()
    tool_call = ToolCall(tool_name, parameters, context)
    result = validator.validate_tool_call(tool_call)
    
    if result.validation_level.value == "rejected":
        raise SecurityError(result.reasoning)
    
    return True  # Allow execution
```

### 3. Logging Approach

Log all validations for audit:

```python
import json
from datetime import datetime

def log_validation(result, tool_name, parameters):
    """Log validation result for audit trail"""
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "tool": tool_name,
        "status": result.validation_level.value,
        "safe": result.is_safe,
        "appropriate": result.is_appropriate,
        "confidence": result.confidence,
        "reasoning": result.reasoning,
        "jev_details": result.jev_decision
    }
    
    # Write to audit log
    with open("jev_audit.jsonl", "a") as f:
        f.write(json.dumps(log_entry) + "\n")
```

## Validation Results

### Tool Call Example

```json
{
  "tool_name": "delete_records",
  "validation_level": "rejected",
  "is_safe": false,
  "is_appropriate": false,
  "confidence": 0.52,
  "reasoning": "Tool call may not be safe. Tool choice may be inappropriate. High risk operation - review recommended. Confidence: 52%",
  "jev_decision": {
    "is_safe": {"noul": 0.2, ...},
    "is_appropriate": {"noul": 0.1, ...},
    "confidence": {"score": 1.04, ...},
    "risk_level": {"choice": "high", ...}
  }
}
```

## Configuration

Customize validation rules by modifying `jev_validator.py`:

### Risk Level Mapping

```python
# In validate_tool_call method
validation_map = {
    "low": ValidationLevel.APPROVED,
    "medium": ValidationLevel.UNCERTAIN,
    "high": ValidationLevel.REJECTED
}
```

### Custom Validation Questions

Add more questions to Jev's decision framework:

```python
"questions": {
    "is_reversible": {
        "type": "noul",
        "instructions": "Can this action be reversed?",
        "criteria": {...}
    },
    "data_impact": {
        "type": "choice",
        "instructions": "Does this affect user data?",
        "criteria": {...}
    }
}
```

## Performance Metrics

From test runs:

| Metric | Value |
|--------|-------|
| Avg Validation Time | ~0.5s |
| Tool Validations | 3 approved, 2 rejected |
| Decision Validations | 1 approved, 1 uncertain, 1 rejected |
| Overall Safety Assessment | 38% marked safe |
| Confidence Scores | 45% average |

## Best Practices

1. **Always validate dangerous operations**
   - Delete/modify operations
   - Permission changes
   - External communications
   - Financial transactions

2. **Log all validations**
   - Create audit trail
   - Enable root cause analysis
   - Track validation patterns

3. **Handle uncertainty gracefully**
   - Don't auto-reject uncertain validations
   - Log for human review
   - Allow override with confirmation

4. **Tune confidence thresholds**
   - Start conservative (high confidence required)
   - Adjust based on false positive/negative rates
   - Monitor Jev's accuracy over time

5. **Combine with other checks**
   - Don't rely solely on Jev
   - Use in combination with traditional guardrails
   - Maintain human oversight for critical decisions

## Examples

See `test_jev_validator.py` for:
- ✅ Safe database queries
- ❌ Dangerous bulk deletes
- ✅ Safe email sending
- ❌ Risky permission updates
- ✅ Appropriate backups
- Decision validation examples

## Running Tests

```bash
# Run full validation test suite
python test_jev_validator.py

# Output includes:
# - Tool call validations (5 tests)
# - Decision validations (3 tests)
# - Summary statistics
# - System health metrics
```

## Troubleshooting

**Validator timing out?**
- Increase timeout in `jev_validator.py` (currently 60s)
- Check network connectivity to OpenRouter

**Validation results inconsistent?**
- Jev may need more context
- Add more details to `context` parameter
- Review Jev's decision breakdown in results

**False positives/negatives?**
- Adjust validation questions
- Modify risk criteria
- Tune confidence thresholds

## Next Steps

1. Integrate with your OpenClaw instance
2. Test with real tool calls
3. Monitor validation results
4. Tune thresholds based on feedback
5. Add custom validation rules for your domain
