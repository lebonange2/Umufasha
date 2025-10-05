# Contributing to Brainstorming Assistant

Thank you for your interest in contributing! This document provides guidelines for contributing to the project.

## Getting Started

1. **Fork the repository**
2. **Clone your fork**:
   ```bash
   git clone https://github.com/yourusername/brainstorm-assistant.git
   cd brainstorm-assistant
   ```
3. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```
4. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   pip install pytest black flake8 mypy
   ```

## Development Workflow

### 1. Create a Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/your-bug-fix
```

### 2. Make Changes

- Follow the existing code style
- Add docstrings to functions and classes
- Keep functions focused and modular
- Add type hints where appropriate

### 3. Test Your Changes

```bash
# Run tests
pytest tests/

# Run specific test file
pytest tests/test_brain.py -v

# Check code style
black --check .
flake8 .

# Type checking
mypy app.py brain/ llm/ storage/
```

### 4. Commit Changes

```bash
git add .
git commit -m "feat: add new feature"
# or
git commit -m "fix: resolve issue with X"
```

**Commit message format**:
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `test:` - Test additions/changes
- `refactor:` - Code refactoring
- `style:` - Code style changes
- `chore:` - Build/tooling changes

### 5. Push and Create PR

```bash
git push origin feature/your-feature-name
```

Then create a Pull Request on GitHub.

## Code Style

### Python Style
- Follow PEP 8
- Use Black for formatting: `black .`
- Maximum line length: 100 characters
- Use type hints for function signatures

### Example:
```python
def process_audio(audio_data: np.ndarray, sample_rate: int = 16000) -> Optional[str]:
    """Process audio data and return transcription.
    
    Args:
        audio_data: Audio samples as numpy array
        sample_rate: Sample rate in Hz
        
    Returns:
        Transcribed text or None if failed
    """
    # Implementation
    pass
```

### Docstrings
Use Google-style docstrings:
```python
def function(arg1: str, arg2: int) -> bool:
    """Short description.
    
    Longer description if needed.
    
    Args:
        arg1: Description of arg1
        arg2: Description of arg2
        
    Returns:
        Description of return value
        
    Raises:
        ValueError: When something is wrong
    """
```

## Testing

### Writing Tests
- Place tests in `tests/` directory
- Name test files `test_*.py`
- Name test functions `test_*`
- Use pytest fixtures for setup/teardown
- Aim for >80% code coverage

### Example Test:
```python
def test_idea_creation():
    """Test creating a new idea."""
    idea = Idea.create("Test idea", tags=["test"])
    
    assert idea.text == "Test idea"
    assert "test" in idea.tags
    assert idea.id is not None
```

### Running Tests:
```bash
# All tests
pytest

# With coverage
pytest --cov=. --cov-report=html

# Specific test
pytest tests/test_brain.py::test_idea_creation -v
```

## Adding New Features

### New STT Backend
1. Create file in `stt/` directory
2. Inherit from `STTBackend`
3. Implement `transcribe()` and `is_available()`
4. Add to backend selection in `app.py`
5. Update documentation

### New LLM Backend
1. Create file in `llm/` directory
2. Inherit from `LLMBackend`
3. Implement `chat()` and `is_available()`
4. Add to backend selection in `app.py`
5. Update documentation

### New Export Format
1. Add exporter class in `storage/exporters.py`
2. Implement `export()` method
3. Add to `export_session()` function
4. Update documentation

### New TUI Widget
1. Create widget in `tui/widgets.py`
2. Inherit from appropriate Textual widget
3. Add to `main_view.py` if needed
4. Update CSS in `app.tcss`

## Documentation

### Code Documentation
- Add docstrings to all public functions/classes
- Update README.md for user-facing changes
- Update QUICKSTART.md for setup changes
- Add inline comments for complex logic

### User Documentation
- Update README.md for new features
- Add examples to QUICKSTART.md
- Update config.yaml comments
- Update help text in TUI

## Pull Request Guidelines

### Before Submitting
- [ ] Tests pass: `pytest`
- [ ] Code formatted: `black .`
- [ ] No linting errors: `flake8 .`
- [ ] Documentation updated
- [ ] CHANGELOG.md updated (if applicable)

### PR Description
Include:
1. **What** - What does this PR do?
2. **Why** - Why is this change needed?
3. **How** - How does it work?
4. **Testing** - How was it tested?
5. **Screenshots** - If UI changes

### Example PR Template:
```markdown
## Description
Adds support for Ollama as an LLM backend.

## Motivation
Many users want to run fully offline without API keys.

## Changes
- Added OllamaClient in llm/ollama_client.py
- Updated app.py to support ollama backend
- Added configuration options
- Added tests

## Testing
- Tested with Ollama running locally
- All existing tests pass
- Added test_ollama_client.py

## Documentation
- Updated README.md with Ollama setup
- Updated QUICKSTART.md
```

## Issue Guidelines

### Bug Reports
Include:
- **Description** - What happened?
- **Expected** - What should happen?
- **Steps to reproduce**
- **Environment** - OS, Python version, etc.
- **Logs** - Relevant error messages

### Feature Requests
Include:
- **Description** - What feature?
- **Use case** - Why is it needed?
- **Proposed solution** - How might it work?
- **Alternatives** - Other approaches considered?

## Code Review Process

1. **Automated checks** run on PR
2. **Maintainer review** within 1-2 days
3. **Address feedback** if requested
4. **Approval and merge** when ready

## Community

- Be respectful and constructive
- Help others in issues/discussions
- Share your use cases and ideas
- Report bugs you find

## Questions?

- Open an issue for questions
- Check existing issues first
- Be specific and provide context

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

Thank you for contributing! 🎉
