#!/usr/bin/env python3
"""
Performance Benchmarks for All AI Agents

Measures execution time, memory usage, and throughput for all agents.
"""

import pytest
import asyncio
import time
import psutil
import os
from pathlib import Path
import sys
import json
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.agents.vector_chart_agent import VectorChartAgent
from backend.agents.presentation_canvas_agent import PresentationCanvasAgent
from backend.agents.geo_sub_agent import GeoSubAgent, CoordinateTransformer
from backend.agents.ai_image_generator import AIImageGenerator


class BenchmarkResult:
    """Container for benchmark results"""
    
    def __init__(self, name):
        self.name = name
        self.start_time = None
        self.end_time = None
        self.memory_before = None
        self.memory_after = None
        self.iterations = 0
    
    def start(self):
        """Start benchmark"""
        process = psutil.Process(os.getpid())
        self.memory_before = process.memory_info().rss / 1024 / 1024  # MB
        self.start_time = time.time()
    
    def end(self, iterations=1):
        """End benchmark"""
        self.end_time = time.time()
        process = psutil.Process(os.getpid())
        self.memory_after = process.memory_info().rss / 1024 / 1024  # MB
        self.iterations = iterations
    
    def get_stats(self):
        """Get benchmark statistics"""
        duration = self.end_time - self.start_time
        memory_used = self.memory_after - self.memory_before
        
        return {
            'name': self.name,
            'duration_seconds': round(duration, 3),
            'duration_per_iteration_ms': round((duration / self.iterations) * 1000, 2),
            'iterations': self.iterations,
            'throughput_per_second': round(self.iterations / duration, 2) if duration > 0 else 0,
            'memory_used_mb': round(memory_used, 2),
            'memory_before_mb': round(self.memory_before, 2),
            'memory_after_mb': round(self.memory_after, 2)
        }


class TestVectorChartAgentBenchmarks:
    """Benchmarks for VectorChartAgent"""
    
    @pytest.fixture
    def agent(self):
        return VectorChartAgent()
    
    @pytest.mark.benchmark
    @pytest.mark.asyncio
    async def test_benchmark_single_chart_generation(self, agent):
        """Benchmark single chart generation"""
        benchmark = BenchmarkResult("VectorChart: Single Bar Chart")
        
        benchmark.start()
        result = await agent.generate_chart(
            "Create a bar chart",
            template='bimschg_overview'
        )
        benchmark.end(iterations=1)
        
        stats = benchmark.get_stats()
        print(f"\n{json.dumps(stats, indent=2)}")
        
        assert result['success'] is True
        assert stats['duration_seconds'] < 5.0  # Should complete in < 5s
    
    @pytest.mark.benchmark
    @pytest.mark.asyncio
    async def test_benchmark_multiple_charts(self, agent):
        """Benchmark generating 10 charts"""
        benchmark = BenchmarkResult("VectorChart: 10 Charts")
        iterations = 10
        
        benchmark.start()
        for i in range(iterations):
            await agent.generate_chart(
                f"Chart {i}",
                template='bimschg_overview'
            )
        benchmark.end(iterations=iterations)
        
        stats = benchmark.get_stats()
        print(f"\n{json.dumps(stats, indent=2)}")
        
        assert stats['throughput_per_second'] > 0.5  # At least 0.5 charts/second
    
    @pytest.mark.benchmark
    @pytest.mark.asyncio
    async def test_benchmark_concurrent_generation(self, agent):
        """Benchmark concurrent chart generation"""
        benchmark = BenchmarkResult("VectorChart: 5 Concurrent")
        iterations = 5
        
        benchmark.start()
        tasks = [
            agent.generate_chart(f"Chart {i}", template='bimschg_overview')
            for i in range(iterations)
        ]
        results = await asyncio.gather(*tasks)
        benchmark.end(iterations=iterations)
        
        stats = benchmark.get_stats()
        print(f"\n{json.dumps(stats, indent=2)}")
        
        assert all(r['success'] for r in results)
        assert stats['duration_seconds'] < 10.0  # Concurrent should be faster


class TestPresentationCanvasAgentBenchmarks:
    """Benchmarks for PresentationCanvasAgent"""
    
    @pytest.fixture
    def agent(self):
        return PresentationCanvasAgent()
    
    @pytest.mark.benchmark
    @pytest.mark.asyncio
    async def test_benchmark_single_presentation(self, agent):
        """Benchmark single presentation generation"""
        benchmark = BenchmarkResult("Presentation: 2 Slides")
        
        benchmark.start()
        result = await agent.generate_presentation(
            "Create a 2-slide presentation about wind energy"
        )
        benchmark.end(iterations=1)
        
        stats = benchmark.get_stats()
        print(f"\n{json.dumps(stats, indent=2)}")
        
        assert result['success'] is True
        assert stats['duration_seconds'] < 10.0
    
    @pytest.mark.benchmark
    @pytest.mark.asyncio
    async def test_benchmark_vdl_rendering(self, agent):
        """Benchmark VDL rendering performance"""
        benchmark = BenchmarkResult("Presentation: 10 VDL Renders")
        iterations = 10
        
        vdl = {
            "slides": [
                {
                    "layout": "title_slide",
                    "elements": [
                        {
                            "type": "text",
                            "content": "Test",
                            "position": {"x": 480, "y": 360},
                            "properties": {"font_size": 44}
                        }
                    ]
                }
            ]
        }
        
        benchmark.start()
        for i in range(iterations):
            await agent.generate_from_vdl(vdl)
        benchmark.end(iterations=iterations)
        
        stats = benchmark.get_stats()
        print(f"\n{json.dumps(stats, indent=2)}")
        
        assert stats['throughput_per_second'] > 1.0  # At least 1 render/second


