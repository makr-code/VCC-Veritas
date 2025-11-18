#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VERITAS API Startup Manager
Intelligenter Startup-Manager für das VERITAS API-System mit Port-Management,
Dependency-Checks und automatischer Konfiguration.
"""

import logging
import os
import signal
import socket
import subprocess
import sys
import time
from pathlib import Path
from typing import List, Optional, Tuple

import psutil

# Logging Setup
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class VeritasAPIManager:
    """Manager für VERITAS API-System mit intelligenter Port-Verwaltung"""

    def __init__(self, default_port: int = 5000, host: str = "0.0.0.0"):
        self.default_port = default_port
        self.host = host
        self.current_port = None
        self.process = None
        self.project_root = Path(__file__).parent

    def check_port_availability(self, port: int) -> bool:
        """Prüft ob ein Port verfügbar ist"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(1)
                result = sock.connect_ex((self.host, port))
                return result != 0
        except Exception as e:
            logger.error(f"Port-Check Fehler: {e}")
            return False

    def find_available_port(self, start_port: int = None, max_attempts: int = 20) -> Optional[int]:
        """Findet verfügbaren Port"""
        start = start_port or self.default_port

        for port in range(start, start + max_attempts):
            if self.check_port_availability(port):
                return port
        return None

    def find_veritas_processes(self) -> List[Tuple[int, str]]:
        """Findet laufende VERITAS-Prozesse"""
        veritas_processes = []

        try:
            for proc in psutil.process_iter(["pid", "name", "cmdline"]):
                try:
                    cmdline = " ".join(proc.info["cmdline"] or [])
                    if (
                        "api_endpoint.py" in cmdline
                        or "veritas" in cmdline.lower()
                        or "uvicorn" in cmdline
                        and "5000" in cmdline
                    ):
                        veritas_processes.append((proc.info["pid"], cmdline))
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

        except Exception as e:
            logger.error(f"Prozess-Scan Fehler: {e}")

        return veritas_processes

    def check_dependencies(self) -> bool:
        """Prüft erforderliche Dependencies"""
        required_modules = ["fastapi", "uvicorn", "pydantic", "requests"]

        missing_modules = []

        for module in required_modules:
            try:
                __import__(module)
                logger.info(f"✅ {module} verfügbar")
            except ImportError:
                missing_modules.append(module)
                logger.error(f"❌ {module} fehlt")

        if missing_modules:
            logger.error(f"🚨 Fehlende Dependencies: {', '.join(missing_modules)}")
            logger.info("💡 Installation: pip install fastapi uvicorn pydantic requests")
            return False

        return True

    def kill_conflicting_processes(self) -> bool:
        """Beendet konflikierende VERITAS-Prozesse"""
        processes = self.find_veritas_processes()

        if not processes:
            return True

        logger.warning(f"🔍 {len(processes)} laufende VERITAS-Prozesse gefunden:")
        for pid, cmdline in processes:
            logger.warning(f"  PID {pid}: {cmdline[:80]}...")

        response = input("\n🤔 Sollen diese Prozesse beendet werden? (y/N): ").strip().lower()

        if response == "y":
            killed_count = 0
            for pid, cmdline in processes:
                try:
                    proc = psutil.Process(pid)
                    proc.terminate()
                    proc.wait(timeout=5)
                    logger.info(f"✅ Prozess {pid} beendet")
                    killed_count += 1
                except psutil.TimeoutExpired:
                    try:
                        proc.kill()
                        logger.info(f"🔥 Prozess {pid} forciert beendet")
                        killed_count += 1
                    except Exception as e:
                        logger.error(f"❌ Konnte Prozess {pid} nicht beenden: {e}")
                except Exception as e:
                    logger.error(f"❌ Fehler beim Beenden von Prozess {pid}: {e}")

            if killed_count > 0:
                logger.info(f"✅ {killed_count} Prozesse beendet")
                time.sleep(2)  # Kurz warten damit Ports freigegeben werden
                return True

        return False

    def start_api_server(self, port: int = None) -> bool:
        """Startet API-Server"""
        target_port = port or self.current_port or self.default_port

        try:
            logger.info(f"🚀 Starte VERITAS API auf Port {target_port}...")

            # API im Hintergrund starten
            cmd = [sys.executable, "api_endpoint.py"]

            # Environment-Variablen setzen
            env = os.environ.copy()
            env["VERITAS_PORT"] = str(target_port)
            env["VERITAS_HOST"] = self.host

            self.process = subprocess.Popen(
                cmd, cwd=self.project_root, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True
            )

            # Warten auf Server-Start
            startup_timeout = 30
            for i in range(startup_timeout):
                if self.process.poll() is not None:
                    # Prozess beendet
                    output = self.process.stdout.read()
                    logger.error(f"❌ API-Server konnte nicht gestartet werden:")
                    logger.error(output)
                    return False

                # Prüfen ob Server läuft
                if not self.check_port_availability(target_port):
                    logger.info(f"✅ API-Server erfolgreich gestartet auf Port {target_port}")
                    self.current_port = target_port
                    return True

                time.sleep(1)

            logger.error(f"❌ Server-Start Timeout nach {startup_timeout}s")
            return False

        except Exception as e:
            logger.error(f"❌ Server-Start Fehler: {e}")
            return False

    def stop_api_server(self):
        """Stoppt API-Server"""
        if self.process:
            try:
                logger.info("🛑 Stoppe API-Server...")
                self.process.terminate()
                self.process.wait(timeout=10)
                logger.info("✅ API-Server gestoppt")
            except subprocess.TimeoutExpired:
                logger.warning("⚠️ Forciere Server-Stop...")
                self.process.kill()
                self.process.wait()
                logger.info("🔥 API-Server forciert gestoppt")
            except Exception as e:
                logger.error(f"❌ Server-Stop Fehler: {e}")
            finally:
                self.process = None
                self.current_port = None

    def show_server_info(self):
        """Zeigt Server-Informationen"""
        if self.current_port:
            print(f"\n🌐 VERITAS API läuft auf:")
            print(f"   URL: http://localhost:{self.current_port}")
            print(f"   Dokumentation: http://localhost:{self.current_port}/docs")
            print(f"   Alternative Docs: http://localhost:{self.current_port}/redoc")
            print(f"   Health Check: http://localhost:{self.current_port}/health")
            print(f"\n💡 Zum Stoppen: Ctrl+C oder 'stop' eingeben")

    def interactive_mode(self):
        """Interaktiver Modus"""
        print("\n" + "=" * 60)
        print("VERITAS API MANAGEMENT KONSOLE")
        print("=" * 60)

        while True:
            try:
                if self.current_port:
                    cmd = input(f"\n[API:{self.current_port}] Befehl (stop/restart/info/help): ").strip().lower()
                else:
                    cmd = input("\n[API:gestoppt] Befehl (start/help/quit): ").strip().lower()

                if cmd in ["quit", "exit", "q"]:
                    break
                elif cmd == "start" and not self.current_port:
                    self.smart_startup()
                elif cmd == "stop" and self.current_port:
                    self.stop_api_server()
                elif cmd == "restart":
                    if self.current_port:
                        self.stop_api_server()
                    self.smart_startup()
                elif cmd == "info":
                    self.show_server_info()
                    if self.current_port:
                        processes = self.find_veritas_processes()
                        print(f"\n📊 Aktive Prozesse: {len(processes)}")
                elif cmd == "help":
                    self.show_help()
                elif cmd == "":
                    continue
                else:
                    print("❓ Unbekannter Befehl. 'help' für Hilfe.")

            except KeyboardInterrupt:
                print("\n🛑 Interrupt erkannt...")
                break
            except Exception as e:
                logger.error(f"❌ Befehl-Fehler: {e}")

        # Cleanup
        if self.current_port:
            self.stop_api_server()
        print("\n👋 VERITAS API Manager beendet")

    def show_help(self):
        """Zeigt Hilfe"""
        print(
            """
📚 VERITAS API MANAGER - BEFEHLE

Während API gestoppt:
  start    - API starten (mit automatischer Port-Suche)
  help     - Diese Hilfe anzeigen
  quit     - Manager beenden

Während API läuft:
  stop     - API stoppen
  restart  - API neu starten
  info     - Server-Informationen anzeigen
  help     - Diese Hilfe anzeigen
  quit     - API stoppen und Manager beenden

🔧 Tastenkombinationen:
  Ctrl+C   - API stoppen / Manager beenden
"""
        )

    def smart_startup(self) -> bool:
        """Intelligenter Startup mit allen Prüfungen"""
        logger.info("🔍 Starte intelligenten VERITAS API-Startup...")

        # 1. Dependencies prüfen
        if not self.check_dependencies():
            return False

        # 2. Port-Verfügbarkeit prüfen
        if not self.check_port_availability(self.default_port):
            logger.warning(f"⚠️ Standard-Port {self.default_port} ist belegt")

            # 3. Conflicting Processes finden
            processes = self.find_veritas_processes()
            if processes:
                if not self.kill_conflicting_processes():
                    # Alternative Port suchen
                    alternative_port = self.find_available_port(self.default_port + 1)
                    if alternative_port:
                        logger.info(f"✅ Alternativer Port gefunden: {alternative_port}")
                        self.current_port = alternative_port
                    else:
                        logger.error("❌ Keine verfügbaren Ports gefunden")
                        return False
            else:
                # Port belegt aber keine VERITAS-Prozesse
                alternative_port = self.find_available_port(self.default_port + 1)
                if alternative_port:
                    logger.info(f"✅ Alternativer Port gefunden: {alternative_port}")
                    self.current_port = alternative_port
                else:
                    logger.error("❌ Keine verfügbaren Ports gefunden")
                    return False
        else:
            self.current_port = self.default_port

        # 4. Server starten
        if self.start_api_server():
            self.show_server_info()
            return True

        return False


