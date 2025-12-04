"""
VERITAS Domain Agent Cleanup - Backup & Duplicate Removal
=========================================================

Führt aus:
1. Archiviert alle 69 .bak Dateien
2. Entfernt Wetter-Duplikate
3. Entfernt Immissionsschutz Legacy-Version
4. Auflösung von Merge-Konflikten
5. Generiert Cleanup-Report

Ausführung:
    python backend/agents/migration/cleanup_script.py
"""

import logging
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)-8s | %(message)s")
logger = logging.getLogger(__name__)


class AgentCleanup:
    """Cleanup-Utility für Domain Agents"""

    def __init__(self):
        self.base_dir = Path("c:\\VCC\\veritas")
        self.agents_dir = self.base_dir / "backend" / "agents"
        self.domain_dir = self.agents_dir / "domain"
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.archive_dir = self.base_dir / "archive" / f"agents_cleanup_{self.timestamp}"
        self.report = {
            "timestamp": self.timestamp,
            "backup_files": {"count": 0, "size_mb": 0},
            "duplicates": {"removed": [], "kept": []},
            "conflicts": {"resolved": []},
            "errors": [],
        }

    def run_full_cleanup(self) -> Dict:
        """Führe komplettes Cleanup durch"""
        logger.info("=" * 70)
        logger.info("🚀 VERITAS Agent Cleanup - Gestartet")
        logger.info("=" * 70)

        try:
            # Phase 1: Backup
            logger.info("\n📁 PHASE 1: Archiviere Backup-Dateien (.bak)")
            logger.info("-" * 70)
            self._archive_backups()

            # Phase 2: Remove Duplicates
            logger.info("\n🔗 PHASE 2: Entferne Duplikate")
            logger.info("-" * 70)
            self._remove_weather_duplicates()
            self._remove_immissionsschutz_legacy()

            # Phase 3: Resolve Conflicts
            logger.info("\n🔧 PHASE 3: Löse Merge-Konflikte auf")
            logger.info("-" * 70)
            self._resolve_conflicts()

            # Generate Report
            logger.info("\n📊 PHASE 4: Generiere Report")
            logger.info("-" * 70)
            self._generate_report()

            logger.info("\n" + "=" * 70)
            logger.info("✅ CLEANUP ABGESCHLOSSEN")
            logger.info("=" * 70)

            return self.report

        except Exception as e:
            logger.error(f"❌ Cleanup fehlgeschlagen: {e}", exc_info=True)
            self.report["errors"].append(str(e))
            return self.report

    # =====================================================================
    # Phase 1: Archive Backups
    # =====================================================================

    def _archive_backups(self):
        """Archiviert alle .bak Dateien"""
        logger.info("🔍 Suche nach .bak Dateien...")

        bak_files = list(self.domain_dir.rglob("*.bak"))
        total_size = 0

        if not bak_files:
            logger.info("✅ Keine .bak Dateien gefunden")
            return

        logger.info(f"📦 Gefunden: {len(bak_files)} Backup-Dateien")

        # Create archive directory
        backup_archive = self.archive_dir / "backups"
        backup_archive.mkdir(parents=True, exist_ok=True)

        for i, bak_file in enumerate(bak_files, 1):
            try:
                # Calculate relative path
                rel_path = bak_file.relative_to(self.agents_dir.parent)
                dest = backup_archive / rel_path
                dest.parent.mkdir(parents=True, exist_ok=True)

                # Get file size
                file_size = bak_file.stat().st_size
                total_size += file_size

                # Move file
                shutil.move(str(bak_file), str(dest))

                logger.info(f"  [{i:2d}/{len(bak_files)}] ✅ {bak_file.name} ({file_size/1024:.1f} KB)")

            except Exception as e:
                logger.error(f"  ❌ Fehler bei {bak_file.name}: {e}")
                self.report["errors"].append(f"Backup {bak_file.name}: {e}")

        self.report["backup_files"]["count"] = len(bak_files)
        self.report["backup_files"]["size_mb"] = round(total_size / (1024 * 1024), 2)

        logger.info(f"✅ {len(bak_files)} Dateien archiviert ({total_size/1024/1024:.2f} MB)")
        logger.info(f"   📁 Archiv: {backup_archive}")

    # =====================================================================
    # Phase 2: Remove Duplicates
    # =====================================================================

    def _remove_weather_duplicates(self):
        """Entfernt alte Wetter-Agent Versionen"""
        logger.info("🌡️  Weather Agents: Entferne Duplikate...")

        weather_dir = self.domain_dir / "weather"
        if not weather_dir.exists():
            logger.info("   ℹ️  weather/ Verzeichnis nicht gefunden")
            return

        # Legacy versions to remove (keep V3 Framework + BrightSky)
        legacy_files = [
            "dwd_weather_agent.py",  # v1
            "dwd_weather_agent_v2.py",  # v2 (replaced by v3_framework)
            "dwd_simple.py",
            "dwd_opendata_agent.py",
        ]

        legacy_archive = self.archive_dir / "duplicates" / "weather"
        kept_files = []
        removed_files = []

        for file_name in legacy_files:
            file_path = weather_dir / file_name

            if not file_path.exists():
                continue

            try:
                # Archive instead of delete
                legacy_archive.mkdir(parents=True, exist_ok=True)
                dest = legacy_archive / file_name
                shutil.move(str(file_path), str(dest))

                logger.info(f"   ✅ Archiviert: {file_name}")
                removed_files.append(file_name)

            except Exception as e:
                logger.error(f"   ❌ Fehler bei {file_name}: {e}")
                self.report["errors"].append(f"Weather duplicate {file_name}: {e}")

        # List kept files
        kept_files = [f.name for f in weather_dir.glob("*.py") if f.name != "__init__.py"]

        logger.info(f"   📊 Entfernt: {len(removed_files)} Dateien")
        logger.info(f"   📊 Behalten: {kept_files}")

        self.report["duplicates"]["removed"].extend(removed_files)
        self.report["duplicates"]["kept"] = kept_files

    def _remove_immissionsschutz_legacy(self):
        """Entfernt alte Immissionsschutz-Version"""
        logger.info("🏭 Immissionsschutz Agents: Entferne Legacy-Version...")

        immis_dir = self.domain_dir / "immissionsschutz"
        if not immis_dir.exists():
            logger.info("   ℹ️  immissionsschutz/ Verzeichnis nicht gefunden")
            return

        legacy_file = immis_dir / "immissionschutz_alt.py"

        if not legacy_file.exists():
            logger.info("   ℹ️  immissionschutz_alt.py nicht gefunden (bereits gelöscht?)")
            return

        try:
            legacy_archive = self.archive_dir / "duplicates" / "immissionsschutz"
            legacy_archive.mkdir(parents=True, exist_ok=True)
            dest = legacy_archive / "immissionschutz_alt.py"
            shutil.move(str(legacy_file), str(dest))

            logger.info(f"   ✅ Archiviert: immissionschutz_alt.py")
            self.report["duplicates"]["removed"].append("immissionschutz_alt.py")

        except Exception as e:
            logger.error(f"   ❌ Fehler beim Archivieren: {e}")
            self.report["errors"].append(f"Immissionsschutz legacy: {e}")

    # =====================================================================
    # Phase 3: Resolve Conflicts
    # =====================================================================

    def _resolve_conflicts(self):
        """Löst Merge-Konflikte auf"""
        logger.info("🔍 Suche nach Merge-Konflikten...")

        conflict_files = []

        for py_file in self.domain_dir.rglob("*.py"):
            if "__init__.py" in str(py_file) or ".bak" in str(py_file):
                continue

            try:
                content = py_file.read_text(encoding="utf-8")

                if "<<<<<<<" in content or "=======" in content or ">>>>>>>" in content:
                    conflict_files.append(py_file)
                    logger.info(f"   ⚠️  Konflikt gefunden: {py_file.relative_to(self.domain_dir)}")

            except Exception as e:
                logger.warning(f"   ❌ Fehler beim Lesen {py_file}: {e}")

        if not conflict_files:
            logger.info("✅ Keine Merge-Konflikte gefunden")
            return

        logger.info(f"🔧 Löse {len(conflict_files)} Konflikt(e) auf...")

        for conflict_file in conflict_files:
            try:
                self._resolve_single_conflict(conflict_file)
                logger.info(f"   ✅ Gelöst: {conflict_file.relative_to(self.domain_dir)}")
                self.report["conflicts"]["resolved"].append(str(conflict_file.relative_to(self.domain_dir)))

            except Exception as e:
                logger.error(f"   ❌ Fehler bei {conflict_file.name}: {e}")
                self.report["errors"].append(f"Conflict resolution {conflict_file.name}: {e}")

    def _resolve_single_conflict(self, file_path: Path):
        """Löst einen einzelnen Merge-Konflikt auf"""
        content = file_path.read_text(encoding="utf-8")
        lines = content.split("\n")
        resolved_lines = []

        in_conflict = False
        take_first = True
        conflict_start = 0

        for i, line in enumerate(lines):
            if line.startswith("<<<<<<<"):
                in_conflict = True
                take_first = True
                conflict_start = i

            elif line.startswith("======="):
                take_first = False

            elif line.startswith(">>>>>>>"):
                in_conflict = False

            elif in_conflict:
                if take_first:
                    resolved_lines.append(line)
                # Skip second version
            else:
                resolved_lines.append(line)

        # Write resolved file
        resolved_content = "\n".join(resolved_lines)
        file_path.write_text(resolved_content, encoding="utf-8")

    # =====================================================================
    # Phase 4: Generate Report
    # =====================================================================

    def _generate_report(self):
        """Generiert Cleanup-Report"""
        report_file = self.archive_dir / "CLEANUP_REPORT.md"

        report_content = f"""# VERITAS Agent Cleanup Report

**Datum:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**Archive:** {self.archive_dir}

## 📊 Zusammenfassung

### Backup-Dateien (.bak)
- **Anzahl:** {self.report['backup_files']['count']} Dateien
- **Größe:** {self.report['backup_files']['size_mb']} MB
- **Status:** ✅ Archiviert in `backups/`

### Duplikate entfernt
- **Weather Agents:** {len([f for f in self.report['duplicates']['removed'] if 'dwd' in f or 'weather' in f])} entfernt
  - Behalten: {', '.join(f for f in self.report['duplicates']['kept'] if 'v3' in f or 'bright' in f)}
- **Immissionsschutz:** 1 Legacy-Version archiviert
- **Total:** {len(self.report['duplicates']['removed'])} Duplikate

### Merge-Konflikte
- **Gelöst:** {len(self.report['conflicts']['resolved'])} Datei(en)
- **Dateien:** {chr(10).join(f"  - {f}" for f in self.report['conflicts']['resolved'])}

### Fehler
- **Anzahl:** {len(self.report['errors'])}
- **Details:** {chr(10).join(f"  - {e}" for e in self.report['errors']) if self.report['errors'] else "Keine Fehler"}

## 📁 Archiv-Struktur

```
{self.archive_dir}/
├── backups/              {self.report['backup_files']['count']} .bak Dateien
├── duplicates/
│   ├── weather/
│   └── immissionsschutz/
└── CLEANUP_REPORT.md     Dieser Report
```

## ✅ Nächste Schritte

1. **Agent Migration starten:**
   ```bash
   python backend/agents/migration/migration_accelerator.py --mode=migrate
   ```

2. **Registry aktualisieren:**
   ```bash
   python backend/agents/registry/domain_agent_registration.py
   ```

3. **Tests durchführen:**
   ```bash
   pytest backend/agents/tests/
   ```

4. **Git commit:**
   ```bash
   git add -A
   git commit -m "Migration: Cleanup .bak files and remove duplicates"
   ```

---

**Generated by:** VERITAS Agent Cleanup v2.0
**Command:** `python backend/agents/migration/cleanup_script.py`
"""

        report_file.parent.mkdir(parents=True, exist_ok=True)
        report_file.write_text(report_content)

        logger.info(f"✅ Report generiert: {report_file}")

        return report_file


# =========================================================================
# Main
# =========================================================================

if __name__ == "__main__":
    cleanup = AgentCleanup()
    report = cleanup.run_full_cleanup()

    print("\n" + "=" * 70)
    print("CLEANUP SUMMARY")
    print("=" * 70)
    print(f"✅ Backup-Dateien: {report['backup_files']['count']} ({report['backup_files']['size_mb']} MB)")
    print(f"✅ Duplikate entfernt: {len(report['duplicates']['removed'])}")
    print(f"✅ Konflikte gelöst: {len(report['conflicts']['resolved'])}")
    if report["errors"]:
        print(f"⚠️  Fehler: {len(report['errors'])}")
    else:
        print("✅ Keine Fehler")
    print("=" * 70)
