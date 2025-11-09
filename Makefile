# Makefile für ThemisDB Adapter Test Suite
# =========================================

.PHONY: help install test lint format clean coverage docs

# Colors
CYAN := \033[0;36m
GREEN := \033[0;32m
RED := \033[0;31m
NC := \033[0m # No Color

help:
	@echo "$(CYAN)ThemisDB Adapter Test Suite$(NC)"
	@echo "============================"
	@echo ""
	@echo "Available targets:"
	@echo "  $(GREEN)install$(NC)       - Install dependencies"
	@echo "  $(GREEN)test$(NC)          - Run all tests"
	@echo "  $(GREEN)test-unit$(NC)     - Run unit tests only"
	@echo "  $(GREEN)test-integration$(NC) - Run integration tests"
	@echo "  $(GREEN)test-api$(NC)      - Run API tests"
	@echo "  $(GREEN)test-websocket$(NC) - Run WebSocket tests"
	@echo "  $(GREEN)lint$(NC)          - Run linting checks"
	@echo "  $(GREEN)format$(NC)        - Format code (black, isort)"
	@echo "  $(GREEN)coverage$(NC)      - Run tests with coverage"
	@echo "  $(GREEN)clean$(NC)         - Clean temporary files"
	@echo "  $(GREEN)docs$(NC)          - Generate documentation"
	@echo "  $(GREEN)security$(NC)      - Run security checks"
	@echo "  $(GREEN)load-test$(NC)     - Run load tests"

install:
	@echo "$(CYAN)Installing dependencies...$(NC)"
	pip install -r requirements.txt
	pip install -r requirements-dev.txt
	pre-commit install

test:
	@echo "$(CYAN)Running all tests...$(NC)"
	pytest tests/ -v --cov=backend --cov-report=term-missing

test-unit:
	@echo "$(CYAN)Running unit tests...$(NC)"
	pytest tests/ -v -m "unit or not (integration or e2e)"

test-integration:
	@echo "$(CYAN)Running integration tests...$(NC)"
	pytest tests/ -v -m "integration"

test-api:
	@echo "$(CYAN)Running API tests...$(NC)"
	pytest tests/test_themis_router.py tests/test_adapter_router.py -v

test-websocket:
	@echo "$(CYAN)Running WebSocket tests...$(NC)"
	pytest tests/test_websocket_router.py -v

lint:
	@echo "$(CYAN)Running linting checks...$(NC)"
	black --check backend/ tests/
	isort --check-only backend/ tests/
	flake8 backend/ tests/
	pylint backend/ --exit-zero
	mypy backend/ --ignore-missing-imports

format:
	@echo "$(CYAN)Formatting code...$(NC)"
	black backend/ tests/
	isort backend/ tests/

coverage:
	@echo "$(CYAN)Running tests with coverage...$(NC)"
	pytest tests/ --cov=backend --cov-report=html --cov-report=term-missing
	@echo "$(GREEN)Coverage report: htmlcov/index.html$(NC)"

clean:
	@echo "$(CYAN)Cleaning temporary files...$(NC)"
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage
	rm -rf coverage.xml
	rm -rf pytest-report.xml
	rm -rf bandit-report.json
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete

docs:
	@echo "$(CYAN)Generating documentation...$(NC)"
	mkdocs build

security:
	@echo "$(CYAN)Running security checks...$(NC)"
	bandit -r backend/ -ll || true
	pip-audit -r requirements.txt -r requirements-dev.txt || true

load-test:
	@echo "$(CYAN)Running load tests...$(NC)"
	locust -f tests/load/locustfile.py --headless --users 100 --spawn-rate 10 --run-time 60s --host http://localhost:8000

ci:
	@echo "$(CYAN)Running CI pipeline...$(NC)"
	make lint
	make test
	make security
