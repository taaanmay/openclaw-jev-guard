# Jev Validator Integration Patterns for Agents

## Comparison of Integration Approaches

### 1. **Skill/Tool Approach** ⭐ For Flexible Validation

Agent explicitly calls Jev as a tool when needed.

**Pros:**
- Agent decides when validation is critical
- Can skip for simple operations
- No framework changes needed
- Easy to add/remove

**Cons:**
- Agent might forget to call it
- Adds extra latency to reasoning
- Not enforced on all operations

**Best for:** Agents that need flexibility, optional validation

```python
# Agent calls Jev as a skill/tool
Agent: "I want to delete all inactive users. Let me validate this first."
→ Tool: validate_with_jev(tool_name, parameters)
→ Jev: REJECTED - High risk
Agent: "I should reconsider this decision..."
```

---

### 2. **Middleware/Wrapper Approach** ⭐⭐ For Mandatory Safety

Intercept ALL tool calls at execution layer (cannot be bypassed).

**Pros:**
- Enforced on 100% of operations
- Transparent to agent
- Can't be skipped
- Works with any agent framework
- Best for production safety

**Cons:**
- Requires wrapping execution layer
- All operations pay validation latency
- Less flexible

**Best for:** Production systems, safety-critical applications, mandatory compliance

```python
# Agent doesn't know about validation
Agent: "Execute tool: delete_users"
→ [Middleware intercepts]
→ Jev: REJECTED
→ [Tool never executes]
→ Error returned to agent: "Tool blocked: High risk"
```

---

### 3. **Hook/Interceptor Approach** ⭐⭐ For Framework Integration

Register Jev as pre/post-execution hooks in agent framework.

**Pros:**
- Clean separation of concerns
- Automatic on every tool call
- Can log without blocking
- Framework-native approach

**Cons:**
- Requires hook infrastructure
- Hook ordering matters
- May vary by framework

**Best for:** Agents with hook systems (LangChain, LlamaIndex, etc.)

```python
# Framework calls hooks automatically
agent.before_tool_execute += validate_with_jev
agent.after_tool_execute += log_validation

# Agent doesn't know about validation
Agent: "Execute tool"
→ [Framework calls hooks]
→ Jev validates
→ [Tool executes or blocks]
```

---

### 4. **Structured Output Approach** ⭐ For Reasoning

Embed Jev validation into agent's tool schema and reasoning.

**Pros:**
- Agent reasons explicitly about safety
- Transparent decisions
- Good audit trail
- Agent can learn from validation

**Cons:**
- Adds steps to agent reasoning
- More latency
- Requires schema changes

**Best for:** Explainable AI, compliance-heavy workflows

```python
# Agent's reasoning includes validation
Agent: "To delete users, I should:
1. Understand what users to delete
2. Check if safe (call Jev)
3. Get confirmation (if uncertain)
4. Execute"
```

---

### 5. **Async Background Approach** For Performance

Validate in parallel while agent continues reasoning.

**Pros:**
- Non-blocking
- Fast agent response
- Can continue planning
- Validation happens in background

**Cons:**
- Validation might complete after execution
- Race conditions possible
- Complex error handling

**Best for:** High-throughput systems, non-critical validations

```python
# Validation happens async
Agent: "Execute tool X"
→ Start Jev validation (background)
→ Execute immediately (if threshold met)
→ Update if validation completes with concerns
```

---

## Recommendation Matrix

| Scenario | Approach | Reason |
|----------|----------|--------|
| **Claude/GPT Agents** | Skill + Middleware | Maximize safety, agents can reason about validation |
| **Production Systems** | Middleware | Enforce on everything, can't skip |
| **Safety-Critical** | Middleware + Skill | Defense in depth |
| **Research/Exploration** | Skill | Flexibility for experimentation |
| **LangChain Apps** | Hooks | Native framework integration |
| **High-Speed Apps** | Async + Middleware | Performance + safety |
| **Compliance Required** | Middleware + Structured | Audit trail essential |

---

## Best Practice: Layered Approach

**Combine multiple patterns for defense in depth:**

```
Agent Layer
    ↓
[Skill: validate_before_execute] ← Agent can use
    ↓
[Middleware: mandatory_validation] ← Can't skip
    ↓
[Hook: log_all_validations] ← Always audit
    ↓
Tool Execution
    ↓
[Hook: post_execution_logging]
    ↓
Audit Log
```

This provides:
1. **Agent-level reasoning** (via skill)
2. **Enforcement** (via middleware)
3. **Compliance** (via logging hooks)

---

## Implementation Guide

### Option A: Skill Approach (For Claude Agents)

```python
# Define as a tool the agent can call
tools = [
    {
        "name": "validate_tool_call",
        "description": "Validate if a tool call is safe before executing",
        "input_schema": {
            "type": "object",
            "properties": {
                "tool_name": {"type": "string"},
                "parameters": {"type": "object"},
                "reason": {"type": "string"}
            }
        }
    }
]

# Agent uses it
Agent: "I want to delete records. Let me validate first."
→ Call validate_tool_call("delete_records", {...})
→ Return validation result
Agent: "Decision made based on validation"
```

**Pros:** Explicit agent reasoning, can see decision process
**Cons:** Agent must remember to call it

---

### Option B: Middleware Approach (Recommended for Production)

```python
class ValidatedExecutor:
    """Wraps agent's tool executor"""
    
    def __init__(self, agent, validator):
        self.agent = agent
        self.validator = validator
    
    def execute_tool(self, tool_name, parameters):
        # Always validate first
        validation = self.validator.validate_tool_call(
            ToolCall(tool_name, parameters)
        )
        
        if validation.level == "rejected":
            raise ToolBlockedError(validation.reasoning)
        
        # Execute tool
        return self.agent.execute(tool_name, parameters)

# Use it
executor = ValidatedExecutor(agent, validator)
agent.tool_executor = executor  # Replace executor
```

