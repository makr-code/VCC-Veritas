"""
Unit Tests für WebSocket Router

Tests für alle WebSocket-Endpoints:
- /ws/search - Vector Search
- /ws/adapter/status - Adapter Status
- /ws/logs - Log Streaming
- /ws/graph/traverse - Graph Traversal
"""

import pytest
import json
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch

# Mock backend.app
from backend.app import app


@pytest.fixture
def client():
    """Test Client"""
    return TestClient(app)


class TestWebSocketSearch:
    """
    Tests für /ws/search Endpoint
    """
    
    def test_websocket_search_success(self, client):
        """
        Test erfolgreiche Vector Search via WebSocket
        """
        with patch('backend.adapters.adapter_factory.get_database_adapter') as mock_adapter:
            # Mock Adapter Response
            mock_adapter.return_value = AsyncMock()
            mock_adapter.return_value.vector_search = AsyncMock(return_value=[
                {
                    "id": "doc1",
                    "content": "Machine learning tutorial",
                    "score": 0.95
                },
                {
                    "id": "doc2",
                    "content": "Deep learning guide",
                    "score": 0.88
                }
            ])
            
            with client.websocket_connect("/api/v3/ws/search?client_id=test_client") as websocket:
                # Receive welcome message
                welcome = websocket.receive_json()
                assert welcome["type"] == "connected"
                assert welcome["client_id"] == "test_client"
                
                # Send search query
                websocket.send_json({
                    "action": "search",
                    "query": "machine learning",
                    "top_k": 5,
                    "collection": "documents"
                })
                
                # Receive search_started
                started = websocket.receive_json()
                assert started["type"] == "search_started"
                assert started["query"] == "machine learning"
                
                # Receive results
                results = []
                for _ in range(2):
                    result = websocket.receive_json()
                    if result["type"] == "result":
                        results.append(result)
                
                assert len(results) == 2
                assert results[0]["data"]["id"] == "doc1"
                assert results[0]["score"] == 0.95
                
                # Receive search_complete
                complete = websocket.receive_json()
                assert complete["type"] == "search_complete"
                assert complete["total_results"] == 2
                assert "duration_ms" in complete
    
    def test_websocket_search_missing_query(self, client):
        """
        Test Error bei fehlender Query
        """
        with client.websocket_connect("/api/v3/ws/search?client_id=test_client") as websocket:
            # Welcome
            websocket.receive_json()
            
            # Send incomplete request
            websocket.send_json({
                "action": "search",
                "top_k": 5
                # Missing "query"
            })
            
            # Receive error
            error = websocket.receive_json()
            assert error["type"] == "error"
            assert "Missing required field: query" in error["message"]
    
    def test_websocket_ping_pong(self, client):
        """
        Test Ping/Pong Keep-Alive
        """
        with client.websocket_connect("/api/v3/ws/search?client_id=test_client") as websocket:
            # Welcome
            websocket.receive_json()
            
            # Send ping
            websocket.send_json({"action": "ping"})
            
            # Receive pong
            pong = websocket.receive_json()
            assert pong["type"] == "pong"
            assert "timestamp" in pong


class TestWebSocketAdapterStatus:
    """
    Tests für /ws/adapter/status Endpoint
    """
    
    @pytest.mark.asyncio
    async def test_websocket_status_updates(self, client):
        """
        Test periodische Status-Updates
        """
        with patch('backend.adapters.adapter_factory.get_database_adapter') as mock_adapter, \
             patch('backend.adapters.adapter_factory.is_themisdb_available') as mock_themis, \
             patch('backend.adapters.adapter_factory.is_uds3_available') as mock_uds3:
            
            # Mock Availability
            mock_themis.return_value = True
            mock_uds3.return_value = False
            
            # Mock Adapter
            mock_adapter_instance = AsyncMock()
            mock_adapter_instance.get_stats = MagicMock(return_value={
                "query_count": 100,
                "avg_latency_ms": 45.2,
                "success_rate": 0.95
            })
            mock_adapter.return_value = mock_adapter_instance
            
            with client.websocket_connect("/api/v3/ws/adapter/status?client_id=test&interval=1") as websocket:
                # Connected
                connected = websocket.receive_json()
                assert connected["type"] == "connected"
                assert connected["update_interval_seconds"] == 1
                
                # Receive status update
                status = websocket.receive_json()
                assert status["type"] == "status_update"
                assert status["current_adapter"] == "themis"
                assert status["themis"]["available"] is True
                assert status["uds3"]["available"] is False
                assert "active_websocket_connections" in status


