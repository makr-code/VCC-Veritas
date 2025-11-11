#!/usr/bin/env python3
"""
Tests für Environmental Agent

Author: VERITAS System
Date: 2025-09-28
"""

import os
import sys
import unittest
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.agents.veritas_api_agent_environmental import (
    EnvironmentalAgent,
    EnvironmentalAgentConfig,
    EnvironmentalQueryRequest,
    EnvironmentalQueryResponse,
    create_environmental_agent,
    get_default_environmental_config,
)


class TestEnvironmentalAgent(unittest.TestCase):
    def setUp(self):
        """Setup für jeden Test"""
        self.config = get_default_environmental_config()
        self.agent = create_environmental_agent(self.config)

    def tearDown(self):
        """Cleanup nach jedem Test"""
        self.agent.shutdown()

    def test_agent_initialization(self):
        """Test Agent Initialisierung"""
        self.assertIsNotNone(self.agent)
        self.assertEqual(self.agent.config, self.config)
        self.assertTrue(self.agent.agent_id.startswith("environmental_agent_"))

    def test_basic_query_processing(self):
        """Test Basic Query Processing"""
        request = EnvironmentalQueryRequest(query_id="test-001", query_text="Test query for environmental agent")

        response = self.agent.execute_query(request)

        self.assertTrue(response.success)
        self.assertEqual(response.query_id, "test-001")
        self.assertGreater(len(response.results), 0)
        self.assertGreater(response.confidence_score, 0)

    def test_input_validation(self):
        """Test Input Validation"""
        # Valid request
        valid_request = EnvironmentalQueryRequest(query_id="test-002", query_text="Valid query")
        self.assertTrue(self.agent.validate_input(valid_request))

        # Invalid request (empty query)
        invalid_request = EnvironmentalQueryRequest(query_id="test-003", query_text="")
        self.assertFalse(self.agent.validate_input(invalid_request))

    def test_agent_status(self):
        """Test Agent Status"""
        status = self.agent.get_status()

        self.assertIn("agent_id", status)
        self.assertIn("status", status)
        self.assertIn("performance", status)
        self.assertIn("capabilities", status)

    def test_capabilities(self):
        """Test Agent Capabilities"""
        capabilities = self.agent.get_capabilities()

        self.assertIsInstance(capabilities, list)
        self.assertGreater(len(capabilities), 0)


if __name__ == "__main__":
    unittest.main()
