#!/usr/bin/env python3
"""Behebe alle Merge-Konflikte in der Veritas Codebasis"""

import os
import re
from pathlib import Path
from typing import Optional, Tuple


def resolve_conflict(content: str) -> Tuple[str, int]:
    """Löse Merge-Konflikte auf - wähle immer die Stashed changes (neuere Version)"""

    conflict_pattern = r"<<<<<<< Updated upstream\n(.*?)\n=======\n(.*?)\n>>>>>>> Stashed changes"

    def replacer(match):
        return match.group(2)  # Wähle die Stashed changes (neuere)

    resolved, count = re.subn(conflict_pattern, replacer, content, flags=re.DOTALL)

    return resolved, count


def process_file(filepath: Path) -> bool:
    """Verarbeite eine einzelne Datei"""
    try:
        # Versuche verschiedene Encoding
        for encoding in ["utf-8", "latin1", "cp1252", "ascii"]:
            try:
                with open(filepath, "r", encoding=encoding) as f:
                    content = f.read()
                break
            except (UnicodeDecodeError, LookupError):
                continue
        else:
            return False

        resolved_content, count = resolve_conflict(content)

        if count > 0:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(resolved_content)
            print(f"✓ {filepath}: {count} Konflikt(e) behoben")
            return True
        return False
    except Exception as e:
        return False


def main():
    """Hauptfunktion"""
    os.chdir(r"c:\VCC\veritas")

    # Finde alle Python-Dateien mit Konflikten - nur backend + tests
    extensions = {".py", ".md", ".ps1", ".json"}
    total_files = 0
    resolved_files = 0
    total_conflicts = 0

    print("Suche nach Dateien mit Merge-Konflikten...\n")

    # Nur backend und tests durchsuchen
    for scan_dir in ["backend", "tests", "shared"]:
        if not Path(scan_dir).exists():
            continue

        for root, dirs, files in os.walk(scan_dir):
            # Ignoriere venv und cache
            dirs[:] = [d for d in dirs if d not in {".git", "__pycache__", ".pytest_cache"}]

            for file in files:
                if any(file.endswith(ext) for ext in extensions):
                    filepath = Path(root) / file
                    total_files += 1

                    if process_file(filepath):
                        resolved_files += 1

    print(f"\nZusammenfassung:")
    print(f"   Gesamtdateien durchsucht: {total_files}")
    print(f"   Dateien mit Konflikten: {resolved_files}")
    print(f"\nMerge-Konflikt-Aufloesung abgeschlossen!")


if __name__ == "__main__":
    main()
