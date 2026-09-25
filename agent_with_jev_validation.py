"""
Agent Integration with Jev Validator - Hybrid Approach
Combines Middleware (mandatory) + Skill (explicit reasoning)
"""

import json
import anthropic
from typing import Dict, Any, Optional, List
from jev_validator import JevValidator, ToolCall, ValidationLevel


class JevValidationSkill:
    """Jev validation as a callable skill for agents"""

    def __init__(self, validator: JevValidator):
        self.validator = validator

    def validate(self, tool_name: str, parameters: Dict, reason: str = "") -> Dict[str, Any]:
        """
        Skill: Validate a tool call

        Agent can call this when it wants to explicitly reason about safety
        """
        tool_call = ToolCall(
            tool_name=tool_name,
            parameters=parameters,
            context=reason
        )

        validation = self.validator.validate_tool_call(tool_call)

        return {
            "tool": tool_name,
            "validation_level": validation.validation_level.value,
            "safe": validation.is_safe,
            "appropriate": validation.is_appropriate,
            "confidence": validation.confidence,
            "reasoning": validation.reasoning,
            "approved": validation.validation_level == ValidationLevel.APPROVED,
            "rejected": validation.validation_level == ValidationLevel.REJECTED
        }

    def get_tool_definition(self) -> Dict[str, Any]:
        """Get the tool definition for Claude"""
        return {
            "name": "validate_tool_call",
            "description": "Validate if a tool call is safe to execute. Use this before executing risky operations like deletes, updates, or permission changes.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "tool_name": {
                        "type": "string",
                        "description": "Name of the tool you want to validate (e.g., 'delete_records', 'send_email')"
                    },
                    "parameters": {
                        "type": "object",
                        "description": "The parameters you would pass to the tool"
                    },
                    "reason": {
                        "type": "string",
                        "description": "Why you're considering this action (provide context)"
                    }
                },
                "required": ["tool_name", "parameters"]
            }
        }


