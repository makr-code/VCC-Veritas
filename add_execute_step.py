#!/usr/bin/env python3
"""
Behebe alle Agents - Füge execute_step() Implementation hinzu
"""

import os
import re
from pathlib import Path


def add_execute_step_to_agent(file_path):
    """Füge execute_step() zu einem Agent hinzu"""

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Prüfe ob execute_step bereits existiert
    if "def execute_step" in content:
        print(f"✓ {file_path}: execute_step() bereits vorhanden")
        return True

    # Finde die __init__() Methode und füge execute_step() danach ein
    execute_step_impl = '''

    # =====================================================================
    # Abstract Method Implementation
    # =====================================================================

    def execute_step(self, step_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a single processing step (abstract method implementation)

        Args:
            step_data: Processing step configuration

        Returns:
            Step execution result
        """
        try:
            query = step_data.get("query", "")
            if not query:
                return {"success": False, "error": "No query provided"}

            # Execute synchronously for framework compatibility
            result = asyncio.run(self.process_query(query))
            return result

        except Exception as e:
            self.logger.error(f"Step execution failed: {e}")
            return {"success": False, "error": str(e)}'''

    # Finde das Ende der __init__() Methode
    init_pattern = r"(class \w+.*?:\s*.*?def __init__.*?\n.*?self\.logger\.info\([^)]*\))"

    if re.search(init_pattern, content, re.DOTALL):
        # Füge execute_step() nach __init__() ein
        new_content = re.sub(init_pattern, r"\1" + execute_step_impl, content, count=1, flags=re.DOTALL)

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(new_content)

        print(f"✓ {file_path}: execute_step() hinzugefügt")
        return True
    else:
        print(f"? {file_path}: Konnte __init__() nicht finden")
        return False


# Finde alle Agent-Dateien
agent_files = [
    "backend/agents/domain/weather/dwd_weather_agent_v3_framework.py",
    "backend/agents/domain/construction/construction_agent_v2_framework.py",
    "backend/agents/domain/environmental/environmental_agent_v2_framework.py",
]

os.chdir(r"c:\VCC\veritas")

for agent_file in agent_files:
    if Path(agent_file).exists():
        add_execute_step_to_agent(agent_file)
    else:
        print(f"✗ {agent_file}: Datei nicht gefunden")

print("\nDone!")
