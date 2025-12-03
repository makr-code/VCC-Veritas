#!/usr/bin/env python3
"""
Comprehensive Test Runner for All AI Agent Features

Runs unit tests, integration tests, and benchmarks for all 4 agents.
"""

import subprocess
import sys
from pathlib import Path
import json
from datetime import datetime


def run_command(cmd, description):
    """Run a command and return success status"""
    print(f"\n{'='*70}")
    print(f"{description}")
    print(f"{'='*70}")
    print(f"Command: {' '.join(cmd)}\n")
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=False,
            text=True,
            check=False
        )
        
        success = result.returncode == 0
        print(f"\n{'✅ PASSED' if success else '❌ FAILED'}\n")
        return success
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}\n")
        return False


def main():
    """Main test runner"""
    print("\n" + "="*70)
    print("VERITAS AI AGENTS - COMPREHENSIVE TEST SUITE")
    print("="*70)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    
    results = {}
    project_root = Path(__file__).parent.parent
    
    # 1. Unit Tests - Vector Chart Agent
    results['unit_vector_chart'] = run_command(
        ['pytest', 'tests/agents/test_vector_chart_agent.py', '-v', '-m', 'unit'],
        "Unit Tests: Vector Chart Agent"
    )
    
    # 2. Unit Tests - Presentation Canvas Agent
    results['unit_presentation'] = run_command(
        ['pytest', 'tests/agents/test_presentation_canvas_agent.py', '-v', '-m', 'unit'],
        "Unit Tests: Presentation Canvas Agent"
    )
    
    # 3. Unit Tests - Geo Sub-Agent
    results['unit_geo'] = run_command(
        ['pytest', 'tests/agents/test_geo_sub_agent.py', '-v', '-m', 'unit'],
        "Unit Tests: Geo Sub-Agent"
    )
    
    # 4. Unit Tests - AI Image Generator
    results['unit_ai_image'] = run_command(
        ['pytest', 'tests/agents/test_ai_image_generator.py', '-v', '-m', 'unit'],
        "Unit Tests: AI Image Generator"
    )
    
    # 5. Integration Tests - API Endpoints
    results['integration_api'] = run_command(
        ['pytest', 'tests/integration/test_api_endpoints.py', '-v', '-m', 'integration'],
        "Integration Tests: API Endpoints"
    )
    
    # 6. Benchmarks - Performance Tests
    results['benchmarks'] = run_command(
        ['pytest', 'tests/benchmarks/test_agent_benchmarks.py', '-v', '-m', 'benchmark'],
        "Benchmarks: Performance Tests"
    )
    
    # 7. Coverage Report
    results['coverage'] = run_command(
        ['pytest', 'tests/agents/', '--cov=backend/agents', '--cov-report=term', '--cov-report=html'],
        "Coverage Report: All Agents"
    )
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    failed = total - passed
    
    for test_name, success in results.items():
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{test_name:30} {status}")
    
    print(f"\nTotal: {total} | Passed: {passed} | Failed: {failed}")
    print(f"Success Rate: {(passed/total*100):.1f}%")
    
    # Save results
    results_file = project_root / "test_results.json"
    with open(results_file, 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'results': results,
            'summary': {
                'total': total,
                'passed': passed,
                'failed': failed,
                'success_rate': round(passed/total*100, 1)
            }
        }, f, indent=2)
    
    print(f"\nResults saved to: {results_file}")
    print(f"Coverage report: {project_root}/htmlcov/index.html")
    print("="*70)
    
    # Exit with appropriate code
    sys.exit(0 if failed == 0 else 1)


if __name__ == '__main__':
    main()
