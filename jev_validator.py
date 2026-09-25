"""
Jev Validator - Verification layer for OpenClaw tool calls and decisions
Uses Jev's structured decision-making to validate tool calls and decisions
"""

import os
import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum
import httpx
from dotenv import load_dotenv

load_dotenv()


class ValidationLevel(Enum):
    APPROVED = "approved"
    UNCERTAIN = "uncertain"
    REJECTED = "rejected"


@dataclass
class ToolCall:
    tool_name: str
    parameters: Dict[str, Any]
    context: Optional[str] = None


@dataclass
class ValidationResult:
    tool_name: str
    validation_level: ValidationLevel
    is_safe: bool
    is_appropriate: bool
    confidence: float
    reasoning: str
    jev_decision: Dict[str, Any]


class JevValidator:
    """Validates OpenClaw tool calls and decisions using Jev"""

    def __init__(self):
        """Initialize the Jev validator"""
        self.openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
        if not self.openrouter_api_key:
            raise ValueError("OPENROUTER_API_KEY environment variable not set")

        self.model_id = "typesafe/jev-1.13"

    def validate_tool_call(self, tool_call: ToolCall) -> ValidationResult:
        """Validate a single tool call"""
        # Create structured validation task
        payload = {
            "model": self.model_id,
            "state": {
                "tool_name": tool_call.tool_name,
                "parameters": json.dumps(tool_call.parameters, indent=2),
                "context": tool_call.context or "No additional context provided"
            },
            "questions": {
                "is_safe": {
                    "type": "noul",
                    "instructions": "Is this tool call safe to execute?",
                    "criteria": {
                        "true": "The tool call won't cause harm, data loss, or security issues.",
                        "false": "The tool call could cause harm, data loss, or security issues."
                    }
                },
                "is_appropriate": {
                    "type": "noul",
                    "instructions": "Is this tool call appropriate for the given context?",
                    "criteria": {
                        "true": "The tool call is a reasonable choice given the context.",
                        "false": "The tool call is inappropriate or unnecessary for the context."
                    }
                },
                "confidence": {
                    "type": "score",
                    "instructions": "How confident are you in this validation?",
                    "criteria": [
                        "Low confidence - multiple interpretations possible",
                        "Moderate confidence - some ambiguity",
                        "High confidence - clear validation"
                    ]
                },
                "risk_level": {
                    "type": "choice",
                    "instructions": "What is the risk level of this tool call?",
                    "criteria": {
                        "low": "Tool call has minimal risk",
                        "medium": "Tool call has moderate risk",
                        "high": "Tool call has significant risk"
                    }
                }
            }
        }

        # Call Jev
        headers = {
            "Authorization": f"Bearer {self.openrouter_api_key}",
            "Content-Type": "application/json",
        }

        response = httpx.post(
            "https://openrouter.ai/api/alpha/decisions",
            headers=headers,
            json=payload,
            timeout=60.0
        )

        if response.status_code != 200:
            raise ValueError(f"Jev API error ({response.status_code}): {response.text}")

        jev_response = response.json()
        decisions = jev_response.get("answers", {})

        # Parse Jev's decisions
        is_safe = decisions.get("is_safe", {}).get("noul", 0) > 0.5
        is_appropriate = decisions.get("is_appropriate", {}).get("noul", 0) > 0.5
        confidence_score = decisions.get("confidence", {}).get("score", 1) / 2.0  # Normalize to 0-1
        risk_level = decisions.get("risk_level", {}).get("choice", "medium")

        # Determine validation level
        if risk_level == "high":
            validation_level = ValidationLevel.REJECTED
        elif not is_safe or not is_appropriate:
            validation_level = ValidationLevel.UNCERTAIN
        else:
            validation_level = ValidationLevel.APPROVED

        # Build reasoning
        reasoning = self._build_reasoning(is_safe, is_appropriate, risk_level, confidence_score)

        return ValidationResult(
            tool_name=tool_call.tool_name,
            validation_level=validation_level,
            is_safe=is_safe,
            is_appropriate=is_appropriate,
            confidence=confidence_score,
            reasoning=reasoning,
            jev_decision=decisions
        )

    def validate_decision(self, decision_context: str, decision_made: str, alternatives: Optional[List[str]] = None) -> ValidationResult:
        """Validate a high-level decision"""
        alt_text = "\n".join([f"  - {alt}" for alt in (alternatives or [])])

        payload = {
            "model": self.model_id,
            "state": {
                "context": decision_context,
                "decision_made": decision_made,
                "alternatives": alt_text or "None provided"
            },
            "questions": {
                "is_sound": {
                    "type": "noul",
                    "instructions": "Is this decision logically sound?",
                    "criteria": {
                        "true": "The decision follows logically from the context",
                        "false": "The decision doesn't follow logically"
                    }
                },
                "is_optimal": {
                    "type": "noul",
                    "instructions": "Is this the best decision given the alternatives?",
                    "criteria": {
                        "true": "This is the optimal or near-optimal choice",
                        "false": "A better alternative exists"
                    }
                },
                "confidence": {
                    "type": "score",
                    "instructions": "How confident are you in this validation?",
                    "criteria": [
                        "Low confidence",
                        "Moderate confidence",
                        "High confidence"
                    ]
                },
                "recommendation": {
                    "type": "choice",
                    "instructions": "What is your recommendation?",
                    "criteria": {
                        "approve": "Decision should be approved",
                        "review": "Decision should be reviewed further",
                        "reject": "Decision should be rejected"
                    }
                }
            }
        }

        headers = {
            "Authorization": f"Bearer {self.openrouter_api_key}",
            "Content-Type": "application/json",
        }

        response = httpx.post(
            "https://openrouter.ai/api/alpha/decisions",
            headers=headers,
            json=payload,
            timeout=60.0
        )

        if response.status_code != 200:
            raise ValueError(f"Jev API error ({response.status_code}): {response.text}")

        jev_response = response.json()
        decisions = jev_response.get("answers", {})

        # Parse decisions
        is_sound = decisions.get("is_sound", {}).get("noul", 0) > 0.5
        is_optimal = decisions.get("is_optimal", {}).get("noul", 0) > 0.5
        recommendation = decisions.get("recommendation", {}).get("choice", "review")
        confidence_score = decisions.get("confidence", {}).get("score", 1) / 2.0

        # Determine validation level
        validation_map = {
            "approve": ValidationLevel.APPROVED,
            "review": ValidationLevel.UNCERTAIN,
            "reject": ValidationLevel.REJECTED
        }
        validation_level = validation_map.get(recommendation, ValidationLevel.UNCERTAIN)

        reasoning = f"Decision is {'sound' if is_sound else 'not sound'}. {'Optimal choice.' if is_optimal else 'Better alternatives may exist.'} Recommendation: {recommendation}."

        return ValidationResult(
            tool_name="decision",
            validation_level=validation_level,
            is_safe=is_sound,
            is_appropriate=is_optimal,
            confidence=confidence_score,
            reasoning=reasoning,
            jev_decision=decisions
        )

    def _build_reasoning(self, is_safe: bool, is_appropriate: bool, risk_level: str, confidence: float) -> str:
        """Build human-readable reasoning"""
        parts = []

        if is_safe:
            parts.append("Tool call is safe to execute.")
        else:
            parts.append("Tool call may not be safe.")

        if is_appropriate:
            parts.append("Tool choice is appropriate for the context.")
        else:
            parts.append("Tool choice may be inappropriate.")

        risk_text = {
            "low": "Low risk operation.",
            "medium": "Moderate risk operation.",
            "high": "High risk operation - review recommended."
        }
        parts.append(risk_text.get(risk_level, "Risk level unclear."))

        parts.append(f"Confidence: {confidence:.0%}")

        return " ".join(parts)


