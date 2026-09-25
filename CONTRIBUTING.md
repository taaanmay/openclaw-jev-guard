# Contributing to OpenClaw Decision Maker

Thank you for your interest in contributing! This document provides guidelines and instructions for contributing to the project.

## Code of Conduct

We are committed to providing a welcoming and inspiring community. Please review our [Code of Conduct](./CODE_OF_CONDUCT.md) before participating.

## How to Contribute

### Reporting Bugs

1. Check if the issue already exists in [GitHub Issues](https://github.com/yourusername/openclaw-decision-maker/issues)
2. If not, create a new issue with:
   - Clear, descriptive title
   - Description of the bug
   - Steps to reproduce
   - Expected behavior
   - Actual behavior
   - Screenshots if applicable
   - Your environment (OS, Python version, etc.)

### Suggesting Enhancements

1. Check [GitHub Discussions](https://github.com/yourusername/openclaw-decision-maker/discussions) for similar suggestions
2. Create a discussion with:
   - Clear description of the enhancement
   - Motivation and use cases
   - Possible implementation approach
   - Alternative solutions considered

### Pull Requests

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature-name`
3. Make your changes
4. Add tests for new functionality
5. Update documentation as needed
6. Run tests: `pytest`
7. Format code: `black . && isort .`
8. Commit with clear message: `git commit -m "Add feature description"`
9. Push to your fork: `git push origin feature/your-feature-name`
10. Open a Pull Request with:
    - Clear description of changes
    - Reference to related issues
    - Screenshots if applicable

## Development Setup

```bash
# Clone repository
git clone https://github.com/yourusername/openclaw-decision-maker.git
cd openclaw-decision-maker

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black .
isort .

# Type checking
mypy jev_decision_maker/
```

## Coding Standards

### Style Guide

- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/)
- Use Black for code formatting (line length: 100)
- Use isort for import organization
- Type hints for all public functions

### Testing

- Write tests for all new features
- Maintain or increase code coverage
- Use pytest for testing
- Follow naming convention: `test_*.py` or `*_test.py`

Example test:

```python
def test_validator_rejects_dangerous_operation():
    """Test that validator rejects high-risk operations"""
    validator = JevValidator()
    tool_call = ToolCall(
        tool_name="delete_all",
        parameters={"table": "users"}
    )
    result = validator.validate_tool_call(tool_call)
    assert result.validation_level == ValidationLevel.REJECTED
```

### Documentation

- Update README.md for user-facing changes
- Update docstrings for API changes
- Add examples for new features
- Use Google-style docstrings

Example docstring:

```python
def validate_tool_call(self, tool_call: ToolCall) -> ValidationResult:
    """Validate a tool call for safety and appropriateness.
    
    Args:
        tool_call: The tool call to validate
        
    Returns:
        ValidationResult with status and reasoning
        
    Raises:
        ValueError: If Jev API returns an error
    """
```

## Commit Messages

Write clear, descriptive commit messages:

- Use imperative mood ("add feature" not "added feature")
- Limit subject line to 50 characters
- Reference issues: "Fix #123"
- Explain what and why, not how

Example:
```
Add confidence threshold configuration

Allow users to set minimum confidence requirements for approval.
Fixes #42
```

## Pull Request Process

1. Update the README.md with details of changes
2. Update documentation as needed
3. Ensure all tests pass
4. Ensure code is formatted correctly
5. Request review from maintainers
6. Address review feedback
7. Squash commits if requested

## Review Process

- Maintainers will review PRs within 5 business days
- Request changes indicate needed improvements
- Approved PRs can be merged by maintainers
- Be respectful and constructive in discussions

## Areas for Contribution

### High Priority
- [ ] Framework integrations (FastAPI, Django, etc.)
- [ ] Performance optimizations
- [ ] Dashboard for audit logs
- [ ] More validation examples

### Medium Priority
- [ ] Additional test coverage
- [ ] Documentation improvements
- [ ] Type hint completeness
- [ ] Error message improvements

### Low Priority
- [ ] Code style improvements
- [ ] README formatting
- [ ] Comment updates

## Questions?

- Check [Discussions](https://github.com/yourusername/openclaw-decision-maker/discussions)
- Email: maintainers@example.com
- Open an issue for bugs

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to making AI agents safer! 🛡️
