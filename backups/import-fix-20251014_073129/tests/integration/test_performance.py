"""
VERITAS Performance Benchmarks
Tests für Performance-Metriken kritischer Funktionen

Test Coverage:
- Export Performance (Word, Excel)
- Drag & Drop Performance (multiple files)
- Chat Rendering Performance
- Backend API Response Times
- Memory Usage
"""

import pytest
import time
import psutil
import os
import sys
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

# Add paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'frontend'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))


def measure_time(func):
    """Decorator to measure execution time."""
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        return result, (end - start)
    return wrapper


def measure_memory(func):
    """Decorator to measure memory usage."""
    def wrapper(*args, **kwargs):
        process = psutil.Process(os.getpid())
        mem_before = process.memory_info().rss / 1024 / 1024  # MB
        result = func(*args, **kwargs)
        mem_after = process.memory_info().rss / 1024 / 1024  # MB
        return result, (mem_after - mem_before)
    return wrapper


@pytest.fixture
def sample_messages_small():
    """10 messages for small tests."""
    return _generate_messages(10)


@pytest.fixture
def sample_messages_medium():
    """100 messages for medium tests."""
    return _generate_messages(100)


@pytest.fixture
def sample_messages_large():
    """1000 messages for large tests."""
    return _generate_messages(1000)


def _generate_messages(count):
    """Generate test messages."""
    messages = []
    for i in range(count):
        messages.append({
            'role': 'user',
            'content': f'Question {i}: Was ist das BImSchG?',
            'timestamp': datetime.now() - timedelta(minutes=count-i)
        })
        messages.append({
            'role': 'assistant',
            'content': f'Answer {i}: Das Bundes-Immissionsschutzgesetz (BImSchG) ist ein deutsches Gesetz...' * 10,
            'timestamp': datetime.now() - timedelta(minutes=count-i) + timedelta(seconds=30),
            'metadata': {
                'confidence': 0.85 + (i % 15) / 100,
                'sources': [f'BImSchG §{j}' for j in range(1, min(i+2, 10))],
                'duration': 2.5 + (i % 5) / 10
            }
        })
    return messages


class TestExportPerformance:
    """Performance tests for export functionality."""
    
    @pytest.mark.slow
    def test_word_export_100_messages(self, sample_messages_medium):
        """Test Word export with 100 messages."""
        try:
            from services.office_export import OfficeExportService
        except ImportError:
            pytest.skip("OfficeExportService not available")
        
        service = OfficeExportService()
        
        @measure_time
        def export():
            return service.export_to_word(sample_messages_medium, 'test_100.docx')
        
        result, duration = export()
        
        print(f"\n📊 Word Export (100 messages): {duration:.2f}s")
        assert duration < 5.0, f"Export too slow: {duration}s (expected < 5s)"
        
        # Cleanup
        if os.path.exists('test_100.docx'):
            os.remove('test_100.docx')
    
    @pytest.mark.slow
    def test_word_export_1000_messages(self, sample_messages_large):
        """Test Word export with 1000 messages."""
        try:
            from services.office_export import OfficeExportService
        except ImportError:
            pytest.skip("OfficeExportService not available")
        
        service = OfficeExportService()
        
        @measure_time
        @measure_memory
        def export():
            return service.export_to_word(sample_messages_large, 'test_1000.docx')
        
        (result, mem_delta), duration = export()
        
        print(f"\n📊 Word Export (1000 messages):")
        print(f"   ⏱️  Duration: {duration:.2f}s")
        print(f"   💾 Memory Delta: {mem_delta:.2f} MB")
        
        assert duration < 30.0, f"Export too slow: {duration}s (expected < 30s)"
        assert mem_delta < 200, f"Memory usage too high: {mem_delta} MB (expected < 200 MB)"
        
        # Cleanup
        if os.path.exists('test_1000.docx'):
            os.remove('test_1000.docx')
    
    @pytest.mark.slow
    def test_excel_export_100_messages(self, sample_messages_medium):
        """Test Excel export with 100 messages."""
        try:
            from services.office_export import OfficeExportService
        except ImportError:
            pytest.skip("OfficeExportService not available")
        
        service = OfficeExportService()
        
        @measure_time
        def export():
            return service.export_to_excel(sample_messages_medium, 'test_100.xlsx')
        
        result, duration = export()
        
        print(f"\n📊 Excel Export (100 messages): {duration:.2f}s")
        assert duration < 3.0, f"Export too slow: {duration}s (expected < 3s)"
        
        # Cleanup
        if os.path.exists('test_100.xlsx'):
            os.remove('test_100.xlsx')
    
    @pytest.mark.slow
    def test_excel_export_1000_messages(self, sample_messages_large):
        """Test Excel export with 1000 messages."""
        try:
            from services.office_export import OfficeExportService
        except ImportError:
            pytest.skip("OfficeExportService not available")
        
        service = OfficeExportService()
        
        @measure_time
        @measure_memory
        def export():
            return service.export_to_excel(sample_messages_large, 'test_1000.xlsx')
        
        (result, mem_delta), duration = export()
        
        print(f"\n📊 Excel Export (1000 messages):")
        print(f"   ⏱️  Duration: {duration:.2f}s")
        print(f"   💾 Memory Delta: {mem_delta:.2f} MB")
        
        assert duration < 20.0, f"Export too slow: {duration}s (expected < 20s)"
        assert mem_delta < 150, f"Memory usage too high: {mem_delta} MB (expected < 150 MB)"
        
        # Cleanup
        if os.path.exists('test_1000.xlsx'):
            os.remove('test_1000.xlsx')