class TestWebSocketLogs:
    """
    Tests für /ws/logs Endpoint
    """
    
    def test_websocket_log_streaming(self, client):
        """
        Test Log-Streaming
        """
        with client.websocket_connect("/api/v3/ws/logs?client_id=test&log_level=INFO") as websocket:
            # Connected
            connected = websocket.receive_json()
            assert connected["type"] == "connected"
            assert connected["log_level"] == "INFO"
            
            # Log-Nachrichten werden asynchron gesendet
            # Test nur Connection
            assert websocket.client_state.name == "CONNECTED"
    
    def test_websocket_log_level_change(self, client):
        """
        Test dynamische Log-Level-Änderung
        """
        with client.websocket_connect("/api/v3/ws/logs?client_id=test&log_level=INFO") as websocket:
            # Connected
            websocket.receive_json()
            
            # Change log level
            websocket.send_json({
                "action": "change_level",
                "level": "DEBUG"
            })
            
            # Receive confirmation
            response = websocket.receive_json()
            assert response["type"] == "info"
            assert "DEBUG" in response["message"]


class TestWebSocketGraphTraverse:
    """
    Tests für /ws/graph/traverse Endpoint
    """
    
    def test_websocket_graph_traversal(self, client):
        """
        Test Graph Traversal via WebSocket
        """
        with patch('backend.adapters.adapter_factory.get_database_adapter') as mock_adapter:
            # Mock Graph Traversal Response
            mock_adapter.return_value = AsyncMock()
            mock_adapter.return_value.graph_traverse = AsyncMock(return_value={
                "vertices": [
                    {"_key": "doc1", "label": "Document"},
                    {"_key": "doc2", "label": "Document"}
                ],
                "edges": [
                    {"_from": "doc1", "_to": "doc2", "type": "cites"}
                ]
            })
            
            with client.websocket_connect("/api/v3/ws/graph/traverse?client_id=test") as websocket:
                # Welcome
                welcome = websocket.receive_json()
                assert welcome["type"] == "connected"
                
                # Send traversal request
                websocket.send_json({
                    "action": "traverse",
                    "start_vertex": "doc1",
                    "edge_collection": "citations",
                    "max_depth": 2
                })
                
                # Receive traversal_started
                started = websocket.receive_json()
                assert started["type"] == "traversal_started"
                assert started["start_vertex"] == "doc1"
                
                # Receive nodes
                nodes = []
                for _ in range(2):
                    node = websocket.receive_json()
                    if node["type"] == "node":
                        nodes.append(node)
                
                assert len(nodes) == 2
                
                # Receive edge
                edge = websocket.receive_json()
                assert edge["type"] == "edge"
                
                # Receive traversal_complete
                complete = websocket.receive_json()
                assert complete["type"] == "traversal_complete"
                assert complete["total_nodes"] == 2
                assert complete["total_edges"] == 1


class TestWebSocketConnectionManager:
    """
    Tests für ConnectionManager
    """
    
    def test_multiple_connections_same_client(self, client):
        """
        Test mehrere Verbindungen für denselben Client
        """
        with client.websocket_connect("/api/v3/ws/search?client_id=multi_client") as ws1, \
             client.websocket_connect("/api/v3/ws/search?client_id=multi_client") as ws2:
            
            # Beide sollten connected sein
            assert ws1.client_state.name == "CONNECTED"
            assert ws2.client_state.name == "CONNECTED"
            
            # Welcome messages
            ws1.receive_json()
            ws2.receive_json()
    
    def test_connection_count_endpoint(self, client):
        """
        Test /ws/connections Monitoring-Endpoint
        """
        with client.websocket_connect("/api/v3/ws/search?client_id=test1") as ws1, \
             client.websocket_connect("/api/v3/ws/search?client_id=test2") as ws2:
            
            # Query connection count
            response = client.get("/api/v3/ws/connections")
            
            assert response.status_code == 200
            data = response.json()
            assert data["total_connections"] >= 2
            assert data["active_clients"] >= 2
            assert "test1" in data["clients"]
            assert "test2" in data["clients"]


class TestWebSocketErrorHandling:
    """
    Tests für Error-Handling
    """
    
    def test_websocket_adapter_error(self, client):
        """
        Test Error-Handling bei Adapter-Fehler
        """
        with patch('backend.adapters.adapter_factory.get_database_adapter') as mock_adapter:
            # Mock Adapter Exception
            mock_adapter.return_value = AsyncMock()
            mock_adapter.return_value.vector_search = AsyncMock(
                side_effect=Exception("Database connection failed")
            )
            
            with client.websocket_connect("/api/v3/ws/search?client_id=test") as websocket:
                # Welcome
                websocket.receive_json()
                
                # Send search
                websocket.send_json({
                    "action": "search",
                    "query": "test",
                    "top_k": 5
                })
                
                # Receive search_started
                websocket.receive_json()
                
                # Receive error
                error = websocket.receive_json()
                assert error["type"] == "error"
                assert "Search failed" in error["message"]
    
    def test_websocket_unknown_action(self, client):
        """
        Test unbekannte Action
        """
        with client.websocket_connect("/api/v3/ws/search?client_id=test") as websocket:
            # Welcome
            websocket.receive_json()
            
            # Send unknown action
            websocket.send_json({
                "action": "unknown_action"
            })
            
            # Receive error
            error = websocket.receive_json()
            assert error["type"] == "error"
            assert "Unknown action" in error["message"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
