"""
VERITAS Test Runner
===================

Führt alle Tests aus und gibt einen übersichtlichen Report.

Usage:
    python tests/run_all_tests.py [--verbose] [--coverage]
"""

import sys
import argparse
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pytest


def main():
    parser = argparse.ArgumentParser(description="VERITAS Test Runner")
    parser.add_argument("-v", "--verbose", action="store_true", 
                       help="Verbose output")
    parser.add_argument("-c", "--coverage", action="store_true",
                       help="Run with coverage report")
    parser.add_argument("-k", "--keyword", type=str,
                       help="Run only tests matching keyword")
    parser.add_argument("--json", action="store_true",
                       help="Run only JSON extraction tests")
    parser.add_argument("--template", action="store_true",
                       help="Run only template tests")
    
    args = parser.parse_args()
    
    print("\n" + "="*80)
    print("  VERITAS Test Suite")
    print("="*80 + "\n")
    
    # Build pytest arguments
    pytest_args = [
        "tests/",
        "--color=yes",
        "-W", "ignore::DeprecationWarning"
    ]
    
    if args.verbose:
        pytest_args.append("-vv")
    else:
        pytest_args.append("-v")
    
    if args.coverage:
        pytest_args.extend([
            "--cov=backend",
            "--cov-report=term-missing",
            "--cov-report=html"
        ])
    
    if args.keyword:
        pytest_args.extend(["-k", args.keyword])
    
    if args.json:
        pytest_args = [pytest_args[0]] + ["tests/test_json_extraction.py"] + pytest_args[1:]
    elif args.template:
        pytest_args = [pytest_args[0]] + ["tests/test_ollama_template.py"] + pytest_args[1:]
    
    # Run tests
    exit_code = pytest.main(pytest_args)
    
    # Summary
    print("\n" + "="*80)
    if exit_code == 0:
        print("  ✅ ALLE TESTS ERFOLGREICH")
        print("="*80 + "\n")
        print("  Nächste Schritte:")
        print("  • Backend starten: .\\scripts\\start_services.ps1 -BackendOnly")
        print("  • Query testen:    Invoke-RestMethod http://localhost:5000/api/query")
    else:
        print("  ❌ TESTS FEHLGESCHLAGEN")
        print("="*80 + "\n")
        print("  Debugging:")
        print("  • Logs prüfen:     Get-Content .\\logs\\backend_uvicorn.err.log -Tail 50")
        print("  • Tests einzeln:   python tests/run_all_tests.py --json")
        print("  • Mit Coverage:    python tests/run_all_tests.py --coverage")
    print("="*80 + "\n")
    
    if args.coverage and exit_code == 0:
        print(f"  📊 Coverage Report: {project_root}/htmlcov/index.html\n")
    
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
