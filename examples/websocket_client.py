"""
Python WebSocket Client für ThemisDB Adapter

Beispiele für die Verwendung der WebSocket-Endpoints:
- Real-time Vector Search
- Adapter Status Monitoring
- Live Log Streaming
- Graph Traversal

Installation:
    pip install websockets asyncio

Verwendung:
    python websocket_client.py
"""

import asyncio
import websockets
import json
from datetime import datetime
from typing import Optional


class ThemisWebSocketClient:
    """
    WebSocket Client für ThemisDB/UDS3 Adapter
    """
    
    def __init__(self, base_url: str = "ws://localhost:8000/api/v3/ws"):
        self.base_url = base_url
        self.client_id = f"python_client_{datetime.now().strftime('%H%M%S')}"
    
    async def vector_search(
        self,
        query: str,
        top_k: int = 5,
        collection: str = "documents",
        threshold: Optional[float] = None
    ):
        """
        Real-time Vector Search mit progressivem Result-Streaming
        """
        url = f"{self.base_url}/search?client_id={self.client_id}"
        
        async with websockets.connect(url) as websocket:
            print(f"✓ Connected to {url}")
            
            # Warte auf Welcome Message
            welcome = await websocket.recv()
            print(f"Server: {json.loads(welcome)['message']}")
            
            # Sende Search Query
            search_request = {
                "action": "search",
                "query": query,
                "top_k": top_k,
                "collection": collection
            }
            
            if threshold:
                search_request["threshold"] = threshold
            
            await websocket.send(json.dumps(search_request))
            print(f"\n🔍 Searching for: '{query}' (top_k={top_k})")
            
            # Empfange Results
            results = []
            search_complete = False
            
            while not search_complete:
                response = await websocket.recv()
                message = json.loads(response)
                
                match message["type"]:
                    case "search_started":
                        print(f"✓ Search started (Adapter: {message['adapter']})")
                    
                    case "result":
                        result_data = message["data"]
                        score = message["score"]
                        index = message["index"]
                        total = message["total"]
                        
                        print(f"\nResult {index + 1}/{total}:")
                        print(f"  Score: {score:.4f}")
                        print(f"  ID: {result_data.get('id', 'N/A')}")
                        print(f"  Content: {result_data.get('content', str(result_data)[:100])}")
                        
                        results.append(result_data)
                    
                    case "search_complete":
                        print(f"\n✓ Search Complete:")
                        print(f"  Total Results: {message['total_results']}")
                        print(f"  Duration: {message['duration_ms']:.2f}ms")
                        print(f"  Adapter: {message['adapter_used']}")
                        search_complete = True
                    
                    case "error":
                        print(f"\n❌ Error: {message['message']}")
                        search_complete = True
            
            return results
    
    async def monitor_adapter_status(
        self,
        interval: int = 5,
        duration: Optional[int] = None
    ):
        """
        Live Adapter Status Monitoring
        
        Args:
            interval: Update-Intervall in Sekunden
            duration: Monitoring-Dauer in Sekunden (None = unbegrenzt)
        """
        url = f"{self.base_url}/adapter/status?client_id={self.client_id}&interval={interval}"
        
        async with websockets.connect(url) as websocket:
            print(f"✓ Connected to Status Monitor (interval={interval}s)")
            
            start_time = datetime.now()
            
            while True:
                # Check duration limit
                if duration:
                    elapsed = (datetime.now() - start_time).total_seconds()
                    if elapsed >= duration:
                        print(f"\n⏱ Monitoring duration reached ({duration}s)")
                        break
                
                response = await websocket.recv()
                message = json.loads(response)
                
                if message["type"] == "status_update":
                    timestamp = message["timestamp"]
                    current_adapter = message["current_adapter"]
                    themis = message["themis"]
                    uds3 = message["uds3"]
                    
                    print(f"\n{'='*60}")
                    print(f"Status Update - {datetime.fromisoformat(timestamp).strftime('%H:%M:%S')}")
                    print(f"{'='*60}")
                    print(f"Current Adapter: {current_adapter.upper()}")
                    print(f"ThemisDB: {'✓ Available' if themis['available'] else '✗ Down'}")
                    
                    if "query_count" in themis:
                        print(f"  - Queries: {themis['query_count']}")
                        print(f"  - Avg Latency: {themis.get('avg_latency_ms', 0):.2f}ms")
                        print(f"  - Success Rate: {themis.get('success_rate', 0):.2%}")
                    
                    print(f"UDS3: {'✓ Available' if uds3['available'] else '✗ Down'}")
                    print(f"Active WebSocket Connections: {message.get('active_websocket_connections', 0)}")
    
    async def stream_logs(
        self,
        log_level: str = "INFO",
        duration: Optional[int] = None
    ):
        """
        Live Backend Log Streaming
        
        Args:
            log_level: DEBUG, INFO, WARNING, ERROR, CRITICAL
            duration: Streaming-Dauer in Sekunden (None = unbegrenzt)
        """
        url = f"{self.base_url}/logs?client_id={self.client_id}&log_level={log_level}"
        
        async with websockets.connect(url) as websocket:
            print(f"✓ Connected to Log Stream (level={log_level})")
            
            start_time = datetime.now()
            
            while True:
                # Check duration limit
                if duration:
                    elapsed = (datetime.now() - start_time).total_seconds()
                    if elapsed >= duration:
                        print(f"\n⏱ Streaming duration reached ({duration}s)")
                        break
                
                response = await websocket.recv()
                message = json.loads(response)
                
                if message["type"] == "log":
                    timestamp = datetime.fromisoformat(message["timestamp"]).strftime('%H:%M:%S.%f')[:-3]
                    level = message["level"]
                    logger = message["logger"]
                    msg = message["message"]
                    
                    # Color coding
                    colors = {
                        "DEBUG": "\033[37m",      # White
                        "INFO": "\033[36m",       # Cyan
                        "WARNING": "\033[33m",    # Yellow
                        "ERROR": "\033[31m",      # Red
                        "CRITICAL": "\033[35m"    # Magenta
                    }
                    reset = "\033[0m"
                    
                    color = colors.get(level, "")
                    print(f"{color}[{level}] {timestamp} - {logger}{reset}")
                    print(f"  {msg}")
    
    async def graph_traverse(
        self,
        start_vertex: str,
        edge_collection: str = "edges",
        direction: str = "outbound",
        max_depth: int = 3
    ):
        """
        Real-time Graph Traversal mit progressivem Node-Streaming
        """
        url = f"{self.base_url}/graph/traverse?client_id={self.client_id}"
        
        async with websockets.connect(url) as websocket:
            print(f"✓ Connected to Graph Traversal")
            
            # Welcome
            await websocket.recv()
            
            # Sende Traversal Request
            traversal_request = {
                "action": "traverse",
                "start_vertex": start_vertex,
                "edge_collection": edge_collection,
                "direction": direction,
                "max_depth": max_depth
            }
            
            await websocket.send(json.dumps(traversal_request))
            print(f"\n🌐 Traversing from '{start_vertex}' (depth={max_depth})")
            
            nodes = []
            edges = []
            complete = False
            
            while not complete:
                response = await websocket.recv()
                message = json.loads(response)
                
                match message["type"]:
                    case "traversal_started":
                        print(f"✓ Traversal started")
                    
                    case "node":
                        node_data = message["data"]
                        index = message["index"]
                        total = message["total"]
                        
                        print(f"\nNode {index + 1}/{total}:")
                        print(f"  {json.dumps(node_data, indent=2)}")
                        
                        nodes.append(node_data)
                    
                    case "edge":
                        edge_data = message["data"]
                        edges.append(edge_data)
                    
                    case "traversal_complete":
                        print(f"\n✓ Traversal Complete:")
                        print(f"  Total Nodes: {message['total_nodes']}")
                        print(f"  Total Edges: {message['total_edges']}")
                        print(f"  Max Depth: {message['max_depth_reached']}")
                        complete = True
                    
                    case "error":
                        print(f"\n❌ Error: {message['message']}")
                        complete = True
            
            return {"nodes": nodes, "edges": edges}


