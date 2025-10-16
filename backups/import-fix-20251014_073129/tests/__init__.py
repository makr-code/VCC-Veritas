"""
VERITAS Test Suite v3.19.0

Test Structure:
- backend/    : Backend API tests (FastAPI, Services)
- frontend/   : Frontend UI tests (Tkinter, Mocks)
- integration/: E2E integration tests (Full workflows)

Usage:
    # Run all tests
    pytest tests/
    
    # Run specific category
    pytest tests/backend/
    pytest tests/frontend/
    
    # Run with coverage
    pytest tests/ --cov=backend --cov=frontend --cov-report=html
    
    # Run specific test
    pytest tests/backend/test_feedback_api.py::test_submit_feedback
"""

__version__ = "3.19.0"