def main():
    """Hauptfunktion"""
    manager = VeritasAPIManager()

    try:
        # Kommandozeilen-Parameter prüfen
        if len(sys.argv) > 1:
            if sys.argv[1] == "--start":
                success = manager.smart_startup()
                if success:
                    try:
                        print("🔄 Server läuft... (Ctrl+C zum Stoppen)")
                        while True:
                            time.sleep(1)
                    except KeyboardInterrupt:
                        manager.stop_api_server()
                sys.exit(0 if success else 1)
            elif sys.argv[1] == "--help":
                manager.show_help()
                sys.exit(0)

        # Interaktiver Modus
        manager.interactive_mode()

    except KeyboardInterrupt:
        print("\n🛑 Manager durch Benutzer beendet")
        if manager.current_port:
            manager.stop_api_server()
    except Exception as e:
        logger.error(f"❌ Manager-Fehler: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

"""
VERITAS Protected Module
WARNING: This file contains embedded protection keys.
Modification will be detected and may result in license violations.
"""

# === VERITAS PROTECTION KEYS (DO NOT MODIFY) ===
module_name = "veritas_api_manager"
module_licenced_organization = "VERITAS_TECH_GMBH"
module_licence_key = "eyJjbGllbnRfaWQi...qtsqt4Y="  # Gekuerzt fuer Sicherheit
module_organization_key = "1d871d3886fa8b7e524f6a9baa81afda2afc404e7248dbd2ac6373baee288e1b"
module_file_key = "5ae2aeb00d1510ca6983b0751dabec8caac14de92da0a4a3355e257794ac46b2"
module_version = "1.0"
module_protection_level = 3
# === END PROTECTION KEYS ===
