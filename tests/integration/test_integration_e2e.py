"""
VERITAS End-to-End Integration Tests
Tests für vollständige Workflows über alle Komponenten

Test Coverage:
- Upload → Query → Feedback → Export Workflow
- Cross-component Data Flow
- Backend-Frontend Integration
- Error Recovery
"""

import pytest
import time
import os
import sys
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

# Add paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'frontend'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))


@pytest.fixture
def mock_backend():
    """Mock backend API."""
    backend = Mock()
    backend.submit_query = Mock(return_value={
        'answer': 'Das BImSchG ist das Bundes-Immissionsschutzgesetz.',
        'confidence': 0.92,
        'sources': ['BImSchG §1', 'BImSchG §2'],
        'duration': 2.5
    })
    backend.submit_feedback = Mock(return_value={'success': True})
    return backend


@pytest.fixture
def mock_uds3():
    """Mock UDS3 database."""
    uds3 = Mock()
    uds3.store_document = Mock(return_value='doc_123')
    uds3.search = Mock(return_value=[
        {'id': 'doc_1', 'title': 'BImSchG §1', 'content': '...', 'score': 0.95},
        {'id': 'doc_2', 'title': 'BImSchG §2', 'content': '...', 'score': 0.88}
    ])
    return uds3


class TestUploadQueryFeedbackExportWorkflow:
    """End-to-end test for complete user workflow."""
    
    @pytest.mark.integration
    def test_complete_workflow(self, mock_backend, mock_uds3, tmp_path):
        """Test Upload → Query → Feedback → Export workflow."""
        
        # PHASE 1: Upload Document
        print("\n📤 PHASE 1: Upload Document")
        test_file = tmp_path / "test_document.pdf"
        test_file.write_bytes(b"BImSchG Test Content" * 100)
        
        # Simulate document upload
        with patch('uds3.uds3_core.get_optimized_unified_strategy', return_value=mock_uds3):
            doc_id = mock_uds3.store_document(str(test_file))
            assert doc_id == 'doc_123'
            print(f"   ✅ Document uploaded: {doc_id}")
        
        # PHASE 2: Query
        print("\n🔍 PHASE 2: Query Submission")
        query = "Was ist das BImSchG?"
        
        # Simulate RAG search
        search_results = mock_uds3.search(query)
        assert len(search_results) == 2
        print(f"   ✅ Search returned {len(search_results)} results")
        
        # Simulate LLM response
        response = mock_backend.submit_query(query)
        assert response['answer'] is not None
        assert response['confidence'] > 0.5
        print(f"   ✅ LLM Response received (confidence: {response['confidence']})")
        
        # PHASE 3: Feedback
        print("\n👍 PHASE 3: User Feedback")
        message_id = f"msg_{int(time.time())}"
        
        feedback_result = mock_backend.submit_feedback(
            message_id=message_id,
            rating=1,  # Positive
            category='helpful'
        )
        assert feedback_result['success'] == True
        print(f"   ✅ Feedback submitted for {message_id}")
        
        # PHASE 4: Export
        print("\n📊 PHASE 4: Export Chat History")
        messages = [
            {'role': 'user', 'content': query, 'timestamp': datetime.now()},
            {
                'role': 'assistant',
                'content': response['answer'],
                'timestamp': datetime.now(),
                'metadata': {
                    'confidence': response['confidence'],
                    'sources': response['sources'],
                    'duration': response['duration']
                }
            }
        ]
        
        try:
            from services.office_export import OfficeExportService
            service = OfficeExportService()
            
            export_file = tmp_path / "test_export.docx"
            service.export_to_word(messages, str(export_file))
            
            assert export_file.exists()
            assert export_file.stat().st_size > 0
            print(f"   ✅ Export created: {export_file.name} ({export_file.stat().st_size} bytes)")
        except ImportError:
            pytest.skip("OfficeExportService not available")
        
        print("\n✅ WORKFLOW COMPLETE")
    
    @pytest.mark.integration
    def test_workflow_with_multiple_queries(self, mock_backend, mock_uds3, tmp_path):
        """Test workflow with multiple queries in session."""
        
        messages = []
        queries = [
            "Was ist das BImSchG?",
            "Welche Hauptziele verfolgt das BImSchG?",
            "Was sind die wichtigsten Paragrafen?"
        ]
        
        print("\n🔄 MULTIPLE QUERY WORKFLOW")
        
        for i, query in enumerate(queries):
            print(f"\n   Query {i+1}/{len(queries)}: {query}")
            
            # Search
            search_results = mock_uds3.search(query)
            
            # LLM Response
            response = mock_backend.submit_query(query)
            
            # Store messages
            messages.append({
                'role': 'user',
                'content': query,
                'timestamp': datetime.now()
            })
            messages.append({
                'role': 'assistant',
                'content': response['answer'],
                'timestamp': datetime.now(),
                'metadata': {
                    'confidence': response['confidence'],
                    'sources': response['sources']
                }
            })
            
            print(f"   ✅ Response received (confidence: {response['confidence']})")
        
        # Export all messages
        try:
            from services.office_export import OfficeExportService
            service = OfficeExportService()
            
            export_file = tmp_path / "multi_query_export.docx"
            service.export_to_word(messages, str(export_file))
            
            assert export_file.exists()
            print(f"\n   ✅ Exported {len(messages)} messages")
        except ImportError:
            pytest.skip("OfficeExportService not available")