class ValidatedAgent:
    """
    Agent with integrated Jev validation (Hybrid: Middleware + Skill)

    This approach:
    1. Adds validate_tool_call as a skill agent can use
    2. Also validates all tool calls via middleware
    3. Agent can reason explicitly about risky operations
    4. All operations are validated regardless
    """

    def __init__(
        self,
        client: anthropic.Anthropic,
        tools: List[Dict],
        validator: Optional[JevValidator] = None,
        strict_mode: bool = False
    ):
        """
        Initialize validated agent

        Args:
            client: Anthropic client
            tools: List of tool definitions for the agent
            validator: JevValidator instance (creates new if None)
            strict_mode: If True, reject UNCERTAIN validations
        """
        self.client = client
        self.validator = validator or JevValidator()
        self.strict_mode = strict_mode
        self.audit_log = []

        # Add Jev validation skill
        self.validation_skill = JevValidationSkill(self.validator)
        self.tools = tools + [self.validation_skill.get_tool_definition()]

    def run(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_iterations: int = 10
    ) -> Dict[str, Any]:
        """
        Run agent with Jev validation

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            max_iterations: Max tool call iterations

        Returns:
            Final response with audit log
        """

        if system_prompt is None:
            system_prompt = self._get_default_system_prompt()

        messages = [{"role": "user", "content": prompt}]

        for iteration in range(max_iterations):
            # Get response from Claude
            response = self.client.messages.create(
                model="claude-opus-5-5",
                max_tokens=2048,
                system=system_prompt,
                tools=self.tools,
                messages=messages
            )

            # Check if we're done
            if response.stop_reason == "end_turn":
                final_text = ""
                for block in response.content:
                    if hasattr(block, "text"):
                        final_text = block.text
                        break

                return {
                    "status": "success",
                    "response": final_text,
                    "iterations": iteration + 1,
                    "audit_log": self.audit_log
                }

            # Process tool calls
            tool_results = []
            has_tool_calls = False

            for block in response.content:
                if block.type == "tool_use":
                    has_tool_calls = True
                    tool_result = self._handle_tool_call(block)
                    tool_results.append(tool_result)

            if not has_tool_calls:
                # No tool calls but not end_turn
                continue

            # Add response to messages
            messages.append({"role": "assistant", "content": response.content})

            # Add tool results
            messages.append({
                "role": "user",
                "content": tool_results
            })

        return {
            "status": "max_iterations_reached",
            "iterations": max_iterations,
            "audit_log": self.audit_log
        }

    def _handle_tool_call(self, tool_use) -> Dict[str, Any]:
        """
        Handle a tool call with middleware validation

        Middleware: Always validate before execution
        """

        tool_name = tool_use.name
        tool_input = tool_use.input

        # Special handling for validation skill
        if tool_name == "validate_tool_call":
            # Agent is explicitly requesting validation
            result = self.validation_skill.validate(
                tool_input.get("tool_name", ""),
                tool_input.get("parameters", {}),
                tool_input.get("reason", "")
            )

            self._log_action(
                type="skill_call",
                tool=tool_name,
                input=tool_input,
                result=result
            )

            return {
                "type": "tool_result",
                "tool_use_id": tool_use.id,
                "content": json.dumps(result)
            }

        # Middleware: Validate all other tool calls
        validation = self.validator.validate_tool_call(
            ToolCall(
                tool_name=tool_name,
                parameters=tool_input,
                context="Agent tool call"
            )
        )

        self._log_action(
            type="tool_call",
            tool=tool_name,
            input=tool_input,
            validation=validation
        )

        # Decide whether to allow execution
        if validation.validation_level == ValidationLevel.REJECTED:
            error_msg = f"Tool blocked by validator: {validation.reasoning}"
            return {
                "type": "tool_result",
                "tool_use_id": tool_use.id,
                "content": json.dumps({"error": error_msg, "blocked": True}),
                "is_error": True
            }

        elif validation.validation_level == ValidationLevel.UNCERTAIN and self.strict_mode:
            error_msg = f"Tool uncertain in strict mode: {validation.reasoning}"
            return {
                "type": "tool_result",
                "tool_use_id": tool_use.id,
                "content": json.dumps({"error": error_msg, "uncertain": True}),
                "is_error": True
            }

        # Execute tool (in real scenario, call actual tool)
        # For this example, we simulate execution
        tool_result = self._simulate_tool_execution(tool_name, tool_input)

        return {
            "type": "tool_result",
            "tool_use_id": tool_use.id,
            "content": json.dumps(tool_result)
        }

    def _simulate_tool_execution(self, tool_name: str, parameters: Dict) -> Dict:
        """Simulate tool execution"""
        return {
            "status": "executed",
            "tool": tool_name,
            "message": f"Tool {tool_name} executed successfully (simulated)"
        }

    def _log_action(self, type: str, tool: str, input: Dict, **kwargs):
        """Log action for audit trail"""
        log_entry = {
            "type": type,
            "tool": tool,
            "input": str(input)[:100],  # Truncate for log
        }

        if "result" in kwargs:
            log_entry["result"] = kwargs["result"]

        if "validation" in kwargs:
            validation = kwargs["validation"]
            log_entry["validation"] = {
                "status": validation.validation_level.value,
                "safe": validation.is_safe,
                "confident": validation.confidence
            }

        self.audit_log.append(log_entry)

    def _get_default_system_prompt(self) -> str:
        return """You are a helpful agent that can execute tools safely.

IMPORTANT: Before executing any risky operations (delete, modify, create, permission changes):
1. Use the validate_tool_call tool to check if it's safe
2. Explain your reasoning
3. Only execute if validation approves it

Safety Guidelines:
- ALWAYS validate delete operations
- ALWAYS validate permission/access changes
- ALWAYS validate external communications (email, notifications)
- ALWAYS validate financial transactions
- Safe to skip validation for: read-only queries, information requests

Use validate_tool_call when uncertain about safety of any operation."""


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*70)
    print("AGENT WITH JEV VALIDATION - HYBRID APPROACH")
    print("="*70)

    # Initialize
    client = anthropic.Anthropic()
    validator = JevValidator()

    # Define some tools for the agent
    tools = [
        {
            "name": "search_database",
            "description": "Search the database for records",
            "input_schema": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"}
                },
                "required": ["query"]
            }
        },
        {
            "name": "delete_records",
            "description": "Delete records from database",
            "input_schema": {
                "type": "object",
                "properties": {
                    "table": {"type": "string"},
                    "condition": {"type": "string"}
                },
                "required": ["table", "condition"]
            }
        },
        {
            "name": "send_email",
            "description": "Send an email",
            "input_schema": {
                "type": "object",
                "properties": {
                    "to": {"type": "string"},
                    "subject": {"type": "string"},
                    "body": {"type": "string"}
                },
                "required": ["to", "subject", "body"]
            }
        }
    ]

    # Create validated agent
    agent = ValidatedAgent(
        client=client,
        tools=tools,
        validator=validator,
        strict_mode=False  # Allow uncertain operations with warning
    )

    # Example prompts
    prompts = [
        "Search for all users named John and tell me how many there are.",
        "Delete all inactive users from the database. Think about whether this is safe first.",
        "Send a confirmation email to customer@example.com about their order."
    ]

    for i, prompt in enumerate(prompts, 1):
        print(f"\n{'='*70}")
        print(f"Example {i}: {prompt[:50]}...")
        print("="*70)

        try:
            result = agent.run(
                prompt=prompt,
                max_iterations=5
            )

            print(f"\n✅ Status: {result['status']}")
            print(f"📊 Iterations: {result['iterations']}")

            if result["status"] == "success":
                print(f"\n📝 Response (first 200 chars):")
                print(result["response"][:200])

            print(f"\n📋 Audit Trail ({len(result['audit_log'])} actions):")
            for j, action in enumerate(result["audit_log"], 1):
                print(f"   {j}. {action['type']}: {action['tool']}")
                if "validation" in action:
                    print(f"      Validation: {action['validation']['status']}")

        except Exception as e:
            print(f"❌ Error: {str(e)[:100]}")

    print("\n" + "="*70)
    print("✨ Agent with Jev Validation - Complete!")
    print("="*70)
