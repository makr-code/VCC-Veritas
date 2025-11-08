"""
Locust Load Testing für ThemisDB/UDS3 Adapter Endpoints

Verwendung:
    # Web UI
    locust -f tests/load/locustfile.py --host http://localhost:8000

    # Headless
    locust -f tests/load/locustfile.py \
        --headless \
        --users 100 \
        --spawn-rate 10 \
        --run-time 60s \
        --host http://localhost:8000
"""

from locust import HttpUser, task, between, events
import json
import random


class ThemisDBUser(HttpUser):
    """
    Simulated User für ThemisDB/UDS3 Adapter Load Testing
    """
    
    wait_time = between(1, 3)  # 1-3 Sekunden Wartezeit zwischen Tasks
    
    # Sample Queries
    queries = [
        "machine learning",
        "artificial intelligence",
        "data science",
        "neural networks",
        "deep learning",
        "natural language processing",
        "computer vision",
        "reinforcement learning"
    ]
    
    def on_start(self):
        """
        Wird beim Start jedes Users ausgeführt
        """
        self.client.headers = {
            "Content-Type": "application/json",
            "User-Agent": "Locust Load Test"
        }
    
    @task(10)
    def vector_search(self):
        """
        Test Vector Search Endpoint (hohe Gewichtung)
        """
        payload = {
            "query": random.choice(self.queries),
            "top_k": random.randint(3, 10),
            "collection": "documents"
        }
        
        with self.client.post(
            "/api/v3/themis/vector/search",
            json=payload,
            catch_response=True,
            name="Vector Search"
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if "results" in data and len(data["results"]) > 0:
                    response.success()
                else:
                    response.failure("No results returned")
            else:
                response.failure(f"Status code: {response.status_code}")
    
    @task(5)
    def adapter_status(self):
        """
        Test Adapter Status Endpoint
        """
        with self.client.get(
            "/api/v3/adapters/status",
            catch_response=True,
            name="Adapter Status"
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if "current_adapter" in data:
                    response.success()
                else:
                    response.failure("Missing current_adapter field")
            else:
                response.failure(f"Status code: {response.status_code}")
    
    @task(3)
    def adapter_metrics(self):
        """
        Test Adapter Metrics Endpoint
        """
        self.client.get(
            "/api/v3/adapters/metrics",
            name="Adapter Metrics"
        )
    
    @task(2)
    def adapter_capabilities(self):
        """
        Test Adapter Capabilities Endpoint
        """
        with self.client.get(
            "/api/v3/adapters/capabilities",
            catch_response=True,
            name="Adapter Capabilities"
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list) and len(data) > 0:
                    response.success()
                else:
                    response.failure("Invalid capabilities response")
    
    @task(1)
    def health_check(self):
        """
        Test Health Check Endpoint (niedrige Gewichtung)
        """
        self.client.get("/api/v3/themis/health", name="Health Check")
    
    @task(1)
    def graph_traverse(self):
        """
        Test Graph Traversal Endpoint
        """
        payload = {
            "start_vertex": f"doc{random.randint(1, 100)}",
            "edge_collection": "citations",
            "direction": "outbound",
            "max_depth": random.randint(1, 3)
        }
        
        self.client.post(
            "/api/v3/themis/graph/traverse",
            json=payload,
            name="Graph Traverse"
        )
    
    @task(1)
    def aql_query(self):
        """
        Test AQL Query Endpoint
        """
        payload = {
            "query": "FOR doc IN documents LIMIT 10 RETURN doc",
            "bind_vars": {}
        }
        
        self.client.post(
            "/api/v3/themis/aql/query",
            json=payload,
            name="AQL Query"
        )


class WebSocketUser(HttpUser):
    """
    WebSocket Load Testing (experimental)
    """
    
    wait_time = between(2, 5)
    
    @task
    def websocket_search(self):
        """
        Simuliert WebSocket-Verbindung
        (Locust unterstützt WebSocket nur begrenzt)
        """
        # Placeholder für WebSocket-Tests
        # Für echte WebSocket-Tests: k6 verwenden
        pass


# Event Handlers für Custom Metrics

@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """
    Wird beim Start des Load Tests ausgeführt
    """
    print("Starting Load Test...")
    print(f"Target: {environment.host}")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """
    Wird beim Ende des Load Tests ausgeführt
    """
    print("\nLoad Test Completed!")
    print(f"Total Requests: {environment.stats.total.num_requests}")
    print(f"Total Failures: {environment.stats.total.num_failures}")
    print(f"Average Response Time: {environment.stats.total.avg_response_time:.2f}ms")
    print(f"Requests/sec: {environment.stats.total.total_rps:.2f}")


@events.request.add_listener
def on_request(request_type, name, response_time, response_length, exception, **kwargs):
    """
    Wird nach jedem Request ausgeführt
    """
    # Custom Logging oder Metrics können hier hinzugefügt werden
    pass


if __name__ == "__main__":
    import os
    os.system("locust -f locustfile.py --host http://localhost:8000")
