"""
VERITAS Phase 4 - Integration Tests
====================================

End-to-End Tests für Agent-Kommunikationsprotokoll:
1. Request/Response Pattern
2. Publish/Subscribe Pattern
3. Broadcast Pattern
4. Context-Sharing Pattern
5. Supervisor-Koordination mit Messages
6. Performance-Benchmarks

Version: 1.0
Author: VERITAS Development Team
Date: 6. Oktober 2025
"""

import asyncio
import time
import logging
import sys
import os
from pathlib import Path
from typing import Dict, Any, Optional

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from shared.protocols.agent_message import (
        AgentMessage,
        AgentIdentity,
        MessageType,
        MessagePriority,
        create_request_message,
        create_event_message,
        create_broadcast_message,
        create_context_share_message
    )
    from backend.agents.agent_message_broker import AgentMessageBroker
    from backend.agents.agent_message_broker_enhanced import BrokerConfiguration
    from shared.mixins.agent_communication_mixin import AgentCommunicationMixin
except ImportError as e:
    print(f"❌ Import-Fehler: {e}")
    print("   Stelle sicher, dass PYTHONPATH korrekt gesetzt ist")
    sys.exit(1)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# TEST AGENTS
# ============================================================================

class TestEnvironmentalAgent(AgentCommunicationMixin):
    """Test-Agent: Environmental Analysis"""
    
    def __init__(self, broker: AgentMessageBroker):
        identity = AgentIdentity(
            agent_id="test-env-agent",
            agent_type="environmental",
            agent_name="Test Environmental Agent",
            capabilities=["environmental_analysis", "geographic_data"]
        )
        super().__init__(broker, identity)
        
        # Custom-Handler
        self.register_message_handler(MessageType.REQUEST, self._handle_analysis)
        
        # Subscribe to topics
        self.subscribe("rag_context_updates")
        self.subscribe("project_updates")
        
        # Stats
        self.requests_handled = 0
        self.events_received = 0
        self.contexts_received = 0
        self.broadcasts_received = 0  # NEW: Track broadcasts
    
    async def _handle_analysis(self, message: AgentMessage) -> Dict[str, Any]:
        """Handle environmental analysis requests"""
        self.requests_handled += 1
        query = message.payload.get("query", "")
        
        # Simulate work
        await asyncio.sleep(0.05)
        
        return {
            "result": {
                "environmental_assessment": "Good",
                "terrain_type": "urban",
                "air_quality": "acceptable",
                "water_quality": "good"
            },
            "confidence": 0.95,
            "agent": "environmental",
            "processing_time_ms": 50
        }
    
    async def _handle_event(self, message: AgentMessage) -> None:
        self.events_received += 1
        await super()._handle_event(message)
    
    async def _handle_broadcast(self, message: AgentMessage) -> None:
        """Handle broadcast messages"""
        self.broadcasts_received += 1
        await super()._handle_broadcast(message)
    
    async def _handle_context_share(self, message: AgentMessage) -> None:
        self.contexts_received += 1
        await super()._handle_context_share(message)


class TestFinancialAgent(AgentCommunicationMixin):
    """Test-Agent: Financial Analysis"""
    
    def __init__(self, broker: AgentMessageBroker):
        identity = AgentIdentity(
            agent_id="test-fin-agent",
            agent_type="financial",
            agent_name="Test Financial Agent",
            capabilities=["financial_analysis", "cost_estimation"]
        )
        super().__init__(broker, identity)
        
        # Custom-Handler
        self.register_message_handler(MessageType.REQUEST, self._handle_analysis)
        
        # Subscribe
        self.subscribe("rag_context_updates")
        
        # Stats
        self.requests_handled = 0
        self.events_received = 0
        self.contexts_received = 0
        self.broadcasts_received = 0  # NEW
    
    async def _handle_analysis(self, message: AgentMessage) -> Dict[str, Any]:
        """Handle financial analysis requests"""
        self.requests_handled += 1
        query = message.payload.get("query", "")
        
        # Simulate work
        await asyncio.sleep(0.05)
        
        return {
            "result": {
                "total_cost": 1500000,
                "currency": "EUR",
                "breakdown": {
                    "land": 500000,
                    "construction": 800000,
                    "permits": 100000
                }
            },
            "confidence": 0.92,
            "agent": "financial",
            "processing_time_ms": 50
        }
    
    async def _handle_event(self, message: AgentMessage) -> None:
        self.events_received += 1
        await super()._handle_event(message)
    
    async def _handle_broadcast(self, message: AgentMessage) -> None:
        """Handle broadcast messages"""
        self.broadcasts_received += 1
        await super()._handle_broadcast(message)
    
    async def _handle_context_share(self, message: AgentMessage) -> None:
        self.contexts_received += 1
        await super()._handle_context_share(message)


