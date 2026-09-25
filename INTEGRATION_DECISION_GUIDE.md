# Jev Validator Integration - Decision Guide

## Quick Answer

**For most agents (Claude, LLMs): Use the Hybrid Approach**

```python
agent = ValidatedAgent(client, tools, validator, strict_mode=False)
result = agent.run("Your prompt here")
```

This gives you:
- ✅ Agent can explicitly reason about safety (Skill)
- ✅ All operations validated automatically (Middleware)
- ✅ Can't be bypassed
- ✅ Full audit trail

---

## Option Comparison Matrix

| Feature | Skill Only | Middleware Only | Hybrid ⭐ | Hooks |
|---------|-----------|-----------------|--------|-------|
| **Agent decides when** | ✅ Yes | ❌ No | ✅ Yes | ❌ No |
| **Enforced on all ops** | ❌ No | ✅ Yes | ✅ Yes | ✅ Yes |
| **Can be bypassed** | ✅ Yes | ❌ No | ❌ No | ❌ No |
| **Reasoning visible** | ✅ Yes | ❌ No | ✅ Yes | ❌ No |
| **Audit trail** | ⚠️ If agent logs | ✅ Auto | ✅ Auto | ✅ Auto |
| **Setup complexity** | 🟢 Easy | 🟡 Medium | 🟡 Medium | 🟢 Easy |
| **Latency overhead** | 📊 Low | 📊 Medium | 📊 Medium | 📊 Low |
| **Best for** | Research | Production | Production Safe AI | Framework-native |

---

## Integration Paths by Use Case

### Use Case 1: Production System (Recommended)

**Goal:** Ensure safe operations, mandatory validation, compliance

**Approach:** Hybrid (Middleware + Skill)

```python
# Files to use:
# - agent_with_jev_validation.py
# - jev_validator.py

from agent_with_jev_validation import ValidatedAgent
from jev_validator import JevValidator

validator = JevValidator()
agent = ValidatedAgent(
    client=client,
    tools=your_tools,
    validator=validator,
    strict_mode=True  # Reject uncertain operations
)

result = agent.run("Your prompt")
# Validation happens automatically on all tool calls
# Agent can also explicitly validate risky ops
# Audit log tracks everything
```

**Benefits:**
- 100% of tool calls validated
- Agent can reason about safety
- Can't be skipped
- Full compliance trail

---

### Use Case 2: Research / Experimentation

**Goal:** Flexibility, optional validation

**Approach:** Skill Only

```python
# Add validation as a tool
tools = your_tools + [JevValidationSkill(validator).get_tool_definition()]

response = client.messages.create(
    model="claude-opus-5-5",
    tools=tools,
    system="Use validate_tool_call when you want to check if something is safe",
    messages=[{"role": "user", "content": prompt}]
)

# Agent decides when to validate
# More flexible, less overhead
```

**Benefits:**
- Agent decides what to validate
- Lower latency for simple ops
- Flexible, experimentation-friendly

---

### Use Case 3: Framework Integration (LangChain, etc.)

**Goal:** Native integration with existing framework

**Approach:** Hooks/Callbacks

```python
from langchain.callbacks import BaseCallbackHandler

class JevValidationCallback(BaseCallbackHandler):
    def on_tool_start(self, serialized, input_str, **kwargs):
        validation = validator.validate_tool_call(...)
        if validation.rejected:
            raise ValueError(validation.reasoning)

agent.callbacks = [JevValidationCallback()]
```

**Benefits:**
- Framework-native
- Clean separation
- Automatic integration

---

### Use Case 4: High-Speed / Real-Time

**Goal:** Fast response, validation in background

**Approach:** Async Validation

```python
# Validate in background, log results
async def validate_async(tool_call):
    validation = await validator.validate_tool_call_async(tool_call)
    if validation.rejected:
        log_warning(f"Post-execution validation failed: {validation.reasoning}")

# Execute first, validate second
result = execute_tool(tool_call)
asyncio.create_task(validate_async(tool_call))  # Background
```

**Benefits:**
- No latency impact
- Fast tool execution
- Validation for audit

---

## Implementation Guide by Framework

### Claude API / Claude Code

**Recommended: Hybrid Approach**

```python
# See: agent_with_jev_validation.py

from agent_with_jev_validation import ValidatedAgent

agent = ValidatedAgent(
    client=anthropic.Anthropic(),
    tools=[your_tools],
    validator=JevValidator()
)

result = agent.run(user_prompt)
```

**File:** `agent_with_jev_validation.py` (ready to use)

---

### LangChain

**Recommended: Hooks Approach**

```python
from langchain.callbacks import BaseCallbackHandler
from langchain.agents import AgentExecutor, create_react_agent

class JevCallback(BaseCallbackHandler):
    def __init__(self, validator):
        self.validator = validator
    
    def on_tool_start(self, serialized, input_str, **kwargs):
        tool_name = serialized["name"]
        params = json.loads(input_str)
        validation = self.validator.validate_tool_call(
            ToolCall(tool_name, params)
        )
        if validation.rejected:
            raise ValueError(validation.reasoning)

agent_executor = AgentExecutor.from_agent_and_tools(
    agent=create_react_agent(llm, tools),
    tools=tools,
    callbacks=[JevCallback(validator)]
)

result = agent_executor.invoke({"input": prompt})
```

---

### LlamaIndex

**Recommended: Tool Wrapper**

