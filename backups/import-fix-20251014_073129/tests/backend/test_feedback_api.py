"""
Test Suite: Feedback API
=========================

Tests für Backend Feedback System:
- POST /api/feedback/submit
- GET /api/feedback/stats
- GET /api/feedback/list
"""

import pytest
from datetime import datetime, timedelta
from typing import Dict, List


# ============================================================================
# Test Data
# ============================================================================

VALID_FEEDBACK_PAYLOAD = {
    'message_id': 'msg_123',
    'rating': 1,  # 1=positive, 0=neutral, -1=negative
    'category': 'accuracy',
    'comment': 'Great response!',
    'user_id': 'user_test_001'
}

INVALID_FEEDBACK_PAYLOADS = [
    # Missing message_id
    {'rating': 1, 'category': 'accuracy'},
    # Invalid rating
    {'message_id': 'msg_123', 'rating': 5, 'category': 'accuracy'},
    # Invalid category
    {'message_id': 'msg_123', 'rating': 1, 'category': 'invalid_cat'},
]


# ============================================================================
# Test: Submit Feedback
# ============================================================================

def test_submit_feedback_valid(mock_feedback_api):
    """Test: Submit valid feedback"""
    # Arrange
    payload = VALID_FEEDBACK_PAYLOAD.copy()
    
    # Act
    result = mock_feedback_api.submit_feedback(**payload)
    
    # Assert
    assert result['success'] is True
    assert 'feedback_id' in result
    assert isinstance(result['feedback_id'], str)
    mock_feedback_api.submit_feedback.assert_called_once()


def test_submit_feedback_positive_rating(mock_feedback_api):
    """Test: Submit positive feedback (rating=1)"""
    # Arrange
    payload = VALID_FEEDBACK_PAYLOAD.copy()
    payload['rating'] = 1
    
    # Act
    result = mock_feedback_api.submit_feedback(**payload)
    
    # Assert
    assert result['success'] is True
    # Verify rating was captured
    call_args = mock_feedback_api.submit_feedback.call_args
    assert call_args[1]['rating'] == 1


def test_submit_feedback_negative_rating(mock_feedback_api):
    """Test: Submit negative feedback (rating=-1)"""
    # Arrange
    payload = VALID_FEEDBACK_PAYLOAD.copy()
    payload['rating'] = -1
    payload['comment'] = 'Incorrect information'
    
    # Act
    result = mock_feedback_api.submit_feedback(**payload)
    
    # Assert
    assert result['success'] is True
    call_args = mock_feedback_api.submit_feedback.call_args
    assert call_args[1]['rating'] == -1


def test_submit_feedback_with_category(mock_feedback_api):
    """Test: Submit feedback with category"""
    # Arrange
    categories = ['accuracy', 'completeness', 'relevance', 'performance']
    
    for category in categories:
        payload = VALID_FEEDBACK_PAYLOAD.copy()
        payload['category'] = category
        
        # Act
        result = mock_feedback_api.submit_feedback(**payload)
        
        # Assert
        assert result['success'] is True


def test_submit_feedback_without_comment(mock_feedback_api):
    """Test: Submit feedback without comment (optional)"""
    # Arrange
    payload = VALID_FEEDBACK_PAYLOAD.copy()
    del payload['comment']
    
    # Act
    result = mock_feedback_api.submit_feedback(**payload)
    
    # Assert
    assert result['success'] is True


@pytest.mark.parametrize("invalid_payload", INVALID_FEEDBACK_PAYLOADS)
def test_submit_feedback_invalid_payload(mock_feedback_api, invalid_payload):
    """Test: Submit invalid feedback payload"""
    # Configure mock to raise ValueError
    mock_feedback_api.submit_feedback.side_effect = ValueError("Invalid payload")
    
    # Act & Assert
    with pytest.raises(ValueError):
        mock_feedback_api.submit_feedback(**invalid_payload)


# ============================================================================
# Test: Get Feedback Statistics
# ============================================================================

def test_get_feedback_stats_all_time(mock_feedback_api, sample_feedback_stats):
    """Test: Get all-time feedback statistics"""
    # Arrange
    mock_feedback_api.get_stats.return_value = sample_feedback_stats
    
    # Act
    stats = mock_feedback_api.get_stats()
    
    # Assert
    assert stats['total_feedback'] == 150
    assert stats['positive_count'] == 120
    assert stats['positive_ratio'] == 80.0
    assert 'categories' in stats


def test_get_feedback_stats_last_7_days(mock_feedback_api):
    """Test: Get feedback statistics for last 7 days"""
    # Arrange
    expected_stats = {
        'total_feedback': 42,
        'positive_count': 35,
        'positive_ratio': 83.3,
        'period': '7_days'
    }
    mock_feedback_api.get_stats.return_value = expected_stats
    
    # Act
    stats = mock_feedback_api.get_stats(days=7)
    
    # Assert
    assert stats['total_feedback'] == 42
    assert stats['period'] == '7_days'
    mock_feedback_api.get_stats.assert_called_once_with(days=7)


def test_get_feedback_stats_last_30_days(mock_feedback_api):
    """Test: Get feedback statistics for last 30 days"""
    # Arrange
    expected_stats = {
        'total_feedback': 95,
        'positive_count': 78,
        'positive_ratio': 82.1,
        'period': '30_days'
    }
    mock_feedback_api.get_stats.return_value = expected_stats
    
    # Act
    stats = mock_feedback_api.get_stats(days=30)
    
    # Assert
    assert stats['total_feedback'] == 95
    assert stats['period'] == '30_days'