class TestGeoSubAgentBenchmarks:
    """Benchmarks for GeoSubAgent"""
    
    @pytest.fixture
    def agent(self):
        return GeoSubAgent()
    
    @pytest.fixture
    def transformer(self):
        return CoordinateTransformer()
    
    @pytest.mark.benchmark
    def test_benchmark_coordinate_transformation(self, transformer):
        """Benchmark coordinate transformation speed"""
        benchmark = BenchmarkResult("Geo: 1000 Coordinate Transforms")
        iterations = 1000
        
        benchmark.start()
        for i in range(iterations):
            transformer.utm33n_to_wgs84(400000 + i, 5800000 + i)
        benchmark.end(iterations=iterations)
        
        stats = benchmark.get_stats()
        print(f"\n{json.dumps(stats, indent=2)}")
        
        assert stats['throughput_per_second'] > 1000  # Should be very fast
    
    @pytest.mark.benchmark
    @pytest.mark.asyncio
    async def test_benchmark_geo_data_retrieval(self, agent):
        """Benchmark geo data retrieval"""
        benchmark = BenchmarkResult("Geo: Data Retrieval (100 features)")
        
        query = {'source': 'bimschg', 'limit': 100}
        
        benchmark.start()
        geo_data = await agent.get_geo_data(query)
        benchmark.end(iterations=1)
        
        stats = benchmark.get_stats()
        print(f"\n{json.dumps(stats, indent=2)}")
        
        assert geo_data['type'] == 'FeatureCollection'
        assert stats['duration_seconds'] < 2.0
    
    @pytest.mark.benchmark
    @pytest.mark.asyncio
    async def test_benchmark_map_generation(self, agent):
        """Benchmark map generation"""
        benchmark = BenchmarkResult("Geo: Map Generation")
        
        query = {'source': 'bimschg', 'limit': 50}
        geo_data = await agent.get_geo_data(query)
        
        benchmark.start()
        result = await agent.generate_map(geo_data, {'title': 'Test Map'})
        benchmark.end(iterations=1)
        
        stats = benchmark.get_stats()
        print(f"\n{json.dumps(stats, indent=2)}")
        
        assert result['success'] is True
        assert stats['duration_seconds'] < 5.0


class TestAIImageGeneratorBenchmarks:
    """Benchmarks for AIImageGenerator"""
    
    @pytest.fixture
    def agent(self):
        return AIImageGenerator(generator_type='swarmui')
    
    @pytest.mark.benchmark
    @pytest.mark.asyncio
    async def test_benchmark_image_generation(self, agent):
        """Benchmark image generation (placeholder)"""
        benchmark = BenchmarkResult("AIImage: Generation")
        
        benchmark.start()
        result = await agent.generate_image("A wind turbine")
        benchmark.end(iterations=1)
        
        stats = benchmark.get_stats()
        print(f"\n{json.dumps(stats, indent=2)}")
        
        assert result['success'] is True
        assert stats['duration_seconds'] < 3.0  # Placeholder should be fast
    
    @pytest.mark.benchmark
    @pytest.mark.asyncio
    async def test_benchmark_image_analysis(self, agent):
        """Benchmark image analysis"""
        benchmark = BenchmarkResult("AIImage: Analysis")
        
        # Generate test image
        gen_result = await agent.generate_image("Test")
        image_path = gen_result['image_path']
        
        benchmark.start()
        result = await agent.analyze_image(
            image_path=image_path,
            task='caption'
        )
        benchmark.end(iterations=1)
        
        stats = benchmark.get_stats()
        print(f"\n{json.dumps(stats, indent=2)}")
        
        assert result['success'] is True
        assert stats['duration_seconds'] < 2.0
    
    @pytest.mark.benchmark
    @pytest.mark.asyncio
    async def test_benchmark_batch_generation(self, agent):
        """Benchmark batch image generation"""
        benchmark = BenchmarkResult("AIImage: Batch 5 Images")
        iterations = 5
        
        prompts = [f"Image {i}" for i in range(iterations)]
        
        benchmark.start()
        results = await agent.batch_generate(prompts)
        benchmark.end(iterations=iterations)
        
        stats = benchmark.get_stats()
        print(f"\n{json.dumps(stats, indent=2)}")
        
        assert len(results) == iterations
        assert all(r['success'] for r in results)


@pytest.mark.benchmark
def test_save_benchmark_results():
    """Save all benchmark results to file"""
    results_file = Path(__file__).parent.parent / "benchmark_results.json"
    
    results = {
        "timestamp": datetime.now().isoformat(),
        "note": "Run with: pytest tests/benchmarks/test_agent_benchmarks.py -v -m benchmark"
    }
    
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nBenchmark results saved to: {results_file}")


if __name__ == '__main__':
    # Run benchmarks
    pytest.main([__file__, '-v', '-m', 'benchmark', '--tb=short'])
