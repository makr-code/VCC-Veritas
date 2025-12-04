#!/usr/bin/env python3
"""Behebe alle Agent Monitor Methodenaufrufe"""

import os
from pathlib import Path

os.chdir(r"c:\VCC\veritas")

# Dateien, die zu beheben sind
files_to_fix = [
    "backend/agents/domain/construction/genehmigung_agent.py",
    "backend/agents/domain/weather/dwd_weather_agent_v3_framework.py",
    "backend/agents/domain/environmental/environmental_agent_v2_framework.py",
]

for file_path in files_to_fix:
    if not Path(file_path).exists():
        continue

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Entferne alle nicht-existierenden monitor Methoden
    # record_failure -> simply remove
    content = content.replace(
        "self.monitor.record_failure(", "if False: self.monitor.record_failure("  # Deaktiviere den Aufruf
    )

    # record_error -> simply remove
    content = content.replace("self.monitor.record_error(", "if False: self.monitor.record_error(")  # Deaktiviere den Aufruf

    # record_execution -> simply remove
    content = content.replace(
        "self.monitor.record_execution(", "if False: self.monitor.record_execution("  # Deaktiviere den Aufruf
    )

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"✓ {file_path} fixed")

print("\nDone!")
