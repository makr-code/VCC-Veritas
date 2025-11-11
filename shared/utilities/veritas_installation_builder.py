#!/usr/bin/env python3
"""
VERITAS Installation Builder - Finale Production Pipeline
Erstellt selbstextrahierende Installation Packages
"""

import json
import os
import sys
import time
import zipfile
from pathlib import Path
from typing import Dict, List


class VERITASInstallationBuilder:
    """
    Erstellt selbstextrahierende Installation Packages für VERITAS
    """

    def __init__(self, export_root: str = None):
        self.export_root = Path(export_root or "veritas_export")
        self.dist_dir = self.export_root / "dist"
        self.installer_dir = self.export_root / "installer"

    def create_installation_package(self, package_name: str = None) -> Dict:
        """
        Erstellt ein komplettes Installation Package
        """
        if package_name is None:
            timestamp = str(int(time.time()))[-8:]
            package_name = f"VERITAS_v1.0.0_Build{timestamp}"

        print(f"📦 Creating Installation Package: {package_name}")
        print("=" * 60)

        # Installer-Verzeichnis erstellen
        self.installer_dir.mkdir(exist_ok=True)
        package_dir = self.installer_dir / package_name
        package_dir.mkdir(exist_ok=True)

        # 1. Distribution Files kopieren
        if not self.dist_dir.exists():
            print("❌ Distribution directory not found!")
            print("   Run export pipeline first!")
            return {"success": False, "error": "No distribution"}

        print("\\n📋 Copying distribution files...")
        import shutil

        # Alle Dateien aus dist/ kopieren
        copied_files = []
        for item in self.dist_dir.iterdir():
            if item.is_file():
                target_file = package_dir / item.name
                shutil.copy2(item, target_file)
                copied_files.append(item.name)
                print(f"  ✅ {item.name}")

        # 2. Enhanced Installation Script erstellen
        enhanced_installer = self._create_enhanced_installer()
        installer_script = package_dir / "install_veritas_enhanced.py"
        with open(installer_script, "w", encoding="utf-8") as f:
            f.write(enhanced_installer)
        print("  ✅ install_veritas_enhanced.py")

        # 3. Batch Installation Script (Windows)
        batch_installer = self._create_batch_installer()
        batch_script = package_dir / "install_veritas.bat"
        with open(batch_script, "w", encoding="utf-8") as f:
            f.write(batch_installer)
        print(f"  ✅ install_veritas.bat")

        # 4. Verification Script
        verification_script = self._create_verification_script()
        verify_script = package_dir / "verify_installation.py"
        with open(verify_script, "w", encoding="utf-8") as f:
            f.write(verification_script)
        print(f"  ✅ verify_installation.py")

        # 5. README & Documentation
        readme_content = self._create_installation_readme()
        readme_file = package_dir / "README_INSTALLATION.md"
        with open(readme_file, "w", encoding="utf-8") as f:
            f.write(readme_content)
        print(f"  ✅ README_INSTALLATION.md")

        # 6. Package als ZIP erstellen
        zip_package = self.installer_dir / f"{package_name}.zip"
        print("\\n📦 Creating ZIP package...")

        with zipfile.ZipFile(zip_package, "w", zipfile.ZIP_DEFLATED) as zipf:
            for file_path in package_dir.rglob("*"):
                if file_path.is_file():
                    arc_name = file_path.relative_to(package_dir)
                    zipf.write(file_path, arc_name)
                    print(f"  ✅ {arc_name}")

        package_size = zip_package.stat().st_size
        print("\\n📊 Package Results:")
        print(f"  📁 Package Directory: {package_dir}")
        print(f"  📦 ZIP Package: {zip_package}")
        print(f"  💾 Package Size: {package_size:,} bytes")
        print(f"  📄 Files: {len(copied_files) + 4}")  # +4 für die zusätzlichen Scripts

        # 7. Installation Instructions erstellen
        instructions = self._create_deployment_instructions(package_name, zip_package)
        instructions_file = self.installer_dir / f"{package_name}_DEPLOYMENT_INSTRUCTIONS.md"
        with open(instructions_file, "w", encoding="utf-8") as f:
            f.write(instructions)

        return {
            "success": True,
            "package_name": package_name,
            "package_directory": str(package_dir),
            "zip_package": str(zip_package),
            "package_size": package_size,
            "files_count": len(copied_files) + 4,
            "deployment_instructions": str(instructions_file),
        }

    def _create_enhanced_installer(self) -> str:
        """
        Erstellt Enhanced Installation Script
        """
        return '''#!/usr/bin/env python3
"""
VERITAS Enhanced Installation Script
Production-grade installation with verification and configuration
"""

import os
import sys
import json
import shutil
import hashlib
from pathlib import Path

class VERITASInstaller:
    """
    Enhanced VERITAS Installation Manager
    """

    def __init__(self):
        self.install_dir = None
        self.license_key = None
        self.manifest = None

    def load_manifest(self):
        """Lädt Installation Manifest"""
        manifest_file = Path(__file__).parent / "VERITAS_DISTRIBUTION_MANIFEST.json"
        if not manifest_file.exists():
            raise FileNotFoundError("Distribution manifest not found!")

        with open(manifest_file, 'r') as f:
            self.manifest = json.load(f)

        print("📋 Manifest loaded:")
        print(f"   Build: {self.manifest['build_info']['build_id']}")
        print(f"   Files: {self.manifest['total_files']}")

    def check_license_key(self):
        """Prüft License Key"""
        self.license_key = os.environ.get('VERITAS_LICENSE_KEY')
        if not self.license_key:
            print("\\n🔑 License Key Setup Required")
            print("Option 1: Set environment variable")
            print("   Windows: set VERITAS_LICENSE_KEY=your_license_key")
            print("   Linux:   export VERITAS_LICENSE_KEY=your_license_key")
            print("\\nOption 2: Enter manually")

            manual_key = input("Enter license key (or press Enter to exit): ").strip()
            if manual_key:
                self.license_key = manual_key
                os.environ['VERITAS_LICENSE_KEY'] = manual_key
            else:
                print("❌ License key required for installation!")
                return False

        print(f"✅ License key: {self.license_key[:20]}...")
        return True

    def select_installation_directory(self):
        """Wählt Installation Directory"""
        print("\\n📁 Installation Directory")
        default_dir = str(Path.home() / "VERITAS")

        user_dir = input(f"Install directory (default: {default_dir}): ").strip()
        self.install_dir = Path(user_dir if user_dir else default_dir)

        if self.install_dir.exists():
            if any(self.install_dir.iterdir()):
                overwrite = input("Directory exists and not empty. Overwrite? (y/N): ").lower()
                if overwrite != 'y':
                    print("❌ Installation cancelled")
                    return False

        self.install_dir.mkdir(parents=True, exist_ok=True)
        print(f"✅ Installation directory: {self.install_dir}")
        return True

    def install_files(self):
        """Installiert VERITAS Dateien"""
        print("\\n📦 Installing VERITAS files...")

        source_dir = Path(__file__).parent
        installed_files = []

        for filename in self.manifest['files']:
            source_file = source_dir / filename
            target_file = self.install_dir / filename

            if source_file.exists():
                # Verzeichnis erstellen falls nötig
                target_file.parent.mkdir(parents=True, exist_ok=True)

                # Datei kopieren
                shutil.copy2(source_file, target_file)
                installed_files.append(filename)
                print(f"  ✅ {filename}")
            else:
                print(f"  ❌ {filename} (source not found)")

        print(f"\\n📊 Installation: {len(installed_files)} files installed")
        return installed_files

    def create_configuration(self):
        """Erstellt VERITAS Konfiguration"""
        config = {
            "installation": {
                "directory": str(self.install_dir),
                "timestamp": time.time(),
                "license_key_set": bool(self.license_key)
            },
            "build_info": self.manifest['build_info'],
            "python_path": str(self.install_dir)
        }

        config_file = self.install_dir / "veritas_config.json"
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)

        print(f"  ✅ Configuration: {config_file}")
        return config_file

    def run_installation(self):
        """Führt komplette Installation aus"""
        print("🚀 VERITAS Enhanced Installation")
        print("=" * 40)

        try:
            # 1. Manifest laden
            self.load_manifest()

            # 2. License Key prüfen
            if not self.check_license_key():
                return False

            # 3. Installation Directory
            if not self.select_installation_directory():
                return False

            # 4. Dateien installieren
            installed_files = self.install_files()

            # 5. Konfiguration erstellen
            config_file = self.create_configuration()

            # 6. Erfolgs-Meldung
            print("\\n🎉 VERITAS Installation SUCCESSFUL!")
            print(f"   📁 Location: {self.install_dir}")
            print(f"   📄 Files: {len(installed_files)}")
            print(f"   ⚙️ Config: {config_file}")
            print("\\n🔍 Next Steps:")
            print(f"   1. Add to Python path: {self.install_dir}")
            print("   2. Run verification: python verify_installation.py")
            print(f"   3. Test import: from shared.core.veritas_core import *")

            return True

        except Exception as e:
            print(f"❌ Installation failed: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    import time

    installer = VERITASInstaller()
    success = installer.run_installation()
    sys.exit(0 if success else 1)
'''

    def _create_batch_installer(self) -> str:
        """Erstellt Windows Batch Installer"""
        return """@echo off
echo ========================================
echo VERITAS Installation (Windows)
echo ========================================

echo Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found!
    echo Please install Python 3.8+ and try again.
    pause
    exit /b 1
)

echo Python found. Starting installation...
python install_veritas_enhanced.py

echo.
echo Installation completed.
echo.
echo To verify installation:
echo   python verify_installation.py
echo.
pause
"""

    def _create_verification_script(self) -> str:
        """Erstellt Verification Script"""
        return '''#!/usr/bin/env python3
"""
VERITAS Installation Verification
Prüft Installation und License Protection
"""

import os
import sys
import json
from pathlib import Path

def verify_installation():
    """
    Verifiziert VERITAS Installation
    """
    print("🔍 VERITAS Installation Verification")
    print("=" * 40)

    # 1. Konfiguration laden
    config_file = Path("veritas_config.json")
    if not config_file.exists():
        print("❌ Configuration file not found!")
        return False

    with open(config_file, 'r') as f:
        config = json.load(f)

    install_dir = Path(config['installation']['directory'])
    print(f"📁 Installation: {install_dir}")

    # 2. License Key prüfen
    license_key = os.environ.get('VERITAS_LICENSE_KEY')
    if not license_key:
        print("❌ VERITAS_LICENSE_KEY not set!")
        return False

    print(f"🔑 License: {license_key[:20]}...")

    # 3. Core Module Test
    print("\\n🧪 Testing core modules...")

    try:
        sys.path.insert(0, str(install_dir))

        # Test imports
        import shared.core.veritas_core as veritas_core
        print("  ✅ veritas_core")

        import license_protection_system
        print("  ✅ license_protection_system")

        import database_manager
        print("  ✅ database_manager")

    except ImportError as e:
        print(f"  ❌ Import failed: {e}")
        return False

    # 4. License Protection Test
    print("\\n🔐 Testing license protection...")

    try:
        from license_protection_integration import protection_integrator
        status = protection_integrator.get_protection_status()

        print(f"  License Valid: {status.get('license_valid', False)}")
        print(f"  Protection Level: {status.get('protection_level', 0)}")

        if not status.get('license_valid', False):
            print("  ⚠️ License validation issues")
            return False

    except Exception as e:
        print(f"  ❌ Protection test failed: {e}")
        return False

    print("\\n🎉 Verification SUCCESSFUL!")
    print("   VERITAS is ready to use!")
    return True

if __name__ == "__main__":
    success = verify_installation()
    sys.exit(0 if success else 1)
'''

    def _create_installation_readme(self) -> str:
        """Erstellt Installation README"""
        return """# VERITAS Installation Guide

## Overview
This package contains a complete VERITAS distribution with Enhanced License Protection.

## Installation Requirements
- Python 3.8 or higher
- Valid VERITAS license key
- 50+ MB disk space

## Quick Installation (Windows)
1. Extract this package to a temporary directory
2. Set your license key: `set VERITAS_LICENSE_KEY=your_license_key`
3. Run: `install_veritas.bat`
4. Follow the prompts

## Manual Installation (All Platforms)
1. Extract this package
2. Set license key environment variable:
   - Windows: `set VERITAS_LICENSE_KEY=your_license_key`
   - Linux/Mac: `export VERITAS_LICENSE_KEY=your_license_key`
3. Run: `python install_veritas_enhanced.py`
4. Choose installation directory
5. Verify: `python verify_installation.py`

## Post-Installation
1. Add installation directory to Python path
2. Test imports: `python -c "import shared.core.veritas_core as veritas_core"`
3. Check license: `python -c "from license_protection_integration import protection_integrator; print(protection_integrator.get_protection_status())"`

## Files Included
- VERITAS core modules (20 files)
- Enhanced License Protection
- Database APIs
- Quality management systems
- GUI applications

## Troubleshooting
- License issues: Ensure VERITAS_LICENSE_KEY is set correctly
- Import errors: Check Python path includes installation directory
- Permission errors: Run as administrator/sudo if needed

## Support
For technical support, contact your VERITAS license provider.

Build Info: See VERITAS_DISTRIBUTION_MANIFEST.json
"""

    def _create_deployment_instructions(self, package_name: str, zip_path: Path) -> str:
        """Erstellt Deployment Instructions"""
        return """# VERITAS Deployment Instructions

## Package Information
- **Package Name**: {package_name}
- **Package File**: {zip_path.name}
- **Package Size**: {zip_path.stat().st_size:,} bytes
- **Created**: {time.strftime('%Y-%m-%d %H:%M:%S')}

## Deployment Steps

### 1. Package Distribution
```bash
# Copy package to target systems
scp {zip_path.name} user@target-server:/tmp/
```

### 2. Remote Installation
```bash
# Extract package
unzip {zip_path.name}
cd {package_name}

# Set license key
export VERITAS_LICENSE_KEY="your_license_key_here"

# Run installation
python install_veritas_enhanced.py

# Verify installation
python verify_installation.py
```

### 3. Batch Deployment Script
```bash
#!/bin/bash
# batch_deploy.sh

SERVERS="server1 server2 server3"
LICENSE_KEY="your_license_key"
PACKAGE="{zip_path.name}"

for server in $SERVERS; do
    echo "Deploying to $server..."

    # Copy package
    scp $PACKAGE user@$server:/tmp/

    # Remote installation
    ssh user@$server << EOF
        cd /tmp
        unzip -o $PACKAGE
        cd {package_name}
        export VERITAS_LICENSE_KEY="$LICENSE_KEY"
        python install_veritas_enhanced.py
        python verify_installation.py
EOF

    echo "Deployment to $server completed."
done
```

### 4. Docker Deployment
```dockerfile
FROM python:3.9-slim

# Copy package
COPY {zip_path.name} /tmp/

# Extract and install
RUN cd /tmp && \\
    unzip {zip_path.name} && \\
    cd {package_name} && \\
    python install_veritas_enhanced.py

# Set license key
ENV VERITAS_LICENSE_KEY="your_license_key"

# Verify installation
RUN cd /tmp/{package_name} && python verify_installation.py

WORKDIR /app
CMD ["python", "-c", "import shared.core.veritas_core as veritas_core; print('VERITAS ready')"]
```

## Security Considerations
- License keys contain sensitive information
- Store license keys securely (environment variables, secrets management)
- Verify package integrity before deployment
- Use secure channels for package distribution

## Production Checklist
- [ ] Package integrity verified
- [ ] License keys distributed securely
- [ ] Target systems meet requirements
- [ ] Backup existing installations
- [ ] Test deployment on staging environment
- [ ] Monitor installation logs
- [ ] Verify post-installation functionality

## Package Contents
This package includes all necessary VERITAS components with Enhanced License Protection:
- Core system modules
- Database connectivity
- API endpoints
- Quality management
- GUI applications
- Installation and verification tools

Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}
Package: {package_name}
"""


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="VERITAS Installation Builder")
    parser.add_argument("--build", action="store_true", help="Build installation package")
    parser.add_argument("--export-dir", type=str, default="veritas_export", help="Export directory")
    parser.add_argument("--package-name", type=str, help="Package name (auto-generated if not provided)")

    args = parser.parse_args()

    if args.build:
        builder = VERITASInstallationBuilder(args.export_dir)
        result = builder.create_installation_package(args.package_name)

        if result["success"]:
            print("\\n🎉 Installation Package READY!")
            print(f"📦 Package: {result['zip_package']}")
            print(f"📋 Instructions: {result['deployment_instructions']}")
        else:
            print("\\n❌ Package creation failed!")

        sys.exit(0 if result["success"] else 1)
    else:
        print("🏭 VERITAS Installation Builder")
        print("Usage: --build [--package-name NAME] [--export-dir DIR]")

"""
VERITAS Protected Module
WARNING: This file contains embedded protection keys.
Modification will be detected and may result in license violations.
"""

# === VERITAS PROTECTION KEYS (DO NOT MODIFY) ===
module_name = "veritas_installation_builder"
module_licenced_organization = "VERITAS_TECH_GMBH"
module_licence_key = "eyJjbGllbnRfaWQi...rkAWcaE="  # Gekuerzt fuer Sicherheit
module_organization_key = "847cff8f9586d0857c2fece9f8c368508212b8ee1d2eac9440fd7f933d8dd9da"
module_file_key = "8ae175d0fcf6f5ce1a8af7c86dc2764aa5ab3e45294bc80a2db7e0c3a4e0f35a"
module_version = "1.0"
module_protection_level = 3
# === END PROTECTION KEYS ===
