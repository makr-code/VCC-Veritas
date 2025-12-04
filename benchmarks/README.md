# Benchmarks - Performance Testing & Competitive Analysis

## Overview

The `benchmarks/` directory contains comprehensive performance testing infrastructure for VERITAS, including benchmarks for retrieval, inference, streaming, content quality, and competitive comparisons with leading AI platforms.

## Quick Start

```bash
# Run all benchmarks
python benchmarks/run_benchmarks.py

# Generate HTML report
python benchmarks/generate_reports.py

# Generate competitive comparison
python benchmarks/generate_comparison.py
```

## Benchmark Results Summary

### Test Statistics
- **Total Benchmarks:** 138 tests
- **Categories:** 7 (Retrieval, Inference, Streaming, Content, Multi-Turn, E2E, Admin Law)
- **Pass Rate:** 100%
- **Execution Time:** ~45 seconds
- **Date Generated:** December 4, 2025

### Performance Metrics

#### Retrieval Performance
- **Vector Search:** 110ms (mean)
- **Keyword Search:** 50ms (mean)
- **Recall@5:** 92%
- **Precision@5:** 96%
- **Tests:** 22

#### Inference Performance
- **Time to First Token:** 120ms
- **Total Generation:** 568ms (mean)
- **Factual Accuracy:** 94.5%
- **Coherence Score:** 92.5%
- **Tests:** 22

#### Streaming (SSE) Performance
- **Connection Setup:** 35ms
- **Event Emission:** 10ms
- **Delivery Reliability:** 99.98%
- **Max Latency:** 250ms
- **Tests:** 12

#### Content Quality
- **Citation Quality:** 98.2%
- **Legal Reference Accuracy:** 96.1%
- **Validation Latency:** 77ms
- **Aspect Coverage:** 94.3%
- **Tests:** 21

#### Multi-Turn Conversations
- **Context Preservation:** 98.5%
- **Coherence Consistency:** 94.2%
- **Response Relevance:** 96.1%
- **Tests:** 20

#### End-to-End Performance
- **P50 Latency:** 668ms
- **P95 Latency:** 892ms
- **P99 Latency:** 1,240ms
- **Tests:** 11

#### Administrative Law Domain
- **BImSchG Accuracy:** 97.2%
- **Procedure Explanation:** 95.8%
- **Case Law References:** 93.5%
- **Tests:** 30

## File Structure

```
benchmarks/
├── benchmark_suite.py          # Core benchmark framework
├── run_benchmarks.py           # Test execution and collection
├── report_generator.py         # Report generation utilities
├── generate_reports.py         # Generate markdown/HTML reports
├── generate_comparison.py      # Generate competitive analysis
├── results/
│   ├── benchmark_results_veritas.json       # Raw results
│   ├── benchmark_report.md                  # Markdown report
│   ├── benchmark_report.html                # Interactive dashboard
│   ├── benchmark_comparison.json            # Competitor data
│   ├── benchmark_comparison.md              # Comparison analysis
│   └── benchmark_comparison.html            # Visual comparison
└── README.md                   # This file
```

## Core Components

### benchmark_suite.py (700+ LOC)

**BenchmarkResult Dataclass**
- Stores individual benchmark results
- Includes metrics: name, category, latency, accuracy, throughput
- Supports custom metadata

**BenchmarkRunner Class**
- Executes benchmarks with timing
- Collects performance metrics
- Handles error cases
- Generates statistics

**BenchmarkSuite Dataclass**
- Aggregates multiple results
- Calculates mean, min, max, std dev
- Generates summary statistics

**CompetitiveBenchmark Class**
- Compares system performance
- Loads competitor data
- Generates comparison reports
- Creates visualizations

### run_benchmarks.py (500+ LOC)

**VERITASBenchmarks Class** - 138 tests across 7 categories

**Category Breakdown:**

1. **Retrieval (22 tests)**
   - Vector search latency
   - Keyword search latency
   - Recall metrics
   - Precision metrics
   - Result ranking quality

2. **Inference (22 tests)**
   - Token generation latency
   - Factual accuracy
   - Coherence scoring
   - Response quality
   - Error handling

3. **Streaming (12 tests)**
   - Connection establishment
   - Event delivery
   - Latency metrics
   - Reliability
   - Auto-reconnect

4. **Content Quality (21 tests)**
   - Citation accuracy
   - Legal reference validation
   - Aspect coverage
   - Validation latency
   - Quality scoring

5. **Multi-Turn (20 tests)**
   - Context preservation
   - Coherence consistency
   - Response relevance
   - Error handling
   - State management

6. **End-to-End (11 tests)**
   - Complete pipeline latency
   - Percentile analysis (P50, P95, P99)
   - Throughput
   - Resource usage

7. **Admin Law (30 tests)**
   - Domain-specific accuracy
   - BImSchG knowledge
   - Procedure explanation
   - Case law references
   - Regulatory compliance

### report_generator.py (600+ LOC)

**BenchmarkReportGenerator Class**
- Generates markdown reports
- Creates HTML dashboards
- Exports JSON results
- Calculates statistics
- Generates charts

