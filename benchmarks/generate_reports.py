"""
Generate Benchmark Reports - Windows compatible
"""

import sys
import json
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load results
results_file = Path(__file__).parent.parent / "benchmark_results_veritas.json"

if not results_file.exists():
    print(f"Results file not found: {results_file}")
    sys.exit(1)

with open(results_file, encoding='utf-8') as f:
    data = json.load(f)

from benchmarks.report_generator import BenchmarkReportGenerator, ComparisonReportGenerator

# Generate Markdown Report
print("[REPORT] Generating Markdown report...")
gen = BenchmarkReportGenerator(data)
md = gen.generate_markdown_report()

report_md_path = Path(__file__).parent.parent / "benchmark_report.md"
with open(report_md_path, 'w', encoding='utf-8') as f:
    f.write(md)
print(f"  Saved: {report_md_path}")

# Generate HTML Report (with HTML-safe entities)
print("[REPORT] Generating HTML report...")
html = gen.generate_html_report()

report_html_path = Path(__file__).parent.parent / "benchmark_report.html"
with open(report_html_path, 'w', encoding='utf-8') as f:
    f.write(html)
print(f"  Saved: {report_html_path}")

# Summary Statistics
print("\n[SUMMARY] Benchmark Statistics:")
summary = data.get('summary', {})
print(f"  Total Benchmarks: {summary.get('total_benchmarks', 0)}")
print(f"  Passed: {summary.get('total_passed', 0)}")
print(f"  Failed: {summary.get('total_failed', 0)}")
print(f"  Pass Rate: {(summary.get('total_passed', 0) / max(summary.get('total_benchmarks', 1), 1) * 100):.1f}%")

print("\n[CATEGORIES] Results by category:")
for cat, stats in sorted(summary.get('by_category', {}).items()):
    print(f"  {cat.title():20} | Mean: {stats.get('mean', 0):8.2f}ms | Count: {stats.get('count', 0):3}")

print("\n[SUCCESS] Reports generated successfully!")