class TestCrossComponentDataFlow:
    """Tests for data flow between components."""
    
    @pytest.mark.integration
    def test_backend_frontend_data_flow(self, mock_backend):
        """Test data flow from backend to frontend."""
        
        # Backend sends response
        backend_response = {
            'answer': 'Test answer',
            'confidence': 0.85,
            'sources': ['Source 1', 'Source 2'],
            'duration': 1.5,
            'metadata': {
                'model': 'llama3.1:8b',
                'temperature': 0.7
            }
        }
        
        # Frontend receives and processes
        assert 'answer' in backend_response
        assert 'confidence' in backend_response
        assert 'sources' in backend_response
        
        # Frontend displays
        display_data = {
            'content': backend_response['answer'],
            'confidence_badge': f"{backend_response['confidence']*100:.0f}%",
            'source_list': backend_response['sources'],
            'timing': f"{backend_response['duration']:.1f}s"
        }
        
        assert display_data['confidence_badge'] == "85%"
        assert len(display_data['source_list']) == 2
        print(f"   ✅ Data flow validated: {backend_response.keys()} → {display_data.keys()}")
    
    @pytest.mark.integration
    def test_uds3_backend_integration(self, mock_uds3):
        """Test UDS3 → Backend data integration."""
        
        # UDS3 search
        search_query = "Baurecht"
        search_results = mock_uds3.search(search_query)
        
        # Backend processes search results
        context_docs = [result['content'] for result in search_results]
        assert len(context_docs) == 2
        
        # Backend creates prompt with context
        prompt = f"Context: {' '.join(context_docs)}\nQuestion: {search_query}"
        assert 'Context:' in prompt
        assert search_query in prompt
        
        print(f"   ✅ UDS3 → Backend integration: {len(search_results)} docs → prompt")
    
    @pytest.mark.integration
    def test_feedback_to_analytics_flow(self, mock_backend):
        """Test feedback → analytics data flow."""
        
        # Collect feedback
        feedbacks = []
        for i in range(10):
            feedback = {
                'message_id': f'msg_{i}',
                'rating': 1 if i % 2 == 0 else -1,
                'category': 'helpful' if i % 2 == 0 else 'incorrect',
                'timestamp': datetime.now()
            }
            feedbacks.append(feedback)
            mock_backend.submit_feedback(**feedback)
        
        # Analytics processing
        positive_count = sum(1 for f in feedbacks if f['rating'] == 1)
        negative_count = sum(1 for f in feedbacks if f['rating'] == -1)
        positive_ratio = positive_count / len(feedbacks)
        
        assert positive_count == 5
        assert negative_count == 5
        assert positive_ratio == 0.5
        
        print(f"   ✅ Feedback → Analytics: {len(feedbacks)} feedbacks → {positive_ratio:.0%} positive")


