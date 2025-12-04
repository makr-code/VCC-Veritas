#!/usr/bin/env python3
"""
Behebe Framework-Initialisierungsfehler in allen Agents
"""

import os
from pathlib import Path

os.chdir(r"c:\VCC\veritas")

# Fix construction_agent_v2_framework.py
construction_file = Path("backend/agents/domain/construction/construction_agent_v2_framework.py")
if construction_file.exists():
    content = construction_file.read_text("utf-8")

    # Replace QualityGate initialization
    content = content.replace(
        "self.quality_gate = QualityGate(min_confidence=0.6)",
        """# Quality Gate with policy
        policy = QualityPolicy(min_quality=0.6, target_quality=0.8)
        self.quality_gate = QualityGate(policy)""",
    )

    # Replace RetryHandler initialization
    content = content.replace(
        "self.retry_handler = RetryHandler(max_retries=3)",
        """retry_config = RetryConfig(max_retries=3)
        self.retry_handler = RetryHandler(retry_config)""",
    )

    # Update imports if needed
    if "from backend.agents.framework.quality_gate import QualityGate" in content:
        content = content.replace(
            "from backend.agents.framework.quality_gate import QualityGate",
            "from backend.agents.framework.quality_gate import QualityGate, QualityPolicy",
        )

    if "from backend.agents.framework.retry_handler import RetryHandler" in content:
        content = content.replace(
            "from backend.agents.framework.retry_handler import RetryHandler",
            "from backend.agents.framework.retry_handler import RetryHandler, RetryConfig",
        )

    # Add execute_step() if not present
    if "def execute_step" not in content:
        # Find the get_capabilities method and add execute_step before it
        insert_point = content.find("    def get_agent_type")
        if insert_point > 0:
            execute_step = '''    def execute_step(self, step_data: dict) -> dict:
        """Execute a single processing step."""
        try:
            query = step_data.get("query", "")
            if not query:
                return {"success": False, "error": "No query provided"}
            result = asyncio.run(self.process_query(query))
            return result
        except Exception as e:
            return {"success": False, "error": str(e)}

'''
            content = content[:insert_point] + execute_step + content[insert_point:]

    construction_file.write_text(content, "utf-8")
    print("✓ construction_agent_v2_framework.py fixed")

# Fix environmental_agent_v2_framework.py
environmental_file = Path("backend/agents/domain/environmental/environmental_agent_v2_framework.py")
if environmental_file.exists():
    content = environmental_file.read_text("utf-8")

    # Replace QualityGate initialization
    content = content.replace(
        "self.quality_gate = QualityGate(min_confidence=0.6)",
        """# Quality Gate with policy
        policy = QualityPolicy(min_quality=0.6, target_quality=0.8)
        self.quality_gate = QualityGate(policy)""",
    )

    # Replace RetryHandler initialization
    content = content.replace(
        "self.retry_handler = RetryHandler(max_retries=3)",
        """retry_config = RetryConfig(max_retries=3)
        self.retry_handler = RetryHandler(retry_config)""",
    )

    # Update imports
    if "from backend.agents.framework.quality_gate import QualityGate" in content:
        content = content.replace(
            "from backend.agents.framework.quality_gate import QualityGate",
            "from backend.agents.framework.quality_gate import QualityGate, QualityPolicy",
        )

    if "from backend.agents.framework.retry_handler import RetryHandler" in content:
        content = content.replace(
            "from backend.agents.framework.retry_handler import RetryHandler",
            "from backend.agents.framework.retry_handler import RetryHandler, RetryConfig",
        )

    # Add execute_step() if not present
    if "def execute_step" not in content:
        insert_point = content.find("    def get_agent_type")
        if insert_point > 0:
            execute_step = '''    def execute_step(self, step_data: dict) -> dict:
        """Execute a single processing step."""
        try:
            query = step_data.get("query", "")
            if not query:
                return {"success": False, "error": "No query provided"}
            result = asyncio.run(self.process_query(query))
            return result
        except Exception as e:
            return {"success": False, "error": str(e)}

'''
            content = content[:insert_point] + execute_step + content[insert_point:]

    environmental_file.write_text(content, "utf-8")
    print("✓ environmental_agent_v2_framework.py fixed")

# Fix dwd_weather_agent_v3_framework.py
weather_file = Path("backend/agents/domain/weather/dwd_weather_agent_v3_framework.py")
if weather_file.exists():
    content = weather_file.read_text("utf-8")

    # Check for similar patterns
    if "QualityGate(min_confidence" in content:
        content = content.replace(
            "self.quality_gate = QualityGate(min_confidence=0.6)",
            """# Quality Gate with policy
        policy = QualityPolicy(min_quality=0.6, target_quality=0.8)
        self.quality_gate = QualityGate(policy)""",
        )

        if "from backend.agents.framework.quality_gate import QualityGate" in content:
            content = content.replace(
                "from backend.agents.framework.quality_gate import QualityGate",
                "from backend.agents.framework.quality_gate import QualityGate, QualityPolicy",
            )

    if "RetryHandler(max_retries=" in content:
        content = content.replace(
            "self.retry_handler = RetryHandler(max_retries=3)",
            """retry_config = RetryConfig(max_retries=3)
        self.retry_handler = RetryHandler(retry_config)""",
        )

        if "from backend.agents.framework.retry_handler import RetryHandler" in content:
            content = content.replace(
                "from backend.agents.framework.retry_handler import RetryHandler",
                "from backend.agents.framework.retry_handler import RetryHandler, RetryConfig",
            )

    # Add execute_step() if not present
    if "def execute_step" not in content:
        insert_point = content.find("    def get_agent_type")
        if insert_point > 0:
            execute_step = '''    def execute_step(self, step_data: dict) -> dict:
        """Execute a single processing step."""
        try:
            query = step_data.get("query", "")
            if not query:
                return {"success": False, "error": "No query provided"}
            result = asyncio.run(self.process_query(query))
            return result
        except Exception as e:
            return {"success": False, "error": str(e)}

'''
            content = content[:insert_point] + execute_step + content[insert_point:]

        weather_file.write_text(content, "utf-8")
        print("✓ dwd_weather_agent_v3_framework.py fixed")

print("\nDone!")
