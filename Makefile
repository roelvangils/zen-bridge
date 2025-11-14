.PHONY: help dev install clean test test-unit test-integration test-e2e lint format typecheck pre-commit all

# Default target
help:
	@echo "Inspekt - Development Commands"
	@echo ""
	@echo "Setup:"
	@echo "  make dev          Install package in development mode with all dependencies"
	@echo "  make install      Install package for production use"
	@echo "  make clean        Remove build artifacts and caches"
	@echo ""
	@echo "Testing:"
	@echo "  make test         Run all tests with coverage"
	@echo "  make test-unit    Run unit tests only"
	@echo "  make test-integration  Run integration tests only"
	@echo "  make test-e2e     Run end-to-end tests (requires browser)"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint         Run linter (ruff check)"
	@echo "  make format       Format code (ruff format)"
	@echo "  make typecheck    Run type checker (mypy)"
	@echo "  make pre-commit   Install and run pre-commit hooks"
	@echo ""
	@echo "Combined:"
	@echo "  make all          Run format, lint, typecheck, and test"

# Development setup
dev:
	pip install -e ".[dev]"
	@echo ""
	@echo "✓ Development environment ready!"
	@echo "  Run 'make pre-commit' to install pre-commit hooks"
	@echo "  Run 'make test' to run the test suite"

install:
	pip install -e .

# Clean build artifacts
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .pytest_cache
	rm -rf .mypy_cache
	rm -rf .ruff_cache
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf coverage.xml
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	@echo "✓ Cleaned build artifacts"

# Testing
test:
	pytest tests/ -v --cov=inspekt --cov-report=term-missing --cov-report=html
	@echo ""
	@echo "✓ Tests complete. Coverage report: htmlcov/index.html"

test-unit:
	pytest tests/unit/ -v -m unit

test-integration:
	pytest tests/integration/ -v -m integration

test-e2e:
	pytest tests/e2e/ -v -m e2e

# Code quality
lint:
	ruff check inspekt/ tests/

format:
	ruff format inspekt/ tests/
	@echo "✓ Code formatted"

typecheck:
	mypy inspekt/ --config-file=pyproject.toml

# Pre-commit
pre-commit:
	pre-commit install
	pre-commit run --all-files
	@echo "✓ Pre-commit hooks installed and run"

# Run all checks
all: format lint typecheck test
	@echo ""
	@echo "✓ All checks passed!"