# Example usage
if __name__ == "__main__":
    validator = JevValidator()

    # Test tool call validation
    print("="*60)
    print("TOOL CALL VALIDATION EXAMPLES")
    print("="*60)

    # Example 1: Safe tool call
    tool_call_1 = ToolCall(
        tool_name="search_database",
        parameters={"query": "customer_name='John'", "table": "users"},
        context="User requested customer information lookup"
    )

    result_1 = validator.validate_tool_call(tool_call_1)
    print(f"\n✅ Tool: {result_1.tool_name}")
    print(f"   Status: {result_1.validation_level.value}")
    print(f"   Safe: {result_1.is_safe}, Appropriate: {result_1.is_appropriate}")
    print(f"   Confidence: {result_1.confidence:.0%}")
    print(f"   Reasoning: {result_1.reasoning}")

    # Example 2: Potentially dangerous tool call
    tool_call_2 = ToolCall(
        tool_name="delete_database_records",
        parameters={"table": "users", "condition": "1=1"},
        context="User asked to clean up old data"
    )

    result_2 = validator.validate_tool_call(tool_call_2)
    print(f"\n⚠️  Tool: {result_2.tool_name}")
    print(f"   Status: {result_2.validation_level.value}")
    print(f"   Safe: {result_2.is_safe}, Appropriate: {result_2.is_appropriate}")
    print(f"   Confidence: {result_2.confidence:.0%}")
    print(f"   Reasoning: {result_2.reasoning}")

    # Example 3: Decision validation
    print("\n" + "="*60)
    print("DECISION VALIDATION EXAMPLES")
    print("="*60)

    result_3 = validator.validate_decision(
        decision_context="User asked to send an email to all customers about a product update",
        decision_made="Send email to all customers",
        alternatives=["Send email to opted-in customers only", "Post on company blog instead"]
    )

    print(f"\n📋 Decision: Send email")
    print(f"   Status: {result_3.validation_level.value}")
    print(f"   Confidence: {result_3.confidence:.0%}")
    print(f"   Reasoning: {result_3.reasoning}")