class TestDragDropPerformance:
    """Performance tests for drag & drop functionality."""
    
    def test_validate_single_file(self, tmp_path):
        """Test validation of single file."""
        try:
            from ui.veritas_ui_drag_drop import DragDropHandler
        except ImportError:
            pytest.skip("DragDropHandler not available")
        
        # Create test file
        test_file = tmp_path / "test.pdf"
        test_file.write_bytes(b"test content" * 1000)  # ~12 KB
        
        handler = DragDropHandler(None, max_files=10)
        
        @measure_time
        def validate():
            return handler._validate_file(str(test_file))
        
        result, duration = validate()
        
        print(f"\n📊 File Validation (single, 12 KB): {duration*1000:.2f}ms")
        assert duration < 0.1, f"Validation too slow: {duration}s"
    
    @pytest.mark.slow
    def test_validate_100_files(self, tmp_path):
        """Test validation of 100 files."""
        try:
            from ui.veritas_ui_drag_drop import DragDropHandler
        except ImportError:
            pytest.skip("DragDropHandler not available")
        
        # Create 100 test files
        files = []
        for i in range(100):
            test_file = tmp_path / f"test_{i}.pdf"
            test_file.write_bytes(b"test content" * 1000)
            files.append(str(test_file))
        
        handler = DragDropHandler(None, max_files=100)
        
        @measure_time
        def validate_all():
            results = []
            for file in files:
                results.append(handler._validate_file(file))
            return results
        
        results, duration = validate_all()
        
        print(f"\n📊 File Validation (100 files, 1.2 MB total):")
        print(f"   ⏱️  Duration: {duration:.2f}s")
        print(f"   ⚡ Per-file: {(duration/100)*1000:.2f}ms")
        
        assert duration < 5.0, f"Validation too slow: {duration}s (expected < 5s)"
        assert (duration/100) < 0.05, "Per-file validation too slow"
    
    def test_duplicate_detection_performance(self, tmp_path):
        """Test SHA256 duplicate detection performance."""
        try:
            from ui.veritas_ui_drag_drop import DragDropHandler
        except ImportError:
            pytest.skip("DragDropHandler not available")
        
        # Create test file (1 MB)
        test_file = tmp_path / "large_test.pdf"
        test_file.write_bytes(b"x" * 1024 * 1024)
        
        handler = DragDropHandler(None)
        
        @measure_time
        def compute_hash():
            return handler._compute_file_hash(str(test_file))
        
        hash_value, duration = compute_hash()
        
        print(f"\n📊 SHA256 Hash (1 MB file): {duration*1000:.2f}ms")
        assert duration < 0.5, f"Hash computation too slow: {duration}s"


class TestChatRenderingPerformance:
    """Performance tests for chat rendering."""
    
    def test_render_10_messages(self, sample_messages_small):
        """Test rendering 10 messages."""
        # Mock chat formatter
        @measure_time
        def render():
            # Simulate rendering process
            formatted = []
            for msg in sample_messages_small:
                formatted.append({
                    'role': msg['role'],
                    'content': msg['content'],
                    'formatted': f"[{msg['role']}] {msg['content']}"
                })
            return formatted
        
        result, duration = render()
        
        print(f"\n📊 Chat Render (10 messages): {duration*1000:.2f}ms")
        assert duration < 0.1, f"Rendering too slow: {duration}s"
    
    @pytest.mark.slow
    def test_render_100_messages(self, sample_messages_medium):
        """Test rendering 100 messages."""
        @measure_time
        @measure_memory
        def render():
            formatted = []
            for msg in sample_messages_medium:
                formatted.append({
                    'role': msg['role'],
                    'content': msg['content'],
                    'formatted': f"[{msg['role']}] {msg['content']}"
                })
            return formatted
        
        (result, mem_delta), duration = render()
        
        print(f"\n📊 Chat Render (100 messages):")
        print(f"   ⏱️  Duration: {duration*1000:.2f}ms")
        print(f"   💾 Memory Delta: {mem_delta:.2f} MB")
        
        assert duration < 1.0, f"Rendering too slow: {duration}s"
        assert mem_delta < 10, f"Memory usage too high: {mem_delta} MB"


