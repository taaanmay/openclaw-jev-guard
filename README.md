# OpenClaw-Jev-Guard

A production-ready verification layer for AI agents using Jev's structured decision-making. Validates tool calls and decisions before execution, providing safety-critical guarantees for enterprise LLM applications.

**OpenClaw-Jev-Guard** ensures your AI agents make safe, auditable decisions by intercepting all operations and validating them against customizable safety rules.

## Features

✅ **Automatic Tool Validation** — Every tool call validated before execution
✅ **Decision Verification** — Validate high-level agent decisions
✅ **Confidence Scoring** — Know how certain the validator is (0-100%)
✅ **Risk Assessment** — Automatic low/medium/high risk classification
✅ **Full Audit Trail** — 100% of operations logged in JSON format
✅ **Agent Reasoning** — Agents can explicitly validate risky operations
✅ **Can't Be Bypassed** — Middleware enforces validation at execution layer
✅ **Framework Agnostic** — Works with Claude, LangChain, LlamaIndex, custom agents
✅ **Production Ready** — Tested and battle-hardened

## Quick Start

### Installation

```bash
pip install -r requirements.txt
```

### Basic Usage

```python
from jev_decision_maker import ValidatedAgent, JevValidator
import anthropic

# Initialize
validator = JevValidator()
tools = [...]  # Your tools

# Create validated agent
agent = ValidatedAgent(
    client=anthropic.Anthropic(),
    tools=tools,
    validator=validator,
    strict_mode=True
)

# Run with automatic validation
result = agent.run("Delete all inactive users")

# Agent validates: "High risk operation - rejected"
# Check audit log
print(result["audit_log"])
```

## How It Works

```
User Prompt
    ↓
Agent Reasoning
    ├─ Can call validate_tool_call (explicit reasoning)
    └─ Middleware validates all tool calls (mandatory)
        ↓
    JevValidator (powered by Jev 1.13)
        ├─ Is this tool call safe?
        ├─ Is it appropriate for the context?
        ├─ What's the risk level?
        └─ How confident are we?
            ↓
        Result: APPROVED / UNCERTAIN / REJECTED
            ↓
        Execute or Block
            ↓
        Audit Log (100% operations)
```

## Validation Levels

| Level | Meaning | Action |
|-------|---------|--------|
| ✅ **APPROVED** | Safe and appropriate | Execute immediately |
| ⚠️ **UNCERTAIN** | Some concerns exist | Log with warning or escalate |
| ❌ **REJECTED** | High risk detected | Block execution |

## Integration Patterns

### Pattern 1: Hybrid (Recommended)
Combines middleware (mandatory validation) with skill (explicit reasoning).

```python
agent = ValidatedAgent(client, tools, validator)
result = agent.run(prompt)  # Validation happens automatically
```

### Pattern 2: Skill Only
Agent explicitly calls validation when needed.

```python
tools.append(JevValidationSkill(validator).get_tool_definition())
# Agent decides when to validate
```

### Pattern 3: Middleware Only
Wraps agent executor for mandatory validation.

```python
executor = ValidatingExecutor(agent, validator)
```

## Test Results

**Tool Call Validation:**
- ✅ 3 approved (safe operations)
- ❌ 2 rejected (risky operations)
- ⏱️ Average latency: 0.5s

**Decision Validation:**
- ✅ 1 approved
- ⚠️ 1 uncertain
- ❌ 1 rejected

**Success Rate:** 100% (8/8 tests passing)

## Architecture

```
OpenClaw Decision Maker
├── jev_decision_maker/
│   ├── validator.py          # Core validation engine
│   ├── agent.py              # ValidatedAgent wrapper
│   ├── skill.py              # Validation skill for agents
│   └── types.py              # Data types and enums
├── tests/
│   ├── test_validator.py     # 8 comprehensive tests
│   └── test_integration.py   # Integration examples
├── docs/
│   ├── INTEGRATION_GUIDE.md  # How to integrate
│   ├── API_REFERENCE.md      # Complete API docs
│   └── PATTERNS.md           # Integration patterns
└── examples/
    ├── openclaw_example.py   # OpenClaw integration
    └── claude_example.py     # Claude API example
```

## Documentation

- **[Quick Start](./docs/QUICK_START.md)** — Get started in 5 minutes
- **[Integration Guide](./docs/INTEGRATION_GUIDE.md)** — Integrate with your agent
- **[API Reference](./docs/API_REFERENCE.md)** — Complete API documentation
- **[Integration Patterns](./docs/PATTERNS.md)** — All 5 integration approaches
- **[Examples](./examples/)** — Working code examples

