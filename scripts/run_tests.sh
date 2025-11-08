#!/bin/bash
# Bash Script zum Ausführen der Test-Suite (Linux/Mac)
# ====================================================

set -e  # Exit on error

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Default Parameters
TEST_TYPE="all"
COVERAGE=false
VERBOSE=false
PARALLEL=false
WORKERS=4

# Parse Arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --type)
            TEST_TYPE="$2"
            shift 2
            ;;
        --coverage)
            COVERAGE=true
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --parallel)
            PARALLEL=true
            shift
            ;;
        --workers)
            WORKERS="$2"
            shift 2
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

echo -e "${CYAN}================================================${NC}"
echo -e "${CYAN}ThemisDB Adapter Test Suite${NC}"
echo -e "${CYAN}================================================${NC}"
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}✗ Python3 not found!${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 --version)
echo -e "${GREEN}✓ Python found: $PYTHON_VERSION${NC}"

# Activate Virtual Environment
if [ -f ".venv/bin/activate" ]; then
    echo -e "${YELLOW}Activating Virtual Environment...${NC}"
    source .venv/bin/activate
fi

# Install Dependencies
echo -e "${YELLOW}\nInstalling Dependencies...${NC}"
pip install -q -r requirements.txt
pip install -q -r requirements-dev.txt

# Pytest Arguments
PYTEST_ARGS=""

if [ "$VERBOSE" = true ]; then
    PYTEST_ARGS="$PYTEST_ARGS -v"
fi

if [ "$COVERAGE" = true ]; then
    PYTEST_ARGS="$PYTEST_ARGS --cov=backend --cov-report=term-missing --cov-report=html --cov-report=xml"
fi

if [ "$PARALLEL" = true ]; then
    PYTEST_ARGS="$PYTEST_ARGS -n $WORKERS"
fi

# Run Tests
case $TEST_TYPE in
    lint)
        echo -e "${CYAN}\n=== Running Code Quality Checks ===${NC}"
        
        echo -e "${YELLOW}\n→ Black...${NC}"
        black --check backend/ tests/ || true
        
        echo -e "${YELLOW}\n→ isort...${NC}"
        isort --check-only backend/ tests/ || true
        
        echo -e "${YELLOW}\n→ Flake8...${NC}"
        flake8 backend/ tests/ --count --statistics
        
        echo -e "${YELLOW}\n→ Pylint...${NC}"
        pylint backend/ --exit-zero
        
        echo -e "${YELLOW}\n→ mypy...${NC}"
        mypy backend/ --ignore-missing-imports || true
        
        echo -e "${YELLOW}\n→ Bandit...${NC}"
        bandit -r backend/ -ll || true
        ;;
    
    unit)
        echo -e "${CYAN}\n=== Running Unit Tests ===${NC}"
        pytest $PYTEST_ARGS -m "unit or not (integration or e2e)" tests/
        ;;
    
    integration)
        echo -e "${CYAN}\n=== Running Integration Tests ===${NC}"
        pytest $PYTEST_ARGS -m "integration" tests/
        ;;
    
    api)
        echo -e "${CYAN}\n=== Running API Tests ===${NC}"
        pytest $PYTEST_ARGS tests/test_themis_router.py tests/test_adapter_router.py
        ;;
    
    websocket)
        echo -e "${CYAN}\n=== Running WebSocket Tests ===${NC}"
        pytest $PYTEST_ARGS tests/test_websocket_router.py
        ;;
    
    adapter)
        echo -e "${CYAN}\n=== Running Adapter Tests ===${NC}"
        pytest $PYTEST_ARGS tests/test_themisdb_adapter.py
        ;;
    
    all)
        echo -e "${CYAN}\n=== Running All Tests ===${NC}"
        
        echo -e "${YELLOW}\n→ Step 1: Code Quality${NC}"
        bash $0 --type lint
        
        echo -e "${YELLOW}\n→ Step 2: Unit Tests${NC}"
        pytest $PYTEST_ARGS -m "not integration and not e2e" tests/
        
        echo -e "${YELLOW}\n→ Step 3: Integration Tests${NC}"
        bash $0 --type integration
        
        echo -e "${YELLOW}\n→ Step 4: API Tests${NC}"
        bash $0 --type api
        
        echo -e "${YELLOW}\n→ Step 5: WebSocket Tests${NC}"
        bash $0 --type websocket
        ;;
    
    *)
        echo -e "${RED}Unknown test type: $TEST_TYPE${NC}"
        echo -e "${YELLOW}Available: all, unit, integration, api, websocket, adapter, lint${NC}"
        exit 1
        ;;
esac

# Summary
echo -e "${CYAN}\n================================================${NC}"
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ All tests passed!${NC}"
else
    echo -e "${RED}✗ Some tests failed!${NC}"
fi
echo -e "${CYAN}================================================${NC}"

# Coverage Report
if [ "$COVERAGE" = true ] && [ -f "htmlcov/index.html" ]; then
    echo -e "${YELLOW}\nCoverage Report: htmlcov/index.html${NC}"
    if command -v xdg-open &> /dev/null; then
        xdg-open htmlcov/index.html
    elif command -v open &> /dev/null; then
        open htmlcov/index.html
    fi
fi
