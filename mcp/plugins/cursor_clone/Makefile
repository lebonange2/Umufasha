# Makefile for Cursor-AI Clone

.PHONY: setup dev test accept bench clean

setup:
	@echo "Setting up Cursor-AI Clone..."
	pip install -r requirements.txt || echo "No requirements.txt found"
	@echo "✓ Setup complete"

dev:
	@echo "Starting development mode..."
	python3 -m mcp.plugins.cursor_clone.ui.cli --chat

test:
	@echo "Running unit tests..."
	python3 -m pytest mcp/plugins/cursor_clone/tests/unit/ -v

test-e2e:
	@echo "Running E2E tests..."
	python3 -m pytest mcp/plugins/cursor_clone/tests/e2e/ -v

accept:
	@echo "Running acceptance tests..."
	python3 -m pytest mcp/plugins/cursor_clone/tests/acceptance/ -v -m acceptance

bench:
	@echo "Running benchmarks..."
	python3 -m pytest mcp/plugins/cursor_clone/tests/bench/ -v || echo "No benchmarks found"

clean:
	@echo "Cleaning..."
	find . -type d -name __pycache__ -exec rm -r {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "✓ Clean complete"

index:
	@echo "Indexing repository..."
	python3 -m mcp.plugins.cursor_clone.ui.cli --index

web:
	@echo "Starting web panel..."
	python3 -m mcp.plugins.cursor_clone.ui.webpanel.app