class TestConstructionAgent(AgentCommunicationMixin):
    """Test-Agent: Construction Analysis"""
    
    def __init__(self, broker: AgentMessageBroker):
        identity = AgentIdentity(
            agent_id="test-construction-agent",
            agent_type="construction",
            agent_name="Test Construction Agent",
            capabilities=["building_permits", "zoning_regulations"]
        )
        super().__init__(broker, identity)
        
        # Custom-Handler
        self.register_message_handler(MessageType.REQUEST, self._handle_analysis)
        
        # Subscribe
        self.subscribe("project_updates")
        
        # Stats
        self.requests_handled = 0
        self.events_received = 0
        self.contexts_received = 0
        self.broadcasts_received = 0  # NEW
    
    async def _handle_analysis(self, message: AgentMessage) -> Dict[str, Any]:
        """Handle construction analysis requests"""
        self.requests_handled += 1
        query = message.payload.get("query", "")
        
        # Simulate work
        await asyncio.sleep(0.05)
        
        return {
            "result": {
                "building_regulations": "compliant",
                "zoning": "residential",
                "permits_required": ["building_permit", "environmental_permit"]
            },
            "confidence": 0.88,
            "agent": "construction",
            "processing_time_ms": 50
        }
    
    async def _handle_event(self, message: AgentMessage) -> None:
        self.events_received += 1
        await super()._handle_event(message)
    
    async def _handle_broadcast(self, message: AgentMessage) -> None:
        """Handle broadcast messages"""
        self.broadcasts_received += 1
        await super()._handle_broadcast(message)
    
    async def _handle_context_share(self, message: AgentMessage) -> None:
        self.contexts_received += 1
        await super()._handle_context_share(message)


# ============================================================================
# TEST SUITE
# ============================================================================