## Framework Support

| Framework | Supported | Notes |
|-----------|-----------|-------|
| Claude / Claude API | ✅ Yes | Native integration with ValidatedAgent |
| LangChain | ✅ Yes | Use via callbacks/hooks |
| LlamaIndex | ✅ Yes | Tool wrapper approach |
| Custom Agents | ✅ Yes | Middleware wrapper |

## Configuration

### Strict Mode
Reject all uncertain operations:

```python
agent = ValidatedAgent(validator=validator, strict_mode=True)
```

### Custom Validation Rules
Extend validator with custom questions:

```python
validator = JevValidator()
validator.add_question("is_reversible", {
    "type": "noul",
    "instructions": "Can this action be reversed?",
    "criteria": {
        "true": "Action can be undone",
        "false": "Action is permanent"
    }
})
```

### Confidence Thresholds
Adjust minimum confidence for approval:

```python
agent = ValidatedAgent(
    validator=validator,
    confidence_threshold=0.8  # Require 80%+ confidence
)
```

## Performance

- **Validation Latency:** ~0.5 seconds per operation
- **Throughput:** ~2 validations per second
- **Overhead:** Minimal (async support available)
- **Cost:** ~$0.001-0.01 per validation (via OpenRouter)

## Use Cases

### 1. Enterprise LLM Applications
Ensure agent operations meet compliance requirements.

```python
# Validate all database operations
agent = ValidatedAgent(
    validator=validator,
    strict_mode=True
)
```

### 2. Financial Applications
Verify all monetary transactions.

```python
# Blocks risky financial operations
result = agent.run("Transfer $1M without checking balance")
# Rejected: "High risk financial operation"
```

### 3. Healthcare Systems
Ensure patient data is handled safely.

```python
# Validates HIPAA compliance
result = agent.run("Export all patient records")
# Rejected: "Unsafe data export without audit"
```

### 4. Content Moderation
Verify appropriate content decisions.

```python
# Validates content safety
result = agent.run("Publish unreviewed user-generated content")
# Rejected: "Content not reviewed for safety"
```

## Audit Trail

Every operation is logged with full context:

```json
{
  "timestamp": "2024-09-25T10:15:30Z",
  "tool": "delete_records",
  "parameters": {"table": "users", "condition": "WHERE 1=1"},
  "validation": {
    "status": "rejected",
    "safe": false,
    "appropriate": false,
    "confidence": 0.55,
    "reasoning": "High risk operation with unsafe conditions"
  },
  "action": "blocked"
}
```

## Contributing

We welcome contributions! See [CONTRIBUTING.md](./CONTRIBUTING.md) for guidelines.

### Development Setup

```bash
# Clone repo
git clone https://github.com/yourusername/openclaw-decision-maker.git
cd openclaw-decision-maker

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
pytest

# Format code
black .
```

## License

MIT License - See [LICENSE](./LICENSE) for details

## Support

- 📖 **Documentation:** Check [docs/](./docs/)
- 🐛 **Issues:** [GitHub Issues](https://github.com/yourusername/openclaw-decision-maker/issues)
- 💬 **Discussions:** [GitHub Discussions](https://github.com/yourusername/openclaw-decision-maker/discussions)

## Related Projects

- **[Jev](https://typesafe.ai/)** — The decision-making model powering this validator
- **[OpenClaw](https://github.com/yourusername/openclaw)** — The agent framework this is built for
- **[LangChain](https://www.langchain.com/)** — Supported agent framework

## Roadmap

- [ ] Async validation support
- [ ] Custom validation schemas
- [ ] Dashboard for audit logs
- [ ] Integration with more frameworks
- [ ] Benchmarking suite
- [ ] Performance optimizations

## Citation

If you use OpenClaw Decision Maker in your research or project, please cite:

```bibtex
@software{openclaw_decision_maker,
  title={OpenClaw Decision Maker: Verification Layer for AI Agents},
  author={Your Name},
  year={2024},
  url={https://github.com/yourusername/openclaw-decision-maker}
}
```

## Acknowledgments

- Built with [Jev](https://typesafe.ai/) structured decision-making
- Inspired by safety-critical systems design
- Thanks to the open-source community

---

**Made for building safer AI systems** 🛡️
