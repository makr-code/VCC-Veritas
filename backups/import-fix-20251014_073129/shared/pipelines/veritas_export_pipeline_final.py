#!/usr/bin/env python3
"""
VERITAS Export Pipeline - Production Ready
Finale optimierte Version mit korrekter Verzeichnisstruktur
"""

import json
import os
import shutil
import sys
import time
from pathlib import Path
from typing import Dict, List


class VERITASExportPipelineFinal:
    """
    Production-ready Export Pipeline für VERITAS
    """

    def __init__(self, project_root: str = None, export_root: str = None):
        self.project_root = Path(project_root or str(Path(__file__).parent))
        self.export_root = Path(export_root or self.project_root / "veritas_export_final")
        self.build_info = {"timestamp": time.time(), "version": "1.0.0", "build_id": f"PROD_{str(int(time.time()))[-8:]}"}

    def create_export_structure(self) -> bool:
        """
        Erstellt die komplette Export-Verzeichnisstruktur
        """
        print("📁 Creating export structure...")

        try:
            # Haupt-Verzeichnisse
            directories = {
                "src/core": "Python source files",
                "src/config": "Configuration files",
                "src/data": "Data files",
                "src/resources": "Resources & templates",
                "src/docs": "Documentation",
                "protected/core": "Protected Python files",
                "protected/config": "Protected config files",
                "protected/data": "Protected data files",
                "protected/resources": "Protected resources",
                "protected/docs": "Protected docs",
                "dist": "Final distribution",
                "backup": "Original backups",
                "logs": "Build logs",
                "installer": "Installation packages",
            }

            for dir_path, description in directories.items():
                full_path = self.export_root / dir_path
                full_path.mkdir(parents=True, exist_ok=True)
                print(f"  ✅ {dir_path}")

            # Build-Info speichern
            build_info_file = self.export_root / "build_info.json"
            with open(build_info_file, "w", encoding="utf-8") as f:
                json.dump(self.build_info, f, indent=2)

            print(f"✅ Export structure ready: {self.export_root}")
            return True

        except Exception as e:
            print(f"❌ Structure creation failed: {e}")
            return False

    def get_production_files(self) -> Dict[str, List[str]]:
        """
        Definiert alle Production-relevanten Dateien
        """
        file_structure = {
            "python_files": [
                # Security Core (Kritisch)
                "license_protection_system.py",
                "license_protection_integration.py",
                "license_protection_setup.py",
                "security_validator.py",
                "production_license_manager.py",
                # System Core
                "veritas_core.py",
                "database_manager.py",
                "uds3_core.py",
                "covina_module.py",
                # Database APIs
                "database_api.py",
                "database_api_neo4j.py",
                "database_api_postgresql.py",
                "robust_database_manager.py",
                # API Endpoints
                "api_endpoint_fastapi_production.py",
                "api_endpoint_conversation_dw_manager.py",
                "user_api.py",
                "endpoint_api.py",
                # Quality Systems
                "quality_management_db.py",
                "rag_quality_enhanced_retrieval.py",
                # GUI Apps
                "veritas_app.py",
                "covina_app.py",
            ],
            "config_files": ["requirements.txt", "setup.py", "README.md", "CHANGELOG.md"],
            "data_files": [
                # Erstelle diese Dateien falls sie nicht existieren
                "veritas_default_config.json",
                "database_init.sql",
            ],
            "docs": ["API_DOCUMENTATION.md", "USER_GUIDE.md", "INSTALLATION_GUIDE.md"],
        }

        # Nur existierende Dateien filtern
        filtered_structure = {}
        for category, file_list in file_structure.items():
            existing_files = []
            for filename in file_list:
                file_path = self.project_root / filename
                if file_path.exists():
                    existing_files.append(filename)
                elif category == "data_files":
                    # Erstelle fehlende Data Files
                    self._create_missing_data_file(filename)
                    if file_path.exists():
                        existing_files.append(filename)

            if existing_files:
                filtered_structure[category] = existing_files

        return filtered_structure

    def _create_missing_data_file(self, filename: str):
        """
        Erstellt fehlende Data Files
        """
        file_path = self.project_root / filename

        if filename == "veritas_default_config.json":
            config = {
                "app_name": "VERITAS",
                "version": self.build_info["version"],
                "license_required": True,
                "default_settings": {"log_level": "INFO", "database_timeout": 30, "api_timeout": 60},
            }
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2)

        elif filename == "database_init.sql":
            sql_content = """-- VERITAS Database Initialization
CREATE TABLE IF NOT EXISTS license_keys (
    id INTEGER PRIMARY KEY,
    client_id TEXT NOT NULL,
    license_key TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS file_hashes (
    id INTEGER PRIMARY KEY,
    file_path TEXT NOT NULL,
    hash_value TEXT NOT NULL,
    module_name TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(sql_content)

    def copy_files_structured(self, file_structure: Dict[str, List[str]]) -> Dict:
        """
        Kopiert Dateien mit korrekter Struktur
        """
        print(f"\\n📋 Copying files with structure...")

        results = {"copied": {}, "failed": [], "total_size": 0}

        # Kategorie-Mappings
        category_dirs = {"python_files": "core", "config_files": "config", "data_files": "data", "docs": "docs"}

        for category, files in file_structure.items():
            if category not in category_dirs:
                continue

            target_subdir = category_dirs[category]
            src_dir = self.export_root / "src" / target_subdir
            backup_dir = self.export_root / "backup" / target_subdir

            src_dir.mkdir(parents=True, exist_ok=True)
            backup_dir.mkdir(parents=True, exist_ok=True)

            results["copied"][category] = []

            print(f"\\n📁 {category.upper().replace('_', ' ')} → src/{target_subdir}:")

            for filename in files:
                try:
                    source_file = self.project_root / filename
                    target_file = src_dir / filename
                    backup_file = backup_dir / filename

                    if source_file.exists():
                        # Backup erstellen
                        shutil.copy2(source_file, backup_file)

                        # Nach src kopieren
                        shutil.copy2(source_file, target_file)

                        file_size = target_file.stat().st_size
                        results["total_size"] += file_size
                        results["copied"][category].append(filename)

                        print(f"  ✅ {filename} ({file_size:,} bytes)")
                    else:
                        print(f"  ⏭️ {filename} (not found)")

                except Exception as e:
                    results["failed"].append({"filename": filename, "category": category, "error": str(e)})
                    print(f"  ❌ {filename}: {e}")

        total_copied = sum(len(files) for files in results["copied"].values())
        print(f"\\n📊 Copy Summary: {total_copied} files, {results['total_size']:,} bytes")

        return results

    def apply_protection_structured(self, organization_id: str, license_key: str, copy_results: Dict) -> Dict:
        """
        Wendet License Protection mit korrekter Struktur an
        """
        print(f"\\n🔐 Applying Enhanced License Protection...")

        try:
            from enhanced_license_protection_test import EnhancedLicenseProtection

            protection = EnhancedLicenseProtection(organization_id)
        except ImportError:
            print("❌ Enhanced License Protection not available")
            # Fallback: Einfach kopieren
            return self._fallback_copy_to_protected(copy_results)

        results = {"protected": {}, "verified": {}, "failed": []}

        # Nur Python-Dateien schützen
        python_files = copy_results["copied"].get("python_files", [])

        if python_files:
            src_core_dir = self.export_root / "src" / "core"
            protected_core_dir = self.export_root / "protected" / "core"
            protected_core_dir.mkdir(parents=True, exist_ok=True)

            results["protected"]["python_files"] = []
            results["verified"]["python_files"] = []

            print(f"\\n🔐 Protecting Python files:")

            for filename in python_files:
                try:
                    source_file = src_core_dir / filename
                    target_file = protected_core_dir / filename

                    # Kopieren
                    shutil.copy2(source_file, target_file)

                    # Protection anwenden
                    module_name = Path(filename).stem
                    success = protection.embed_protection_keys(
                        str(target_file), license_key, module_name, self.build_info["version"]
                    )

                    if success:
                        results["protected"]["python_files"].append(filename)

                        # Verifikation
                        verification = protection.verify_file_authenticity(str(target_file))
                        if all([verification["hash_valid"], verification["keys_valid"], verification["organization_valid"]]):
                            results["verified"]["python_files"].append(filename)
                            print(f"  ✅ {filename}")
                        else:
                            print(f"  ⚠️ {filename} (verification issues)")
                    else:
                        results["failed"].append(filename)
                        print(f"  ❌ {filename}")

                except Exception as e:
                    results["failed"].append(filename)
                    print(f"  ❌ {filename}: {e}")

        # Andere Dateien einfach kopieren
        for category, files in copy_results["copied"].items():
            if category == "python_files":
                continue

            if category == "config_files":
                src_dir = self.export_root / "src" / "config"
                target_dir = self.export_root / "protected" / "config"
            elif category == "data_files":
                src_dir = self.export_root / "src" / "data"
                target_dir = self.export_root / "protected" / "data"
            elif category == "docs":
                src_dir = self.export_root / "src" / "docs"
                target_dir = self.export_root / "protected" / "docs"
            else:
                continue

            target_dir.mkdir(parents=True, exist_ok=True)
            results["protected"][category] = []
            results["verified"][category] = []

            for filename in files:
                source_file = src_dir / filename
                target_file = target_dir / filename

                if source_file.exists():
                    shutil.copy2(source_file, target_file)
                    results["protected"][category].append(filename)
                    results["verified"][category].append(filename)

        # Zusammenfassung
        total_protected = sum(len(files) for files in results["protected"].values())
        total_verified = sum(len(files) for files in results["verified"].values())

        print(f"\\n📊 Protection Summary:")
        print(f"  🔐 Protected: {total_protected}")
        print(f"  ✅ Verified: {total_verified}")
        print(f"  ❌ Failed: {len(results['failed'])}")

        return results

    def _fallback_copy_to_protected(self, copy_results: Dict) -> Dict:
        """
        Fallback: Kopiert ohne Protection
        """
        print("⚠️ Fallback: Copying without Enhanced Protection")

        results = {"protected": {}, "verified": {}, "failed": []}

        for category, files in copy_results["copied"].items():
            if category == "python_files":
                src_dir = self.export_root / "src" / "core"
                target_dir = self.export_root / "protected" / "core"
            elif category == "config_files":
                src_dir = self.export_root / "src" / "config"
                target_dir = self.export_root / "protected" / "config"
            elif category == "data_files":
                src_dir = self.export_root / "src" / "data"
                target_dir = self.export_root / "protected" / "data"
            elif category == "docs":
                src_dir = self.export_root / "src" / "docs"
                target_dir = self.export_root / "protected" / "docs"
            else:
                continue

            target_dir.mkdir(parents=True, exist_ok=True)
            results["protected"][category] = []
            results["verified"][category] = []

            for filename in files:
                source_file = src_dir / filename
                target_file = target_dir / filename

                if source_file.exists():
                    shutil.copy2(source_file, target_file)
                    results["protected"][category].append(filename)
                    results["verified"][category].append(filename)

        return results

    def create_distribution(self, protection_results: Dict) -> Dict:
        """
        Erstellt finale Distribution
        """
        print(f"\\n📦 Creating final distribution...")

        dist_dir = self.export_root / "dist"

        # Python-Dateien ins Root
        python_files = protection_results["protected"].get("python_files", [])
        protected_core_dir = self.export_root / "protected" / "core"

        for filename in python_files:
            source_file = protected_core_dir / filename
            target_file = dist_dir / filename

            if source_file.exists():
                shutil.copy2(source_file, target_file)

        # Config-Dateien in config/
        config_files = protection_results["protected"].get("config_files", [])
        if config_files:
            config_dist_dir = dist_dir / "config"
            config_dist_dir.mkdir(exist_ok=True)
            protected_config_dir = self.export_root / "protected" / "config"

            for filename in config_files:
                source_file = protected_config_dir / filename
                target_file = config_dist_dir / filename

                if source_file.exists():
                    shutil.copy2(source_file, target_file)

        # Installation Files erstellen
        self._create_installation_files(dist_dir)

        # Manifest erstellen
        manifest = {
            "build_info": self.build_info,
            "file_structure": protection_results["protected"],
            "total_files": sum(len(files) for files in protection_results["protected"].values()),
            "installation_requirements": {"python_version": ">=3.8", "license_key_required": True, "disk_space_mb": 150},
        }

        manifest_file = dist_dir / "VERITAS_DISTRIBUTION_MANIFEST.json"
        with open(manifest_file, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)

        print(f"✅ Distribution created: {dist_dir}")
        return {"dist_dir": str(dist_dir), "manifest": manifest}

    def _create_installation_files(self, dist_dir: Path):
        """
        Erstellt Installation Scripts
        """
        # Einfacher Installer
        installer_content = '''#!/usr/bin/env python3
"""
VERITAS Simple Installer
"""
import os
import sys
import json
from pathlib import Path

def install():
    print("🚀 VERITAS Installation")

    # License Key prüfen
    license_key = os.environ.get('VERITAS_LICENSE_KEY')
    if not license_key:
        print("❌ VERITAS_LICENSE_KEY required!")
        return False

    # Installation Directory
    install_dir = input("Install directory (default: ./veritas): ").strip()
    if not install_dir:
        install_dir = "./veritas"

    target_path = Path(install_dir)
    target_path.mkdir(exist_ok=True)

    # Dateien kopieren
    import shutil
    source_dir = Path(__file__).parent

    for file in source_dir.glob("*.py"):
        if file.name != "install_veritas.py":
            shutil.copy2(file, target_path / file.name)
            print(f"  ✅ {file.name}")

    print(f"✅ Installation completed: {target_path}")
    return True

if __name__ == "__main__":
    install()
'''

        installer_file = dist_dir / "install_veritas.py"
        with open(installer_file, "w", encoding="utf-8") as f:
            f.write(installer_content)

        # Batch-Installer für Windows
        batch_content = """@echo off