```python
from llama_index.agent import ReActAgent

def wrap_tool_with_validation(tool, validator):
    original_fn = tool.metadata.fn
    
    def validated_fn(*args, **kwargs):
        validation = validator.validate_tool_call(
            ToolCall(tool.metadata.name, {"args": args, "kwargs": kwargs})
        )
        if validation.rejected:
            raise ValueError(validation.reasoning)
        return original_fn(*args, **kwargs)
    
    tool.metadata.fn = validated_fn
    return tool

validated_tools = [wrap_tool_with_validation(t, validator) for t in tools]
agent = ReActAgent.from_tools(validated_tools)
```

---

### Custom Agent

**Recommended: Middleware Approach**

```python
class MyAgent:
    def __init__(self, validator):
        self.validator = validator
    
    def execute_tool(self, tool_name, params):
        # Middleware validation
        validation = self.validator.validate_tool_call(
            ToolCall(tool_name, params)
        )
        
        if validation.rejected:
            return {"error": validation.reasoning}
        
        # Execute
        return self._do_tool_execution(tool_name, params)
```

---

## Decision Tree

```
START: How will you use Jev validation?

1. Production system that can't skip validation?
   → Hybrid (Middleware + Skill) ⭐

2. Want framework-native integration?
   → Hooks/Callbacks

3. Need maximum flexibility & agent reasoning?
   → Skill Only

4. Building custom agent?
   → Middleware (wraps executor)

5. Need real-time performance?
   → Async Validation

6. Using LangChain/LlamaIndex?
   → Framework hooks/callbacks

7. Experimenting/learning?
   → Skill Only (flexible)
```

---

## My Top Recommendation

### For OpenClaw (Your Use Case)

Since you're building a verification layer for an agent system:

**Use: Hybrid Approach (Middleware + Skill)**

**Why:**
1. ✅ **Safety First** — All operations validated (middleware)
2. ✅ **Intelligence** — Agent reasons about validation (skill)
3. ✅ **Enforceable** — Can't be bypassed
4. ✅ **Transparent** — Full audit trail
5. ✅ **Scalable** — Works for multiple agents

**Implementation:**

```python
# 1. Use agent_with_jev_validation.py
from agent_with_jev_validation import ValidatedAgent
from jev_validator import JevValidator

# 2. Create validator
validator = JevValidator()

# 3. Define your tools
tools = [...]

# 4. Create validated agent
agent = ValidatedAgent(
    client=anthropic.Anthropic(),
    tools=tools,
    validator=validator,
    strict_mode=True  # Reject uncertain operations
)

# 5. Run with validation
result = agent.run(user_prompt)

# 6. Check audit log
for action in result["audit_log"]:
    print(f"Action: {action['tool']}, Status: {action.get('validation', {}).get('status')}")
```

**What Happens:**
1. User gives prompt to agent
2. Agent reasons about what to do
3. Agent can call `validate_tool_call` (explicit reasoning)
4. All tool calls validated by middleware (mandatory)
5. Operations allowed/blocked based on Jev
6. Everything logged for audit

---

## Quick Setup

### Option A: Just Add Skill (Minimal Setup)

```python
# Add to your existing agent
validation_skill = JevValidationSkill(validator)
tools.append(validation_skill.get_tool_definition())

# Agent can now call "validate_tool_call"
# Tell agent to use it for risky operations
```

**Time to implement:** 5 minutes
**Safety level:** Medium (agent must remember to validate)

---

### Option B: Use ValidatedAgent (Recommended)

```python
# Use our pre-built solution
from agent_with_jev_validation import ValidatedAgent

agent = ValidatedAgent(client, tools, validator)
result = agent.run(prompt)
```

**Time to implement:** 10 minutes
**Safety level:** High (automatic validation + agent reasoning)

---

### Option C: Wrap Your Existing Agent

```python
# Wrap your agent's tool executor
class ValidatingExecutor:
    def __init__(self, agent, validator):
        self.agent = agent
        self.validator = validator
    
    def execute(self, tool, params):
        v = self.validator.validate_tool_call(ToolCall(tool, params))
        if v.rejected:
            raise ValueError(v.reasoning)
        return self.agent.execute(tool, params)

agent.executor = ValidatingExecutor(agent, validator)
```

**Time to implement:** 15 minutes
**Safety level:** High (works with existing agent)

---

## Files Ready to Use

| File | Purpose | Status |
|------|---------|--------|
| `agent_with_jev_validation.py` | Ready-to-use hybrid agent | ✅ Production-ready |
| `jev_validator.py` | Core validator | ✅ Production-ready |
| `JEV_INTEGRATION_PATTERNS.md` | Integration reference | ✅ Complete |
| `openclaw_integration_example.py` | Integration examples | ✅ Tested |

---

## Next Steps

1. **Choose approach** (I recommend Hybrid)
2. **Copy relevant files** to your project
3. **Update imports** for your paths
4. **Test with sample prompts**
5. **Monitor audit log**
6. **Adjust confidence thresholds** as needed

---

## Summary

| Need | Solution | File |
|------|----------|------|
| Quick skill | `JevValidationSkill` | `jev_validator.py` |
| Full agent with validation | `ValidatedAgent` | `agent_with_jev_validation.py` |
| Integration patterns | Patterns guide | `JEV_INTEGRATION_PATTERNS.md` |
| Examples | Working examples | `openclaw_integration_example.py` |

**Start with:** `agent_with_jev_validation.py` (Hybrid approach)

---

**Your Jev Validator is ready to integrate! 🚀**
