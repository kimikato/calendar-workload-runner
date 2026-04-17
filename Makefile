# ============================================================
# calendar-workload-runner Makefile
#
# This Makefile provides a unified interface for:
#   - Installing development dependencies
#   - Running linters (flake8)
#   - Running type checks (mypy)
#   - Running tests (pytest)
#   - Generating code coverage reports
#   - Auto-formatting the codebase (Black)
#
# Usage:
#   make init          # Install dev dependencies
#   make lint          # Run flake8
#   make typecheck     # Run mypy
#   make test          # Run pytest
#   make check         # Run lint + typecheck + test
#   make coverage      # Run coverage (+ report)
#   make coverage-html # Generate HTML coverage report
#   make format        # Run black formatter
#   make all           # Run check + coverage
#   make clean         # Remove caches and build artifacts
#
# Notes:
#   - All dev tools are installed through pyproject.toml `[project.optional-dependencies].dev`
#   - `make check` is ideal for quick local verification
#   - `make all` is useful for pre-commit checking and CI
# ============================================================

.PHONY: init lint typecheck test check coverage coverage-html format all clean


# ------------------------------------------------------------
# Install development dependencies
# ------------------------------------------------------------
init:
	@echo ">>> Installing calendar-workload-runner development dependencies..."
	python -m pip install -e .[dev]


# ------------------------------------------------------------
# Lint (flake8)
# ------------------------------------------------------------
lint:
	@echo ">>> Running flake8..."
	flake8 src/calendar_workload_runner tests


# ------------------------------------------------------------
# Type checking (mypy)
# ------------------------------------------------------------
typecheck:
	@echo ">>> Running mypy..."
	mypy src/calendar_workload_runner tests


# ------------------------------------------------------------
# Run tests (pytest)
# ------------------------------------------------------------
test:
	@echo ">>> Running pytest..."
	pytest


# ------------------------------------------------------------
# Run quick verification: lint + typecheck + test
# ------------------------------------------------------------
check: lint typecheck test
	@echo ">>> Checks completed successfully!"


# ------------------------------------------------------------
# Coverage: CLI report
# ------------------------------------------------------------
coverage:
	@echo ">>> Running coverage..."
	coverage run -m pytest
	coverage report


# ------------------------------------------------------------
# Coverage: HTML report
# ------------------------------------------------------------
coverage-html:
	@echo ">>> Generating HTML coverage report..."
	coverage run -m pytest
	coverage html
	@echo "Open htmlcov/index.html in your browser."


# ------------------------------------------------------------
# Auto-code formatting (Black)
# ------------------------------------------------------------
format:
	@echo ">>> Formatting code with Black..."
	black src/calendar_workload_runner tests


# ------------------------------------------------------------
# Run everything: check + coverage
# ------------------------------------------------------------
all: check coverage
	@echo ">>> All checks completed successfully!"


# ------------------------------------------------------------
# Clean cache / build artifacts
# ------------------------------------------------------------
clean:
	@echo ">>> Cleaning build artifacts & caches..."
	rm -rf .coverage htmlcov/ __pycache__/ */__pycache__/ \
		build dist *.egg-info