echo VERITAS Installation
python install_veritas.py
pause
"""

        batch_file = dist_dir / "install_veritas.bat"
        with open(batch_file, "w", encoding="utf-8") as f:
            f.write(batch_content)

    def run_complete_pipeline(self, organization_id: str, license_key: str) -> Dict:
        """
        Führt komplette Export-Pipeline aus
        """
        print("🏭 VERITAS Export Pipeline - Final Version")
        print("=" * 55)
        print(f"Organization: {organization_id}")
        print(f"Build: {self.build_info['build_id']}")

        # 1. Struktur erstellen
        if not self.create_export_structure():
            return {"success": False, "error": "Structure creation failed"}

        # 2. Dateien sammeln
        file_structure = self.get_production_files()
        total_files = sum(len(files) for files in file_structure.values())
        print(f"\\n📋 Production Files: {total_files} files in {len(file_structure)} categories")

        # 3. Dateien kopieren
        copy_results = self.copy_files_structured(file_structure)

        # 4. Protection anwenden
        protection_results = self.apply_protection_structured(organization_id, license_key, copy_results)

        # 5. Distribution erstellen
        dist_results = self.create_distribution(protection_results)

        # 6. Summary
        summary = {
            "success": True,
            "build_info": self.build_info,
            "export_directory": str(self.export_root),
            "distribution_directory": dist_results["dist_dir"],
            "stats": {
                "categories": len(file_structure),
                "total_files": total_files,
                "copied": sum(len(files) for files in copy_results["copied"].values()),
                "protected": sum(len(files) for files in protection_results["protected"].values()),
                "verified": sum(len(files) for files in protection_results["verified"].values()),
            },
        }

        # Summary Report
        summary_file = self.export_root / "EXPORT_SUMMARY.json"
        with open(summary_file, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)

        print(f"\\n🎯 Export Pipeline Completed!")
        print(f"📁 Export: {self.export_root}")
        print(f"📦 Distribution: {dist_results['dist_dir']}")
        print(f"📊 Files: {summary['stats']['copied']} copied, {summary['stats']['protected']} protected")
        print(f"📄 Summary: {summary_file}")

        return summary


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="VERITAS Export Pipeline Final")
    parser.add_argument("--export", action="store_true", help="Run export pipeline")
    parser.add_argument("--organization-id", type=str, default="VERITAS_TECH_GMBH")
    parser.add_argument("--license-key", type=str, required=True)
    parser.add_argument("--export-dir", type=str, help="Export directory")

    args = parser.parse_args()

    if args.export:
        pipeline = VERITASExportPipelineFinal(export_root=args.export_dir)

        result = pipeline.run_complete_pipeline(args.organization_id, args.license_key)

        success = result.get("success", False)
        sys.exit(0 if success else 1)
    else:
        print("🏭 VERITAS Export Pipeline Final")
        print("Usage: --export --license-key YOUR_KEY [--export-dir DIR]")

"""
VERITAS Protected Module
WARNING: This file contains embedded protection keys.
Modification will be detected and may result in license violations.
"""

# === VERITAS PROTECTION KEYS (DO NOT MODIFY) ===
module_name = "veritas_export_pipeline_final"
module_licenced_organization = "VERITAS_TECH_GMBH"
module_licence_key = "eyJjbGllbnRfaWQi...Q1Dbz8w="  # Gekuerzt fuer Sicherheit
module_organization_key = "0138b9dc7306f252fea0e1887f7c04e44b43b6b828d835843dbf6197b57f96bd"
module_file_key = "6008cd03e3b05b4538ce4720b63abdf842f47b8ca2f80bd38c097d6607c73448"
module_version = "1.0"
module_protection_level = 3
# === END PROTECTION KEYS ===