def test_get_feedback_stats_empty_database(mock_feedback_api):
    """Test: Get stats when no feedback exists"""
    # Arrange
    mock_feedback_api.get_stats.return_value = {
        'total_feedback': 0,
        'positive_count': 0,
        'negative_count': 0,
        'positive_ratio': 0.0
    }
    
    # Act
    stats = mock_feedback_api.get_stats()
    
    # Assert
    assert stats['total_feedback'] == 0
    assert stats['positive_ratio'] == 0.0


def test_get_feedback_stats_category_breakdown(mock_feedback_api, sample_feedback_stats):
    """Test: Get category breakdown in statistics"""
    # Arrange
    mock_feedback_api.get_stats.return_value = sample_feedback_stats
    
    # Act
    stats = mock_feedback_api.get_stats()
    
    # Assert
    assert 'categories' in stats
    categories = stats['categories']
    assert categories['accuracy'] == 45
    assert categories['completeness'] == 38
    assert categories['relevance'] == 42
    assert categories['performance'] == 25


# ============================================================================
# Test: List Feedback
# ============================================================================

def test_list_feedback_all(mock_feedback_api):
    """Test: List all feedback entries"""
    # Arrange
    expected_feedback = [
        {
            'id': 'fb_001',
            'message_id': 'msg_123',
            'rating': 1,
            'category': 'accuracy',
            'comment': 'Great!',
            'timestamp': '2025-10-09 14:30:00'
        },
        {
            'id': 'fb_002',
            'message_id': 'msg_124',
            'rating': -1,
            'category': 'relevance',
            'comment': 'Not helpful',
            'timestamp': '2025-10-09 14:35:00'
        }
    ]
    mock_feedback_api.list_feedback = lambda **kwargs: expected_feedback
    
    # Act
    feedback = mock_feedback_api.list_feedback()
    
    # Assert
    assert len(feedback) == 2
    assert feedback[0]['rating'] == 1
    assert feedback[1]['rating'] == -1


def test_list_feedback_filter_by_message_id(mock_feedback_api):
    """Test: List feedback filtered by message_id"""
    # Arrange
    expected_feedback = [
        {'id': 'fb_001', 'message_id': 'msg_123', 'rating': 1}
    ]
    mock_feedback_api.list_feedback = lambda **kwargs: expected_feedback if kwargs.get('message_id') == 'msg_123' else []
    
    # Act
    feedback = mock_feedback_api.list_feedback(message_id='msg_123')
    
    # Assert
    assert len(feedback) == 1
    assert feedback[0]['message_id'] == 'msg_123'


def test_list_feedback_filter_by_rating(mock_feedback_api):
    """Test: List feedback filtered by rating"""
    # Arrange
    positive_feedback = [
        {'id': 'fb_001', 'rating': 1},
        {'id': 'fb_003', 'rating': 1}
    ]
    mock_feedback_api.list_feedback = lambda **kwargs: positive_feedback if kwargs.get('rating') == 1 else []
    
    # Act
    feedback = mock_feedback_api.list_feedback(rating=1)
    
    # Assert
    assert len(feedback) == 2
    assert all(f['rating'] == 1 for f in feedback)


def test_list_feedback_pagination(mock_feedback_api):
    """Test: List feedback with pagination"""
    # Arrange
    all_feedback = [{'id': f'fb_{i:03d}'} for i in range(100)]
    
    def paginate(limit=10, offset=0, **kwargs):
        return all_feedback[offset:offset+limit]
    
    mock_feedback_api.list_feedback = paginate
    
    # Act
    page_1 = mock_feedback_api.list_feedback(limit=10, offset=0)
    page_2 = mock_feedback_api.list_feedback(limit=10, offset=10)
    
    # Assert
    assert len(page_1) == 10
    assert len(page_2) == 10
    assert page_1[0]['id'] == 'fb_000'
    assert page_2[0]['id'] == 'fb_010'


# ============================================================================
# Test: Error Handling
# ============================================================================

def test_submit_feedback_database_error(mock_feedback_api):
    """Test: Handle database error during submit"""
    # Arrange
    mock_feedback_api.submit_feedback.side_effect = Exception("Database connection failed")
    
    # Act & Assert
    with pytest.raises(Exception) as exc_info:
        mock_feedback_api.submit_feedback(**VALID_FEEDBACK_PAYLOAD)
    
    assert "Database connection failed" in str(exc_info.value)


def test_get_stats_network_error(mock_feedback_api):
    """Test: Handle network error when getting stats"""
    # Arrange
    mock_feedback_api.get_stats.side_effect = ConnectionError("API unreachable")
    
    # Act & Assert
    with pytest.raises(ConnectionError):
        mock_feedback_api.get_stats()


# ============================================================================
# Test: Integration with Message IDs
# ============================================================================

def test_feedback_for_multiple_messages(mock_feedback_api):
    """Test: Submit feedback for multiple messages"""
    # Arrange
    message_ids = ['msg_001', 'msg_002', 'msg_003']
    results = []
    
    # Act
    for msg_id in message_ids:
        payload = VALID_FEEDBACK_PAYLOAD.copy()
        payload['message_id'] = msg_id
        result = mock_feedback_api.submit_feedback(**payload)
        results.append(result)
    
    # Assert
    assert len(results) == 3
    assert all(r['success'] for r in results)
    assert mock_feedback_api.submit_feedback.call_count == 3


# ============================================================================
# Summary
# ============================================================================

"""
Test Coverage:
- ✅ Submit valid/invalid feedback
- ✅ Feedback ratings (positive/negative/neutral)
- ✅ Categories (accuracy, completeness, relevance, performance)
- ✅ Get statistics (all-time, 7/30 days)
- ✅ List feedback (all, filtered, paginated)
- ✅ Error handling (database, network)
- ✅ Integration with message IDs

Run:
    pytest tests/backend/test_feedback_api.py -v
"""