**Pros:** Transparent, enforced, can't be bypassed
**Cons:** Requires modifying agent's execution layer

---

### Option C: Hook Approach (If Framework Supports)

```python
# For agents with hook system
agent.register_hook(
    "before_tool_execute",
    lambda tool, params: validator.validate_tool_call(
        ToolCall(tool, params)
    )
)

agent.register_hook(
    "after_tool_execute",
    lambda tool, result: log_validation(tool, result)
)
```

**Pros:** Clean, framework-native
**Cons:** Requires hook infrastructure

---

### Option D: Structured Output Approach

```python
# Agent reasons about safety as part of planning

system_prompt = """
Before executing any tool:
1. Think about what the tool does
2. Call validate_tool_call with the tool details
3. If validation is REJECTED, suggest an alternative
4. If APPROVED, execute the tool
5. If UNCERTAIN, ask for confirmation

Always validate risky operations (delete, modify, permission changes).
"""

# Agent reasons: 
# "I need to delete inactive users. Let me validate this..."
# → Calls validate_tool_call → Gets result → Decides next step
```

**Pros:** Transparent reasoning, good for audits
**Cons:** Extra reasoning overhead

---

## Framework-Specific Recommendations

### For Claude (Claude Code / Claude API)

**Recommended: Skill + Middleware Hybrid**

```python
# 1. Add as a tool (skill) agent can use
tools = [validate_tool_call_tool]

# 2. Also wrap tool executor
class ValidatedClaudeAgent:
    def __init__(self, client):
        self.client = client
        self.validator = JevValidator()
    
    def run(self, prompt):
        while True:
            response = self.client.messages.create(
                tools=tools,
                messages=messages
            )
            
            # Handle tool calls
            for tool_use in response.content:
                if tool_use.name == "validate_tool_call":
                    # Agent explicitly validating
                    validation = self.validator.validate_tool_call(...)
                    return validation_result
                else:
                    # Regular tool - also validate
                    validation = self.validator.validate_tool_call(...)
                    if validation.rejected:
                        return error(validation.reasoning)
                    result = execute_tool(tool_use)
```

### For LangChain

**Recommended: Hooks Approach**

```python
from langchain.callbacks import BaseCallbackHandler

class JevValidationCallback(BaseCallbackHandler):
    def on_tool_start(self, serialized, input_str, **kwargs):
        # Validate before tool execution
        validation = validator.validate_tool_call(...)
        if validation.rejected:
            raise ValueError(validation.reasoning)
    
    def on_tool_end(self, output, **kwargs):
        # Log after execution
        log_validation(output)

agent.callbacks = [JevValidationCallback()]
```

### For LlamaIndex

**Recommended: Tool Wrapper**

```python
from llama_index.tools import ToolMetadata

validated_tools = []
for tool in original_tools:
    validated_tool = wrap_with_validation(tool, validator)
    validated_tools.append(validated_tool)

agent = OpenAIAgent.from_tools(validated_tools)
```

---

## My Recommendation for Your Use Case

Based on building a validator for **OpenClaw**:

### **Best: Middleware + Skill Hybrid**

**Why:**
1. **Middleware** ensures 100% of operations are validated (can't be bypassed)
2. **Skill** allows agent to reason about validation explicitly
3. **Layered defense** is stronger than single approach

**Implementation:**

```python
class SmartValidatedAgent:
    def __init__(self, agent, validator):
        self.agent = agent
        self.validator = validator
        self.agent.tools.append(validate_tool_skill)
    
    def execute(self, prompt):
        # Agent can explicitly use validation skill
        # But all tools also go through middleware
        
        while not_done:
            # Agent reasons and calls tools
            response = self.agent.step(prompt)
            
            for tool_use in response.tool_calls:
                if tool_use.name == "validate_tool_call":
                    # Agent explicitly validating
                    validation = self.validator.validate_tool_call(...)
                    result = validation_result
                else:
                    # Middleware: mandatory validation
                    validation = self._validate_before_execute(tool_use)
                    if validation.rejected:
                        result = ErrorResult(validation.reasoning)
                    else:
                        result = self.agent.execute_tool(tool_use)
                
                prompt += f"Tool result: {result}"
```

**Benefits:**
- Agent can reason about safety explicitly (skill)
- All operations validated regardless (middleware)
- Can't be bypassed by agent
- Clear audit trail
- Scales to multiple agents

---

## Decision Tree

```
Do you need to prevent ALL operations from skipping validation?
├─ YES → Use Middleware (mandatory)
└─ NO → Can use Skill alone

Do you want agent to reason about validation?
├─ YES → Add Skill (agent decides when critical)
└─ NO → Middleware only

Is this for production/compliance?
├─ YES → Middleware + Skill + Logging
└─ NO → Skill only (flexible)

Do you have framework hooks?
├─ YES → Use Hooks (cleaner)
└─ NO → Use Middleware (more portable)
```

---

## Summary

| Approach | Strength | Use Case |
|----------|----------|----------|
| **Skill** | Flexible, agent-driven | Experimentation, optional validation |
| **Middleware** | Enforced, safe | Production, mandatory validation |
| **Hooks** | Clean, native | Frameworks with hook support |
| **Structured** | Transparent, audit | Compliance-heavy workflows |
| **Async** | Fast, non-blocking | High-throughput systems |
| **Hybrid** | Best of all | Production safety-critical apps |

**Recommendation: Use Hybrid (Middleware + Skill) for OpenClaw**