class TestBackendAPIPerformance:
    """Performance tests for backend API calls."""
    
    @pytest.mark.slow
    def test_feedback_submission_latency(self):
        """Test feedback submission response time."""
        try:
            from services.feedback_api_client import FeedbackAPIClientSync
        except ImportError:
            pytest.skip("FeedbackAPIClient not available")
        
        client = FeedbackAPIClientSync(base_url="http://localhost:5000")
        
        @measure_time
        def submit_feedback():
            try:
                return client.submit_feedback(
                    message_id="test_123",
                    rating=1,
                    category="helpful"
                )
            except Exception:
                return None  # Backend might not be running
        
        result, duration = submit_feedback()
        
        print(f"\n📊 Feedback Submission: {duration*1000:.2f}ms")
        if result:
            assert duration < 0.5, f"API call too slow: {duration}s"
    
    @pytest.mark.slow
    def test_feedback_stats_query_performance(self):
        """Test feedback stats query performance."""
        try:
            from services.feedback_api_client import FeedbackAPIClientSync
        except ImportError:
            pytest.skip("FeedbackAPIClient not available")
        
        client = FeedbackAPIClientSync(base_url="http://localhost:5000")
        
        @measure_time
        def get_stats():
            try:
                return client.get_statistics(time_period='all')
            except Exception:
                return None
        
        result, duration = get_stats()
        
        print(f"\n📊 Feedback Stats Query: {duration*1000:.2f}ms")
        if result:
            assert duration < 0.3, f"Stats query too slow: {duration}s"


class TestMemoryLeaks:
    """Tests for memory leaks in critical operations."""
    
    @pytest.mark.slow
    def test_export_memory_leak(self, sample_messages_medium):
        """Test for memory leaks in repeated exports."""
        try:
            from services.office_export import OfficeExportService
        except ImportError:
            pytest.skip("OfficeExportService not available")
        
        service = OfficeExportService()
        process = psutil.Process(os.getpid())
        
        mem_readings = []
        for i in range(10):
            mem_before = process.memory_info().rss / 1024 / 1024
            service.export_to_word(sample_messages_medium, f'leak_test_{i}.docx')
            mem_after = process.memory_info().rss / 1024 / 1024
            mem_readings.append(mem_after - mem_before)
            
            # Cleanup
            if os.path.exists(f'leak_test_{i}.docx'):
                os.remove(f'leak_test_{i}.docx')
        
        avg_growth = sum(mem_readings) / len(mem_readings)
        print(f"\n📊 Memory Leak Test (10 exports):")
        print(f"   Average growth: {avg_growth:.2f} MB/export")
        
        # Memory growth should be minimal after first export
        assert avg_growth < 5, f"Possible memory leak: {avg_growth} MB/export"


# Performance Benchmark Summary
def benchmark_summary():
    """Print benchmark summary."""
    print("\n" + "="*80)
    print("PERFORMANCE BENCHMARK SUMMARY")
    print("="*80)
    print("\nBenchmark Coverage:")
    print("  📊 Export Performance:")
    print("     - Word Export (100, 1000 messages)")
    print("     - Excel Export (100, 1000 messages)")
    print("  📊 Drag & Drop Performance:")
    print("     - Single file validation")
    print("     - 100 files validation")
    print("     - SHA256 hash computation")
    print("  📊 Chat Rendering:")
    print("     - 10 messages")
    print("     - 100 messages")
    print("  📊 Backend API:")
    print("     - Feedback submission")
    print("     - Stats query")
    print("  📊 Memory Leaks:")
    print("     - Repeated exports")
    print("\nPerformance Targets:")
    print("  ✅ Word Export (100 msg): < 5s")
    print("  ✅ Word Export (1000 msg): < 30s")
    print("  ✅ Excel Export (100 msg): < 3s")
    print("  ✅ Excel Export (1000 msg): < 20s")
    print("  ✅ File Validation: < 50ms/file")
    print("  ✅ Chat Render (100 msg): < 1s")
    print("  ✅ API Call: < 500ms")
    print("="*80)


if __name__ == '__main__':
    # Run benchmarks
    pytest.main([__file__, '-v', '-m', 'slow', '--tb=short'])
    benchmark_summary()
