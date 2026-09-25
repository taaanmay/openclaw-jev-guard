"""
Example: Integrating Jev Validator with OpenClaw

This shows how to use Jev as a verification layer for OpenClaw
"""

import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from jev_validator import JevValidator, ToolCall, ValidationLevel

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ValidatedOpenClaw:
    """
    Wrapper around OpenClaw that adds Jev validation.

    Usage:
        claw = ValidatedOpenClaw(your_openclaw_instance)
        result = claw.execute_tool("search_users", {"query": "admin"}, "User lookup")
    """

    def __init__(self, openclaw_instance, strict_mode=False):
        """
        Initialize validated OpenClaw wrapper

        Args:
            openclaw_instance: Your OpenClaw instance
            strict_mode: If True, reject UNCERTAIN validations. If False, allow with warning.
        """
        self.openclaw = openclaw_instance
        self.validator = JevValidator()
        self.strict_mode = strict_mode
        self.audit_log = []

    def execute_tool(
        self,
        tool_name: str,
        parameters: Dict[str, Any],
        context: Optional[str] = None,
        force_execute: bool = False
    ) -> Dict[str, Any]:
        """
        Execute a tool with Jev validation

        Args:
            tool_name: Name of the tool to execute
            parameters: Tool parameters
            context: Additional context for validation
            force_execute: Override validation (use with caution)

        Returns:
            Tool execution result
        """

        logger.info(f"🔍 Validating tool call: {tool_name}")

        # Create tool call for validation
        tool_call = ToolCall(
            tool_name=tool_name,
            parameters=parameters,
            context=context or ""
        )

        # Get validation from Jev
        try:
            validation = self.validator.validate_tool_call(tool_call)
        except Exception as e:
            logger.error(f"Validation error: {e}")
            validation = None

        # Log the validation
        self._log_validation(tool_name, parameters, validation, force_execute)

        # Decide whether to execute
        if force_execute:
            logger.warning(f"⚠️  Forcing execution despite validation result")
            return self._execute_without_validation(tool_name, parameters)

        if validation is None:
            logger.warning(f"⚠️  Validation failed, executing with caution")
            return self._execute_without_validation(tool_name, parameters)

        if validation.validation_level == ValidationLevel.APPROVED:
            logger.info(f"✅ Tool approved: {tool_name}")
            return self._execute_with_logging(tool_name, parameters)

        elif validation.validation_level == ValidationLevel.UNCERTAIN:
            if self.strict_mode:
                logger.error(f"❌ Uncertain validation in strict mode: {validation.reasoning}")
                raise ValueError(f"Tool blocked: {validation.reasoning}")
            else:
                logger.warning(f"⚠️  Uncertain validation: {validation.reasoning}")
                return self._execute_with_logging(tool_name, parameters, flag_uncertain=True)

        else:  # REJECTED
            logger.error(f"❌ Tool rejected: {validation.reasoning}")
            raise ValueError(f"Tool blocked by validator: {validation.reasoning}")

    def make_decision(
        self,
        decision_context: str,
        decision: str,
        alternatives: Optional[list] = None
    ) -> Dict[str, Any]:
        """
        Validate a high-level decision before committing

        Args:
            decision_context: Context for the decision
            decision: The decision being made
            alternatives: Alternative options considered

        Returns:
            Decision with validation result
        """

        logger.info(f"📋 Validating decision: {decision}")

        try:
            validation = self.validator.validate_decision(
                decision_context=decision_context,
                decision_made=decision,
                alternatives=alternatives
            )
        except Exception as e:
            logger.error(f"Decision validation error: {e}")
            return {"decision": decision, "validation_failed": True}

        # Log decision
        self._log_decision(decision, decision_context, validation)

        return {
            "decision": decision,
            "validation_level": validation.validation_level.value,
            "reasoning": validation.reasoning,
            "confidence": validation.confidence,
            "approved": validation.validation_level == ValidationLevel.APPROVED
        }

    def _execute_without_validation(self, tool_name: str, parameters: Dict) -> Any:
        """Execute tool without going through OpenClaw wrapper"""
        logger.info(f"Executing (unvalidated): {tool_name}")
        # In real scenario, call: return self.openclaw.execute(tool_name, parameters)
        return {"status": "executed", "tool": tool_name}

    def _execute_with_logging(
        self,
        tool_name: str,
        parameters: Dict,
        flag_uncertain: bool = False
    ) -> Any:
        """Execute tool and log the execution"""
        logger.info(f"Executing (validated): {tool_name}")

        # In real scenario: result = self.openclaw.execute(tool_name, parameters)
        result = {"status": "executed", "tool": tool_name}

        if flag_uncertain:
            logger.warning(f"⚠️  Executed with uncertain validation: {tool_name}")

        return result

    def _log_validation(self, tool_name, parameters, validation, force):
        """Log tool validation for audit trail"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "type": "tool_validation",
            "tool": tool_name,
            "parameters": str(parameters)[:100],  # Truncate for log
            "validation": {
                "status": validation.validation_level.value if validation else "error",
                "safe": validation.is_safe if validation else None,
                "appropriate": validation.is_appropriate if validation else None,
                "confidence": validation.confidence if validation else None,
                "reasoning": validation.reasoning if validation else "Validation failed"
            },
            "force_executed": force
        }
        self.audit_log.append(log_entry)

    def _log_decision(self, decision, context, validation):
        """Log decision validation for audit trail"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "type": "decision_validation",
            "decision": decision,
            "context": context[:100],
            "validation": {
                "status": validation.validation_level.value,
                "approved": validation.validation_level == ValidationLevel.APPROVED,
                "confidence": validation.confidence,
                "reasoning": validation.reasoning
            }
        }
        self.audit_log.append(log_entry)

    def get_audit_log(self) -> list:
        """Get the complete audit log"""
        return self.audit_log

    def save_audit_log(self, filename: str = "jev_audit.json"):
        """Save audit log to file"""
        with open(filename, 'w') as f:
            json.dump(self.audit_log, f, indent=2)
        logger.info(f"Audit log saved to {filename}")


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*70)
    print("OPENCLAW + JEV VALIDATOR INTEGRATION EXAMPLE")
    print("="*70)

    # Mock OpenClaw instance (replace with real one)
    class MockOpenClaw:
        def execute(self, tool_name, parameters):
            return {"result": "success"}

    openclaw = MockOpenClaw()

    # Create validated wrapper
    validated_claw = ValidatedOpenClaw(openclaw, strict_mode=False)

    print("\n📌 SCENARIO 1: Safe Database Query")
    print("-" * 70)
    try:
        result = validated_claw.execute_tool(
            tool_name="query_database",
            parameters={"query": "SELECT * FROM users WHERE id=5"},
            context="User requested customer profile"
        )
        print(f"✅ Result: {result}")
    except Exception as e:
        print(f"❌ Blocked: {e}")

    print("\n📌 SCENARIO 2: Risky Delete Operation")
    print("-" * 70)
    try:
        result = validated_claw.execute_tool(
            tool_name="delete_all_records",
            parameters={"table": "users", "condition": "WHERE 1=1"},
            context="User wants to clean database"
        )
        print(f"✅ Result: {result}")
    except Exception as e:
        print(f"❌ Blocked: {e}")

    print("\n📌 SCENARIO 3: Decision Validation")
    print("-" * 70)
    decision_result = validated_claw.make_decision(
        decision_context="User refund request for purchase made 30 days ago",
        decision="Grant full refund",
        alternatives=["Deny refund", "Offer store credit", "Partial refund"]
    )
    print(f"Decision: {decision_result['decision']}")
    print(f"Status: {decision_result['validation_level']}")
    print(f"Approved: {decision_result['approved']}")
    print(f"Reasoning: {decision_result['reasoning']}")

    print("\n📌 SCENARIO 4: Force Execute Dangerous Tool")
    print("-" * 70)
    try:
        result = validated_claw.execute_tool(
            tool_name="drop_database",
            parameters={"database": "production"},
            context="Emergency - must drop database",
            force_execute=True  # Override validation
        )
        print(f"⚠️  Force executed: {result}")
    except Exception as e:
        print(f"❌ Error: {e}")

    # Print audit log summary
    print("\n" + "="*70)
    print("AUDIT LOG SUMMARY")
    print("="*70)

    audit_log = validated_claw.get_audit_log()
    for i, entry in enumerate(audit_log, 1):
        entry_type = entry['type']
        if entry_type == "tool_validation":
            print(f"\n{i}. Tool: {entry['tool']}")
            print(f"   Status: {entry['validation']['status']}")
            print(f"   Safe: {entry['validation']['safe']}")
        else:
            print(f"\n{i}. Decision: {entry['decision']}")
            print(f"   Status: {entry['validation']['status']}")
            print(f"   Approved: {entry['validation']['approved']}")

    # Save audit log
    validated_claw.save_audit_log()

    print("\n✅ Integration example complete!")
