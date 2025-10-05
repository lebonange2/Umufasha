.PHONY: help install test run clean format lint check audio models

help:
	@echo "🧠 Brainstorming Assistant - Make Commands"
	@echo ""
	@echo "Setup:"
	@echo "  make install    - Install dependencies"
	@echo "  make models     - Download STT models"
	@echo "  make audio      - Check audio devices"
	@echo ""
	@echo "Development:"
	@echo "  make test       - Run tests"
	@echo "  make format     - Format code with black"
	@echo "  make lint       - Run linters"
	@echo "  make check      - Run all checks (format, lint, test)"
	@echo ""
	@echo "Running:"
	@echo "  make run        - Run with default project"
	@echo "  make run PROJECT=name - Run with specific project"
	@echo ""
	@echo "Maintenance:"
	@echo "  make clean      - Clean temporary files"

install:
	@echo "Installing dependencies..."
	pip install -r requirements.txt
	@echo "✓ Dependencies installed"
	@echo ""
	@echo "Next steps:"
	@echo "  1. Copy .env.example to .env"
	@echo "  2. Edit .env with your API keys"
	@echo "  3. Run: make audio (to test microphone)"
	@echo "  4. Run: make models (to download STT models)"
	@echo "  5. Run: make run"

models:
	@echo "Downloading Whisper base model..."
	python scripts/download_models.py whisper --size base
	@echo ""
	@echo "For Vosk models, run:"
	@echo "  python scripts/download_models.py vosk"

audio:
	@echo "Checking audio devices..."
	python scripts/check_audio.py

test:
	@echo "Running tests..."
	pytest tests/ -v --cov=. --cov-report=term-missing

format:
	@echo "Formatting code..."
	black . --exclude venv
	@echo "✓ Code formatted"

lint:
	@echo "Running linters..."
	flake8 . --exclude=venv --max-line-length=100 --extend-ignore=E203,W503
	@echo "✓ Linting complete"

check: format lint test
	@echo "✓ All checks passed"

run:
	@if [ -z "$(PROJECT)" ]; then \
		python app.py; \
	else \
		python app.py --project $(PROJECT); \
	fi

clean:
	@echo "Cleaning temporary files..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.log" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".coverage" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name ".coverage" -delete
	@echo "✓ Cleaned"

.DEFAULT_GOAL := help
