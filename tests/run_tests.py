"""
VERITAS Test Runner
===================

Comprehensive test runner for all VERITAS test suites.

Usage:
    # Run all tests
    python run_tests.py

    # Run specific category
    python run_tests.py --backend
    python run_tests.py --frontend
    python run_tests.py --integration
    python run_tests.py --performance
    python run_tests.py --e2e

    # Run with coverage
    python run_tests.py --coverage

    # Quick tests (skip slow tests)
    python run_tests.py --quick
"""

import sys
import os
import argparse
import subprocess
from pathlib import Path


# Test categories
TEST_CATEGORIES = {
    'backend': 'tests/backend/',
    'frontend': 'tests/frontend/',
    'integration': 'tests/integration/test_integration_e2e.py',
    'performance': 'tests/integration/test_performance.py',
    'all': 'tests/'
}


def run_pytest(args_list):
    """Run pytest with given arguments."""
    cmd = ['pytest'] + args_list
    print(f"\n{'='*80}")
    print(f"Running: {' '.join(cmd)}")
    print(f"{'='*80}\n")
    
    result = subprocess.run(cmd, cwd=os.path.dirname(__file__))
    return result.returncode


def main():
    parser = argparse.ArgumentParser(description='Run VERITAS tests')
    
    # Test categories
    parser.add_argument('--backend', action='store_true', help='Run backend tests only')
    parser.add_argument('--frontend', action='store_true', help='Run frontend tests only')
    parser.add_argument('--integration', action='store_true', help='Run integration tests only')
    parser.add_argument('--performance', action='store_true', help='Run performance benchmarks')
    parser.add_argument('--e2e', action='store_true', help='Run end-to-end tests')
    parser.add_argument('--all', action='store_true', help='Run all tests (default)')
    
    # Options
    parser.add_argument('--coverage', action='store_true', help='Generate coverage report')
    parser.add_argument('--quick', action='store_true', help='Skip slow tests')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--failfast', '-x', action='store_true', help='Stop on first failure')
    
    args = parser.parse_args()
    
    # Determine which tests to run
    test_paths = []
    if args.backend:
        test_paths.append(TEST_CATEGORIES['backend'])
    if args.frontend:
        test_paths.append(TEST_CATEGORIES['frontend'])
    if args.integration or args.e2e:
        test_paths.append(TEST_CATEGORIES['integration'])
    if args.performance:
        test_paths.append(TEST_CATEGORIES['performance'])
    
    # Default to all tests
    if not test_paths or args.all:
        test_paths = [TEST_CATEGORIES['all']]
    
    # Build pytest arguments
    pytest_args = []
    
    # Add test paths
    pytest_args.extend(test_paths)
    
    # Add options
    if args.verbose:
        pytest_args.append('-v')
    
    if args.failfast:
        pytest_args.append('-x')
    
    if args.quick:
        pytest_args.extend(['-m', 'not slow'])
    
    if args.coverage:
        pytest_args.extend([
            '--cov=backend',
            '--cov=frontend',
            '--cov-report=html',
            '--cov-report=term-missing'
        ])
    
    # Always show short test summary
    pytest_args.append('--tb=short')
    
    # Run tests
    return_code = run_pytest(pytest_args)
    
    # Print summary
    print(f"\n{'='*80}")
    if return_code == 0:
        print("✅ ALL TESTS PASSED")
    else:
        print(f"❌ TESTS FAILED (exit code: {return_code})")
    
    if args.coverage:
        print("\n📊 Coverage report generated:")
        print("   HTML: htmlcov/index.html")
    
    print(f"{'='*80}\n")
    
    return return_code


if __name__ == '__main__':
    sys.exit(main())