# ===========================
# Beispiel-Verwendung
# ===========================

async def main():
    """
    Demo aller WebSocket-Features
    """
    client = ThemisWebSocketClient()
    
    print("="*60)
    print("ThemisDB WebSocket Client - Demo")
    print("="*60)
    
    # 1. Vector Search
    print("\n\n### 1. Vector Search ###\n")
    try:
        results = await client.vector_search(
            query="machine learning best practices",
            top_k=3,
            collection="documents"
        )
        print(f"\nReceived {len(results)} results")
    except Exception as e:
        print(f"Vector Search failed: {e}")
    
    # 2. Adapter Status Monitoring (10 Sekunden)
    print("\n\n### 2. Adapter Status Monitoring ###\n")
    try:
        await client.monitor_adapter_status(
            interval=3,
            duration=10
        )
    except Exception as e:
        print(f"Status Monitoring failed: {e}")
    
    # 3. Live Logs (10 Sekunden)
    print("\n\n### 3. Live Log Streaming ###\n")
    try:
        await client.stream_logs(
            log_level="INFO",
            duration=10
        )
    except Exception as e:
        print(f"Log Streaming failed: {e}")
    
    # 4. Graph Traversal
    print("\n\n### 4. Graph Traversal ###\n")
    try:
        graph_data = await client.graph_traverse(
            start_vertex="doc123",
            edge_collection="citations",
            max_depth=2
        )
        print(f"\nTraversal returned {len(graph_data['nodes'])} nodes, {len(graph_data['edges'])} edges")
    except Exception as e:
        print(f"Graph Traversal failed: {e}")


if __name__ == "__main__":
    asyncio.run(main())