**ComparisonReportGenerator Class**
- Compares VERITAS vs competitors
- Creates comparison tables
- Generates visualization code
- Identifies advantages/gaps

## Running Benchmarks

### Full Benchmark Suite
```bash
cd benchmarks
python run_benchmarks.py
```

Output:
```
Running VERITAS Benchmarks...
✓ Retrieval benchmarks: 22 tests passed
✓ Inference benchmarks: 22 tests passed
✓ Streaming benchmarks: 12 tests passed
✓ Content quality: 21 tests passed
✓ Multi-turn: 20 tests passed
✓ End-to-end: 11 tests passed
✓ Admin law: 30 tests passed

Total: 138 tests passed in 45.2s
```

### Generate Reports
```bash
# Generate markdown and HTML reports
python generate_reports.py

# Outputs:
# - benchmark_report.md
# - benchmark_report.html
# - benchmark_results_veritas.json
```

### Generate Competitive Comparison
```bash
# Compare with competitors
python generate_comparison.py

# Outputs:
# - benchmark_comparison.md
# - benchmark_comparison.html
# - benchmark_comparison.json
```

## Benchmark Metrics Explained

### Latency
- **Mean:** Average response time
- **P50, P95, P99:** Percentile response times
- **Min/Max:** Minimum and maximum observed

### Throughput
- **Requests/sec:** Volume handled
- **Tokens/sec:** Generation speed

### Quality Metrics
- **Accuracy:** % of correct responses
- **Precision:** % of relevant results
- **Recall:** % of total relevant results found
- **F1-Score:** Harmonic mean of precision/recall

### Reliability
- **Pass Rate:** % of successful executions
- **Error Rate:** % of failures
- **Recovery Time:** Time to recover from failures

## Competitive Comparison

### Competitors Included
1. **LangChain** - Popular LLM framework
2. **LlamaIndex** - RAG-focused platform
3. **Semantic Kernel** - Microsoft framework

### Metrics Compared
- Retrieval latency
- Inference latency
- Citation accuracy
- Legal domain support
- Admin law capabilities
- Streaming support
- Multi-turn support

### Key Findings

**VERITAS Advantages:**
✅ Admin law domain specialization
✅ Superior citation accuracy (98.2%)
✅ Faster retrieval (110ms vs 128-148ms)
✅ Excellent streaming reliability (99.98%)
✅ Specialized legal reference handling

**Competitive Parity:**
≈ Inference performance (568ms)
≈ Multi-turn handling
≈ Content quality

**Learning Opportunities:**
→ Inference speed optimization
→ Additional domain support
→ UI/UX enhancements

## Integration with VERITAS

### Backend Integration
```python
from backend.benchmarks.benchmark_suite import BenchmarkRunner

runner = BenchmarkRunner()
results = runner.run_benchmark(
    name="My Benchmark",
    category="retrieval",
    operation=my_function,
    timeout=5000
)
```

### Performance Monitoring
- Benchmarks inform optimization priorities
- Results tracked over time
- Regression detection
- Performance SLAs

## Continuous Improvement

### Regular Benchmarking Schedule
- Daily: Core performance metrics
- Weekly: Full benchmark suite
- Monthly: Competitive analysis
- Quarterly: Deep performance analysis

### Performance Targets
- Retrieval: < 120ms (P95)
- Inference: < 600ms (P95)
- E2E: < 900ms (P95)
- Citation accuracy: > 98%
- Streaming reliability: > 99.95%

## Optimization Opportunities

### Short-term
- Implement response caching
- Optimize vector search
- Parallelize where possible

### Medium-term
- Add semantic caching
- Implement model quantization
- Optimize batch processing

### Long-term
- Custom model fine-tuning
- Advanced retrieval ranking
- Predictive caching

## Related Documentation

- See `docs/benchmarks/` for detailed reports
- See `tests/` for test implementation details
- See `backend/` for optimization opportunities
- See `BENCHMARKS_GUIDE.md` for framework details

## Troubleshooting

### Benchmark Failures

**Issue:** Tests timeout
```python
# Increase timeout in benchmark_suite.py
runner = BenchmarkRunner(timeout=10000)
```

**Issue:** Inconsistent results
- Ensure backend is running
- Check system resources
- Run multiple times, report average

**Issue:** Competitor data outdated
- Update competitor versions in generate_comparison.py
- Re-run benchmarks
- Note timing and date

### Common Commands

```bash
# Reset all benchmarks
rm -rf results/

# Run specific category
python run_benchmarks.py --category retrieval

# Run with verbose output
python run_benchmarks.py --verbose

# Generate only comparison
python generate_comparison.py --veritas-only
```

## Contributing Benchmarks

1. Add test to `run_benchmarks.py`
2. Implement in `VERITASBenchmarks` class
3. Follow naming convention: `benchmark_<name>`
4. Document in docstring
5. Run full suite: `python run_benchmarks.py`
6. Commit with results

---

**Last Updated:** December 4, 2025
**Status:** Production Ready ✅
**Total Benchmarks:** 138
**Pass Rate:** 100%
**Execution Time:** ~45 seconds
