"""
pytest Configuration & Fixtures
================================

Shared fixtures for VERITAS test suite.
"""

import pytest
from pathlib import Path
from datetime import datetime
from typing import Dict, List
import tempfile
import shutil


# ============================================================================
# Pytest Markers
# ============================================================================

def pytest_configure(config):
    """Configure custom markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "ui: marks tests as UI tests"
    )
    config.addinivalue_line(
        "markers", "performance: marks tests as performance benchmarks"
    )
    config.addinivalue_line(
        "markers", "e2e: marks tests as end-to-end tests"
    )


# ============================================================================
# Fixtures: Test Data
# ============================================================================

@pytest.fixture
def sample_messages() -> List[Dict]:
    """Sample chat messages for testing"""
    return [
        {
            'role': 'user',
            'content': 'Was ist VERITAS?',
            'timestamp': '2025-10-09 14:20:00',
            'attachments': []
        },
        {
            'role': 'assistant',
            'content': '# VERITAS\n\nVERITAS ist ein **intelligentes RAG-System**.',
            'timestamp': '2025-10-09 14:20:05',
            'metadata': {
                'confidence': 92,
                'duration': 2.3,
                'sources_count': 3
            },
            'sources': [
                {'title': 'VERITAS Docs', 'page': 1, 'relevance': 0.95},
                {'title': 'API Reference', 'page': 5, 'relevance': 0.88},
                {'title': 'Architecture', 'page': 2, 'relevance': 0.82}
            ]
        },
        {
            'role': 'user',
            'content': 'Wie funktioniert die Agenten-Orchestrierung?',
            'timestamp': '2025-10-09 14:25:00',
            'attachments': [
                {'name': 'architecture.pdf', 'size': 1234567, 'path': '/tmp/arch.pdf'}
            ]
        },
        {
            'role': 'assistant',
            'content': 'Die Agenten-Orchestrierung erfolgt über...',
            'timestamp': '2025-10-09 14:25:12',
            'metadata': {
                'confidence': 88,
                'duration': 5.2,
                'sources_count': 5,
                'agents_used': ['orchestrator', 'core_components', 'pipeline_manager']
            },
            'sources': [
                {'title': 'Agent Documentation', 'page': 8, 'relevance': 0.92}
            ]
        }
    ]


@pytest.fixture
def sample_feedback_stats() -> Dict:
    """Sample feedback statistics"""
    return {
        'total_feedback': 150,
        'positive_count': 120,
        'negative_count': 20,
        'neutral_count': 10,
        'positive_ratio': 80.0,
        'average_rating': 4.2,
        'categories': {
            'accuracy': 45,
            'completeness': 38,
            'relevance': 42,
            'performance': 25
        }
    }


@pytest.fixture
def temp_export_dir():
    """Temporary directory for export tests"""
    temp_dir = Path(tempfile.mkdtemp(prefix="veritas_test_"))
    yield temp_dir
    # Cleanup
    if temp_dir.exists():
        shutil.rmtree(temp_dir)


@pytest.fixture
def sample_files(temp_export_dir):
    """Sample files for drag & drop tests"""
    files = []
    
    # Create test files
    test_files = [
        ('test_doc.pdf', b'%PDF-1.4 fake pdf content', 'application/pdf'),
        ('test_text.txt', b'Sample text content', 'text/plain'),
        ('test_data.json', b'{"key": "value"}', 'application/json'),
    ]
    
    for filename, content, mime_type in test_files:
        file_path = temp_export_dir / filename
        file_path.write_bytes(content)
        files.append({
            'name': filename,
            'path': str(file_path),
            'size': len(content),
            'mime_type': mime_type
        })
    
    return files


# ============================================================================
# Fixtures: Mock Backends
# ============================================================================

@pytest.fixture
def mock_database(mocker):
    """Mock database connection"""
    db_mock = mocker.MagicMock()
    db_mock.execute.return_value = mocker.MagicMock()
    db_mock.fetchall.return_value = []
    db_mock.fetchone.return_value = None
    db_mock.commit.return_value = None
    return db_mock


@pytest.fixture
def mock_feedback_api(mocker):
    """Mock Feedback API"""
    api_mock = mocker.MagicMock()
    api_mock.submit_feedback.return_value = {'success': True, 'feedback_id': 'test_id_123'}
    api_mock.get_stats.return_value = {
        'total_feedback': 150,
        'positive_ratio': 80.0
    }
    return api_mock


# ============================================================================
# Fixtures: Performance Testing
# ============================================================================

@pytest.fixture
def large_message_set() -> List[Dict]:
    """Generate 100 messages for performance testing"""
    messages = []
    for i in range(100):
        # User message
        messages.append({
            'role': 'user',
            'content': f'Test query {i+1}',
            'timestamp': f'2025-10-09 14:{i:02d}:00',
            'attachments': []
        })
        # Assistant message
        messages.append({
            'role': 'assistant',
            'content': f'# Response {i+1}\n\nThis is a **test response** with some content.',
            'timestamp': f'2025-10-09 14:{i:02d}:05',
            'metadata': {
                'confidence': 85 + (i % 15),
                'duration': 1.5 + (i % 5) * 0.5,
                'sources_count': 3 + (i % 5)
            },
            'sources': [
                {'title': f'Source {j+1}', 'page': j+1, 'relevance': 0.9 - j*0.1}
                for j in range(3)
            ]
        })
    return messages


# ============================================================================
# Fixtures: Configuration
# ============================================================================

@pytest.fixture
def test_config():
    """Test configuration"""
    return {
        'export': {
            'output_dir': './test_exports',
            'max_file_size': 50 * 1024 * 1024,  # 50 MB
        },
        'drag_drop': {
            'max_files': 10,
            'max_file_size': 50 * 1024 * 1024,
        },
        'performance': {
            'export_threshold_ms': 2000,  # Max 2s for 100 messages
            'render_threshold_ms': 500,   # Max 500ms for chat render
        }
    }


# ============================================================================
# Markers
# ============================================================================

def pytest_configure(config):
    """Register custom markers"""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "ui: marks tests requiring UI (Tkinter)"
    )
    config.addinivalue_line(
        "markers", "performance: marks tests for performance benchmarking"
    )