class Phase4IntegrationTests:
    """Integration Test Suite für Phase 4"""
    
    def __init__(self):
        self.broker = None
        self.env_agent = None
        self.fin_agent = None
        self.construction_agent = None
        self.test_results = []
    
    async def setup(self):
        """Setup test environment"""
        logger.info("🔧 Setup: Broker & Agents initialisieren")
        
        # Optimierte Broker-Configuration (basierend auf Phase 4.1 Benchmarks)
        config = BrokerConfiguration(
            num_workers=1,              # Optimal für In-Process
            enable_batching=True,       # Batching aktiviert
            batch_size=10,              # Optimale Batch-Size
            batch_timeout_ms=50,        # Kurzer Timeout für niedrige Latency
            delivery_parallelism=5,     # Moderate Parallelität
            max_queue_size=10000,
            retry_max_attempts=3
        )
        
        # Broker erstellen & starten
        self.broker = AgentMessageBroker(config=config)
        await self.broker.start()
        
        # Agents erstellen
        self.env_agent = TestEnvironmentalAgent(self.broker)
        self.fin_agent = TestFinancialAgent(self.broker)
        self.construction_agent = TestConstructionAgent(self.broker)
        
        # Wait for broker to be ready
        await asyncio.sleep(0.1)
        
        stats = self.broker.get_stats()
        logger.info(
            f"✅ Setup abgeschlossen: {stats['agents_registered']} Agents, "
            f"{stats['config']['num_workers']} Workers, "
            f"Batching={stats['config']['enable_batching']}"
        )
    
    async def teardown(self):
        """Cleanup test environment"""
        logger.info("🧹 Teardown: Cleanup")
        
        if self.env_agent:
            self.env_agent.cleanup()
        if self.fin_agent:
            self.fin_agent.cleanup()
        if self.construction_agent:
            self.construction_agent.cleanup()
        
        if self.broker:
            await self.broker.stop()
        
        logger.info("✅ Teardown abgeschlossen")
    
    # ========================================================================
    # TEST 1: REQUEST/RESPONSE PATTERN
    # ========================================================================
    
    async def test_request_response(self):
        """Test Request/Response Pattern"""
        logger.info("\n" + "="*80)
        logger.info("[TEST 1] Request/Response Pattern")
        logger.info("="*80)
        
        start = time.time()
        
        # Environmental Agent sendet Request an Financial Agent
        response = await self.env_agent.send_request(
            recipient=self.fin_agent.identity,
            payload={"query": "Grundstückskosten für Projekt XYZ?", "project_id": "test-001"},
            timeout=5.0
        )
        
        elapsed_ms = (time.time() - start) * 1000
        
        # Wait a bit for stats to update
        await asyncio.sleep(0.1)
        
        # Validierung
        success = response is not None
        if success:
            logger.info(f"✅ Response erhalten in {elapsed_ms:.1f}ms")
            logger.info(f"   Result: {response.get('result', {})}")
            logger.info(f"   Confidence: {response.get('confidence')}")
            logger.info(f"   Financial Agent Requests: {self.fin_agent.requests_handled}")
        else:
            logger.error(f"❌ Timeout bei Request/Response")
        
        self.test_results.append({
            "test": "Request/Response",
            "success": success,
            "latency_ms": elapsed_ms
        })
        
        return success
    
    # ========================================================================
    # TEST 2: PUBLISH/SUBSCRIBE PATTERN
    # ========================================================================
    
    async def test_publish_subscribe(self):
        """Test Publish/Subscribe Pattern"""
        logger.info("\n" + "="*80)
        logger.info("[TEST 2] Publish/Subscribe Pattern")
        logger.info("="*80)
        
        start = time.time()
        
        # Environmental Agent published Event an Topic "rag_context_updates"
        await self.env_agent.publish_event(
            topic="rag_context_updates",
            payload={
                "context_id": "ctx-test-001",
                "update_type": "geographic_boundaries",
                "data": {"boundaries": [52.5, 13.4], "area": "Berlin-Mitte"}
            }
        )
        
        # Wait for event delivery
        await asyncio.sleep(0.2)
        
        elapsed_ms = (time.time() - start) * 1000
        
        # Validierung: Env + Fin haben Topic abonniert
        env_events = self.env_agent.events_received
        fin_events = self.fin_agent.events_received
        construction_events = self.construction_agent.events_received
        
        success = (env_events >= 1 and fin_events >= 1)
        
        if success:
            logger.info(f"✅ Event zugestellt in {elapsed_ms:.1f}ms")
            logger.info(f"   Env-Agent Events: {env_events}")
            logger.info(f"   Fin-Agent Events: {fin_events}")
            logger.info(f"   Construction-Agent Events: {construction_events}")
        else:
            logger.error(f"❌ Event-Delivery fehlgeschlagen")
        
        self.test_results.append({
            "test": "Publish/Subscribe",
            "success": success,
            "latency_ms": elapsed_ms
        })
        
        return success
    
    # ========================================================================
    # TEST 3: BROADCAST PATTERN
    # ========================================================================
    
    async def test_broadcast(self):
        """Test Broadcast Pattern"""
        logger.info("\n" + "="*80)
        logger.info("[TEST 3] Broadcast Pattern")
        logger.info("="*80)
        
        start = time.time()
        
        # Reset stats
        env_broadcasts_before = self.env_agent.broadcasts_received
        fin_broadcasts_before = self.fin_agent.broadcasts_received
        construction_broadcasts_before = self.construction_agent.broadcasts_received
        
        # Env-Agent sendet Broadcast an alle
        await self.env_agent.send_broadcast(
            payload={
                "announcement": "System-Update in 5 Minuten",
                "action": "save_state",
                "timestamp": time.time()
            },
            priority=MessagePriority.HIGH
        )
        
        # Wait for delivery (Broadcasts can take longer due to batching)
        await asyncio.sleep(0.3)
        
        # Extra buffer for stats updates
        await asyncio.sleep(0.1)
        
        elapsed_ms = (time.time() - start) * 1000
        
        # Validierung: Alle 3 Agents sollten Broadcast erhalten haben
        # (Env-Agent bekommt eigene Broadcasts auch)
        env_delta = self.env_agent.broadcasts_received - env_broadcasts_before
        fin_delta = self.fin_agent.broadcasts_received - fin_broadcasts_before
        construction_delta = self.construction_agent.broadcasts_received - construction_broadcasts_before
        
        # Broker-Stats prüfen
        broker_stats = self.broker.get_stats()
        
        success = (env_delta >= 1 and fin_delta >= 1 and construction_delta >= 1)
        
        if success:
            logger.info(f"✅ Broadcast zugestellt in {elapsed_ms:.1f}ms")
            logger.info(f"   Empfangen von: Env({env_delta}), Fin({fin_delta}), Construction({construction_delta})")
            logger.info(f"   Broker Stats: {broker_stats['messages_delivered']} delivered, {broker_stats['messages_failed']} failed")
        else:
            logger.error(f"❌ Broadcast-Delivery unvollständig")
            logger.error(f"   Empfangen: Env({env_delta}), Fin({fin_delta}), Construction({construction_delta})")
            logger.error(f"   Broker Stats: {broker_stats}")
        
        self.test_results.append({
            "test": "Broadcast",
            "success": success,
            "latency_ms": elapsed_ms
        })
        
        return success
    
    # ========================================================================
    # TEST 4: CONTEXT-SHARING PATTERN
    # ========================================================================
    
    async def test_context_sharing(self):
        """Test Context-Sharing Pattern"""
        logger.info("\n" + "="*80)
        logger.info("[TEST 4] Context-Sharing Pattern")
        logger.info("="*80)
        
        start = time.time()
        
        # Env-Agent teilt Geographic-Context mit Construction-Agent
        await self.env_agent.share_context(
            recipient=self.construction_agent.identity,
            context_data={
                "project_area": "52.520°N, 13.405°E",
                "terrain_type": "urban",
                "soil_quality": "good",
                "flood_risk": "low"
            },
            context_type="geographic_context"
        )
        
        # Wait for delivery
        await asyncio.sleep(0.2)
        
        elapsed_ms = (time.time() - start) * 1000
        
        # Validierung
        success = self.construction_agent.contexts_received >= 1
        
        if success:
            logger.info(f"✅ Context geteilt in {elapsed_ms:.1f}ms")
            logger.info(f"   Construction-Agent Contexts: {self.construction_agent.contexts_received}")
        else:
            logger.error(f"❌ Context-Sharing fehlgeschlagen")
        
        self.test_results.append({
            "test": "Context-Sharing",
            "success": success,
            "latency_ms": elapsed_ms
        })
        
        return success
    
    # ========================================================================
    # TEST 5: CONCURRENT REQUESTS
    # ========================================================================
    
    async def test_concurrent_requests(self):
        """Test concurrent Request/Response"""
        logger.info("\n" + "="*80)
        logger.info("[TEST 5] Concurrent Requests (10 parallel)")
        logger.info("="*80)
        
        start = time.time()
        
        # 10 parallele Requests
        tasks = []
        for i in range(10):
            task = self.env_agent.send_request(
                recipient=self.fin_agent.identity,
                payload={"query": f"Cost analysis {i}", "request_id": i},
                timeout=10.0
            )
            tasks.append(task)
        
        # Wait for all
        responses = await asyncio.gather(*tasks)
        
        elapsed_ms = (time.time() - start) * 1000
        
        # Validierung
        successful_responses = sum(1 for r in responses if r is not None)
        success = successful_responses == 10
        
        if success:
            logger.info(f"✅ {successful_responses}/10 Requests erfolgreich in {elapsed_ms:.1f}ms")
            logger.info(f"   Avg latency: {elapsed_ms/10:.1f}ms per request")
        else:
            logger.error(f"❌ Nur {successful_responses}/10 Requests erfolgreich")
        
        self.test_results.append({
            "test": "Concurrent Requests",
            "success": success,
            "latency_ms": elapsed_ms,
            "requests": 10,
            "successful": successful_responses
        })
        
        return success
    
    # ========================================================================
    # TEST 6: PERFORMANCE BENCHMARK
    # ========================================================================
    
    async def test_performance_benchmark(self):
        """Performance-Benchmark: Throughput & Latency"""
        logger.info("\n" + "="*80)
        logger.info("[TEST 6] Performance-Benchmark (100 Messages)")
        logger.info("="*80)
        
        start = time.time()
        
        # 100 Messages (Mix aus Request/Event/Broadcast)
        tasks = []
        
        # 50 Requests
        for i in range(50):
            task = self.env_agent.send_request(
                recipient=self.fin_agent.identity,
                payload={"query": f"Benchmark request {i}"},
                timeout=15.0
            )
            tasks.append(("request", task))
        
        # 30 Events
        for i in range(30):
            task = self.env_agent.publish_event(
                topic="rag_context_updates",
                payload={"benchmark_event": i}
            )
            tasks.append(("event", task))
        
        # 20 Broadcasts
        for i in range(20):
            task = self.env_agent.send_broadcast(
                payload={"benchmark_broadcast": i}
            )
            tasks.append(("broadcast", task))
        
        # Wait for all
        results = await asyncio.gather(*[t[1] for t in tasks])
        
        # Wait for async deliveries
        await asyncio.sleep(0.5)
        
        elapsed_ms = (time.time() - start) * 1000
        
        # Stats
        throughput = 100 / (elapsed_ms / 1000)  # messages/sec
        avg_latency = elapsed_ms / 100
        
        # Broker stats
        broker_stats = self.broker.get_stats()
        
        success = broker_stats["messages_delivered"] > 80  # Mindestens 80% zugestellt
        
        logger.info(f"✅ Benchmark abgeschlossen in {elapsed_ms:.1f}ms")
        logger.info(f"   Throughput: {throughput:.1f} messages/sec")
        logger.info(f"   Avg Latency: {avg_latency:.1f}ms")
        logger.info(f"   Messages sent: {broker_stats['messages_sent']}")
        logger.info(f"   Messages delivered: {broker_stats['messages_delivered']}")
        logger.info(f"   Messages failed: {broker_stats['messages_failed']}")
        
        self.test_results.append({
            "test": "Performance Benchmark",
            "success": success,
            "latency_ms": elapsed_ms,
            "throughput_msgs_per_sec": throughput,
            "avg_latency_ms": avg_latency
        })
        
        return success
    
    # ========================================================================
    # RUN ALL TESTS
    # ========================================================================
    
    async def run_all_tests(self):
        """Run all integration tests"""
        logger.info("\n" + "="*80)
        logger.info("VERITAS PHASE 4 - INTEGRATION TESTS")
        logger.info("="*80)
        
        await self.setup()
        
        # Run tests SEQUENTIALLY (nicht parallel) für saubere Stats
        await self.test_publish_subscribe()
        await asyncio.sleep(0.2)  # Buffer zwischen Tests
        
        await self.test_context_sharing()
        await asyncio.sleep(0.2)
        
        await self.test_broadcast()
        await asyncio.sleep(0.2)
        
        await self.test_request_response()
        await asyncio.sleep(0.2)
        
        await self.test_concurrent_requests()
        await asyncio.sleep(0.2)
        
        await self.test_performance_benchmark()
        
        await self.teardown()
        
        # Summary
        logger.info("\n" + "="*80)
        logger.info("TEST SUMMARY")
        logger.info("="*80)
        
        for result in self.test_results:
            status = "✅ PASS" if result["success"] else "❌ FAIL"
            logger.info(f"{status} - {result['test']}: {result.get('latency_ms', 0):.1f}ms")
        
        success_count = sum(1 for r in self.test_results if r["success"])
        total_count = len(self.test_results)
        
        logger.info(f"\nTotal: {success_count}/{total_count} Tests erfolgreich")
        logger.info("="*80)
        
        return success_count == total_count


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    async def main():
        """Run integration tests"""
        test_suite = Phase4IntegrationTests()
        success = await test_suite.run_all_tests()
        
        sys.exit(0 if success else 1)
    
    asyncio.run(main())