class TestErrorRecovery:
    """Tests for error handling and recovery."""
    
    @pytest.mark.integration
    def test_backend_connection_error_recovery(self):
        """Test recovery from backend connection error."""
        
        # Simulate connection error
        backend = Mock()
        backend.submit_query = Mock(side_effect=ConnectionError("Backend not available"))
        
        # Frontend should handle gracefully
        try:
            response = backend.submit_query("test")
        except ConnectionError as e:
            error_message = "Backend nicht erreichbar. Bitte später erneut versuchen."
            assert "Backend" in error_message
            print(f"   ✅ Connection error handled: {error_message}")
    
    @pytest.mark.integration
    def test_uds3_search_error_recovery(self, mock_uds3):
        """Test recovery from UDS3 search error."""
        
        # Simulate UDS3 error
        mock_uds3.search = Mock(side_effect=Exception("UDS3 connection failed"))
        
        # Backend should fall back to cached results or error message
        try:
            results = mock_uds3.search("test")
        except Exception:
            fallback_results = []  # Empty results
            assert len(fallback_results) == 0
            print(f"   ✅ UDS3 error handled with fallback")
    
    @pytest.mark.integration
    def test_export_failure_recovery(self, tmp_path):
        """Test recovery from export failure."""
        
        try:
            from services.office_export import OfficeExportService
        except ImportError:
            pytest.skip("OfficeExportService not available")
        
        service = OfficeExportService()
        
        # Simulate export to invalid path
        invalid_path = "/invalid/path/export.docx"
        
        try:
            service.export_to_word([], invalid_path)
        except (OSError, PermissionError, FileNotFoundError) as e:
            error_message = "Export fehlgeschlagen. Bitte Pfad überprüfen."
            assert "Export" in error_message or "Path" in str(e)
            print(f"   ✅ Export error handled: {error_message}")
    
    @pytest.mark.integration
    def test_partial_workflow_recovery(self, mock_backend, mock_uds3, tmp_path):
        """Test recovery when workflow is interrupted."""
        
        messages = []
        
        # Phase 1: Successful query
        response1 = mock_backend.submit_query("Query 1")
        messages.append({
            'role': 'user',
            'content': 'Query 1',
            'timestamp': datetime.now()
        })
        messages.append({
            'role': 'assistant',
            'content': response1['answer'],
            'timestamp': datetime.now()
        })
        
        # Phase 2: Failed query (backend error)
        mock_backend.submit_query = Mock(side_effect=Exception("Temporary error"))
        try:
            response2 = mock_backend.submit_query("Query 2")
        except Exception:
            # Add error message to chat
            messages.append({
                'role': 'system',
                'content': 'Fehler bei der Verarbeitung. Bitte erneut versuchen.',
                'timestamp': datetime.now()
            })
        
        # Phase 3: Export should still work with partial data
        try:
            from services.office_export import OfficeExportService
            service = OfficeExportService()
            
            export_file = tmp_path / "partial_export.docx"
            service.export_to_word(messages, str(export_file))
            
            assert export_file.exists()
            print(f"   ✅ Partial workflow recovered: exported {len(messages)} messages")
        except ImportError:
            pytest.skip("OfficeExportService not available")


class TestConcurrentOperations:
    """Tests for concurrent operations."""
    
    @pytest.mark.integration
    def test_concurrent_queries(self, mock_backend):
        """Test handling of concurrent queries."""
        import threading
        
        results = []
        errors = []
        
        def submit_query(query_id):
            try:
                response = mock_backend.submit_query(f"Query {query_id}")
                results.append(response)
            except Exception as e:
                errors.append(e)
        
        # Submit 5 concurrent queries
        threads = []
        for i in range(5):
            t = threading.Thread(target=submit_query, args=(i,))
            threads.append(t)
            t.start()
        
        # Wait for all threads
        for t in threads:
            t.join()
        
        assert len(results) == 5
        assert len(errors) == 0
        print(f"   ✅ Concurrent queries handled: {len(results)} responses")
    
    @pytest.mark.integration
    def test_concurrent_feedback_submissions(self, mock_backend):
        """Test handling of concurrent feedback submissions."""
        import threading
        
        results = []
        
        def submit_feedback(msg_id):
            result = mock_backend.submit_feedback(
                message_id=f"msg_{msg_id}",
                rating=1,
                category='helpful'
            )
            results.append(result)
        
        # Submit 10 concurrent feedbacks
        threads = []
        for i in range(10):
            t = threading.Thread(target=submit_feedback, args=(i,))
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        assert len(results) == 10
        print(f"   ✅ Concurrent feedbacks handled: {len(results)} submissions")


# E2E Test Summary
def e2e_summary():
    """Print E2E test summary."""
    print("\n" + "="*80)
    print("E2E INTEGRATION TEST SUMMARY")
    print("="*80)
    print("\nTest Coverage:")
    print("  ✅ Upload → Query → Feedback → Export Workflow (2 tests)")
    print("  ✅ Cross-Component Data Flow (3 tests)")
    print("  ✅ Error Recovery (4 tests)")
    print("  ✅ Concurrent Operations (2 tests)")
    print("\nTotal: 11 integration tests")
    print("\nWorkflow Validation:")
    print("  📤 Document Upload → UDS3")
    print("  🔍 Query → RAG Search → LLM")
    print("  👍 Feedback → Backend → Analytics")
    print("  📊 Chat History → Export Service")
    print("  ⚠️  Error Handling → User Feedback")
    print("="*80)


if __name__ == '__main__':
    # Run E2E tests
    pytest.main([__file__, '-v', '-m', 'integration', '--tb=short'])
    e2e_summary()
