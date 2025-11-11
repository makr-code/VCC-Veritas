#!/usr/bin/env python3
"""
VERITAS Production Scraper Manager
Produktiver Manager für alle VERITAS Scraper mit einheitlicher Orchestrierung
"""

import json
import logging
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

import schedule
from legacy_scrapers.scraper_bverwg_adapter import BVerwGRechtsprechungScraper

# === NEUE COMPREHENSIVE ADAPTER ===
from scraper_adapter_bund import BundComprehensiveScraper
from scraper_adapter_eu import EUComprehensiveScraper
from scraper_adapter_eu_cellar import EUCellarScraper
from scraper_bw_rechtsprechung_adapter import BWRechtsprechungScraper
from scraper_manager import ScraperManager, ScrapingJob, ScrapingResult
from scraper_vgh_bw_adapter import VGHBWRechtsprechungScraper


class VERITASProductionManager:
    """
    Production Manager für alle VERITAS Scraper
    Koordiniert tägliche Legal Updates und Produktionsworkflows
    """

    def __init__(self, config_path: str = None):
        """
        Initialisiert Production Manager

        Args:
            config_path: Pfad zur Konfigurationsdatei
        """
        self.config = self._load_config(config_path)
        self.logger = self._setup_logging()

        # Basis Manager
        self.scraper_manager = ScraperManager(self.config.get("scraper_config", {}))

        # Scraper Registry
        self.scrapers = {}
        self._initialize_scrapers()

        # Production Status
        self.production_status = {
            "last_run": None,
            "next_scheduled": None,
            "total_documents_today": 0,
            "errors_today": 0,
            "active_jobs": [],
        }

        # Scheduling
        self.scheduler_running = False
        self.scheduler_thread = None

        self.logger.info("VERITAS Production Manager initialized")

    def _load_config(self, config_path: str) -> Dict:
        """Lädt Produktionskonfiguration"""
        default_config = {
            "scraper_config": {"request_delay": 2.0, "data_dir": ". / data/production", "max_workers": 4, "timeout": 30},
            "production_schedule": {
                "daily_update_time": "06:00",
                "weekend_update_time": "08:00",
                "enable_hourly": False,
                "hourly_sources": ["eu_comprehensive", "bund_comprehensive", "eu_cellar", "bverwg"],
            },
            "scraping_limits": {
                "daily_total": 2000,
                "per_source": 200,
                "priority_sources": {
                    "bund_comprehensive": 400,
                    "eu_comprehensive": 400,
                    "bverwg": 300,
                    "eu_cellar": 300,
                    "vgh_bw": 200,
                    "bw_rechtsprechung": 200,
                },
            },
            "data_retention": {"raw_data_days": 30, "processed_data_days": 365, "cache_hours": 12},
            "notification": {"enable_email": False, "enable_slack": False, "error_threshold": 10},
        }

        if config_path and Path(config_path).exists():
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    user_config = json.load(f)
                default_config.update(user_config)
            except Exception as e:
                logging.warning(f"Failed to load config from {config_path}: {e}")

        return default_config

    def _setup_logging(self) -> logging.Logger:
        """Richtet Production Logging ein"""
        logger = logging.getLogger("VERITAS_Production")
        logger.setLevel(logging.INFO)

        # File Handler
        log_dir = Path(self.config["scraper_config"]["data_dir"]) / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(
            log_dir / f'veritas_production_{datetime.now().strftime("%Y%m%d")}.log', encoding="utf-8"
        )
        file_handler.setLevel(logging.INFO)

        # Console Handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        # Formatter
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

        return logger

    def _initialize_scrapers(self):
        """Initialisiert alle Production Scraper"""
        scraper_config = self.config["scraper_config"]

        # Baden-Württemberg Rechtsprechung
        self.scrapers["bw_rechtsprechung"] = BWRechtsprechungScraper("bw_rechtsprechung", scraper_config)

        # EU Cellar
        self.scrapers["eu_cellar"] = EUCellarScraper("eu_cellar", scraper_config)

        # VGH Baden-Württemberg
        self.scrapers["vgh_bw"] = VGHBWRechtsprechungScraper("vgh_bw", scraper_config)

        # BVerwG
        self.scrapers["bverwg"] = BVerwGRechtsprechungScraper("bverwg", scraper_config)

        # Bundesländer Comprehensive Adapter - Phase 1 (HTTP-basiert)
        from scraper_adapter_baden_wuerttemberg import BadenWuerttembergJurisComprehensiveScraper
        from scraper_adapter_bayern import BayernComprehensiveScraper

        # Bundesländer Comprehensive Adapter - Phase 2 (Juris JavaScript-basiert)
        from scraper_adapter_berlin import BerlinComprehensiveScraper
        from scraper_adapter_brandenburg import BrandenburgComprehensiveScraper
        from scraper_adapter_bremen import BremenComprehensiveScraper
        from scraper_adapter_hamburg import HamburgComprehensiveScraper
        from scraper_adapter_hessen import HessenComprehensiveScraper
        from scraper_adapter_hessen_lareda import HessenLAREDAComprehensiveScraper
        from scraper_adapter_mecklenburg_vorpommern import MecklenburgVorpommernComprehensiveScraper
        from scraper_adapter_niedersachsen import NiedersachsenComprehensiveScraper
        from scraper_adapter_nrw import NRWComprehensiveScraper
        from scraper_adapter_rheinland_pfalz import RheinlandPfalzComprehensiveScraper
        from scraper_adapter_saarland import SaarlandComprehensiveScraper

        # Bundesländer Comprehensive Adapter - Phase 3 (Remaining States)
        from scraper_adapter_sachsen import SachsenComprehensiveScraper
        from scraper_adapter_sachsen_anhalt import SachsenAnhaltComprehensiveScraper
        from scraper_adapter_schleswig_holstein import SchleswigHolsteinComprehensiveScraper
        from scraper_adapter_thueringen import ThueringenComprehensiveScraper

        # Phase 1 Adapter (HTTP-basiert)
        self.scrapers["bayern_comprehensive"] = BayernComprehensiveScraper(output_dir=f"{scraper_config['data_dir']}/bayern")

        self.scrapers["nrw_comprehensive"] = NRWComprehensiveScraper(output_dir=f"{scraper_config['data_dir']}/nrw")

        self.scrapers["hessen_comprehensive"] = HessenComprehensiveScraper(output_dir=f"{scraper_config['data_dir']}/hessen")

        self.scrapers["niedersachsen_comprehensive"] = NiedersachsenComprehensiveScraper(
            output_dir=f"{scraper_config['data_dir']}/niedersachsen"
        )

        # Phase 2 Adapter (Juris JavaScript-basiert mit Selenium)
        self.scrapers["berlin_comprehensive"] = BerlinComprehensiveScraper(output_dir=f"{scraper_config['data_dir']}/berlin")

        self.scrapers["schleswig_holstein_comprehensive"] = SchleswigHolsteinComprehensiveScraper(
            output_dir=f"{scraper_config['data_dir']}/schleswig_holstein"
        )

        self.scrapers["rheinland_pfalz_comprehensive"] = RheinlandPfalzComprehensiveScraper(
            output_dir=f"{scraper_config['data_dir']}/rheinland_pfalz"
        )

        self.scrapers["baden_wuerttemberg_juris_comprehensive"] = BadenWuerttembergJurisComprehensiveScraper(
            output_dir=f"{scraper_config['data_dir']}/baden_wuerttemberg"
        )

        self.scrapers["thueringen_comprehensive"] = ThueringenComprehensiveScraper(
            output_dir=f"{scraper_config['data_dir']}/thueringen"
        )

        self.scrapers["sachsen_anhalt_comprehensive"] = SachsenAnhaltComprehensiveScraper(
            output_dir=f"{scraper_config['data_dir']}/sachsen_anhalt"
        )

        self.scrapers["mecklenburg_vorpommern_comprehensive"] = MecklenburgVorpommernComprehensiveScraper(
            output_dir=f"{scraper_config['data_dir']}/mecklenburg_vorpommern"
        )

        self.scrapers["hessen_lareda_comprehensive"] = HessenLAREDAComprehensiveScraper(
            output_dir=f"{scraper_config['data_dir']}/hessen_lareda"
        )

        # Phase 3 Adapter (Remaining States)
        self.scrapers["sachsen_comprehensive"] = SachsenComprehensiveScraper(
            output_dir=f"{scraper_config['data_dir']}/sachsen"
        )

        self.scrapers["brandenburg_comprehensive"] = BrandenburgComprehensiveScraper(
            output_dir=f"{scraper_config['data_dir']}/brandenburg"
        )

        self.scrapers["saarland_comprehensive"] = SaarlandComprehensiveScraper(
            output_dir=f"{scraper_config['data_dir']}/saarland"
        )

        self.scrapers["hamburg_comprehensive"] = HamburgComprehensiveScraper(
            output_dir=f"{scraper_config['data_dir']}/hamburg"
        )

        self.scrapers["bremen_comprehensive"] = BremenComprehensiveScraper(output_dir=f"{scraper_config['data_dir']}/bremen")

        # === EU UND BUND COMPREHENSIVE ADAPTER ===

        # Bund Comprehensive (Gesetze, Rechtsprechung, Verwaltungsvorschriften)
        self.scrapers["bund_comprehensive"] = BundComprehensiveScraper(output_dir=f"{scraper_config['data_dir']}/bund")

        # EU Comprehensive (EUR-Lex, EU Cellar, ECHR)
        self.scrapers["eu_comprehensive"] = EUComprehensiveScraper(output_dir=f"{scraper_config['data_dir']}/eu")

        # Registrierung bei ScraperManager ist nicht erforderlich
        # Die Scraper werden direkt in self.scrapers verwaltet

        comprehensive_count = len([k for k in self.scrapers.keys() if "comprehensive" in k])
        self.logger.info(
            f"Initialized {len(self.scrapers)} production scrapers (including {comprehensive_count} comprehensive adapters)"
        )

    def start_production_scheduler(self):
        """Startet Production Scheduler"""
        if self.scheduler_running:
            self.logger.warning("Scheduler already running")
            return

        # Tägliche Updates
        schedule.every().day.at(self.config["production_schedule"]["daily_update_time"]).do(self._run_daily_update)

        # Wochenend-Updates
        schedule.every().saturday.at(self.config["production_schedule"]["weekend_update_time"]).do(self._run_weekend_update)
        schedule.every().sunday.at(self.config["production_schedule"]["weekend_update_time"]).do(self._run_weekend_update)

        # Stündliche Updates für prioritäre Quellen
        if self.config["production_schedule"]["enable_hourly"]:
            schedule.every().hour.do(self._run_hourly_update)

        # Scheduler Thread
        self.scheduler_running = True
        self.scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self.scheduler_thread.start()

        self.logger.info("Production scheduler started")
        self._update_next_scheduled()

    def stop_production_scheduler(self):
        """Stoppt Production Scheduler"""
        self.scheduler_running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)

        schedule.clear()
        self.logger.info("Production scheduler stopped")

    def _scheduler_loop(self):
        """Scheduler Hauptschleife"""
        while self.scheduler_running:
            try:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
            except Exception as e:
                self.logger.error(f"Scheduler error: {e}")
                time.sleep(300)  # Wait 5 minutes on error

    def _run_daily_update(self):
        """Führt tägliches Update durch"""
        self.logger.info("Starting daily production update")

        try:
            # Reset daily counters
            self.production_status["total_documents_today"] = 0
            self.production_status["errors_today"] = 0
            self.production_status["last_run"] = datetime.now().isoformat()

            # Jobs für alle Scraper erstellen
            jobs = self._create_daily_jobs()

            # Jobs ausführen
            results = self.scraper_manager.execute_jobs_parallel(jobs)

            # Ergebnisse verarbeiten
            self._process_daily_results(results)

            # Status aktualisieren
            self._update_production_status(results)

            # Cleanup
            self._cleanup_old_data()

            self.logger.info("Daily production update completed")

        except Exception as e:
            self.logger.error(f"Daily update failed: {e}")
            self.production_status["errors_today"] += 1

        self._update_next_scheduled()

    def _run_weekend_update(self):
        """Führt Wochenend-Update durch (weniger intensiv)"""
        self.logger.info("Starting weekend production update")

        try:
            # Nur prioritäre Quellen
            priority_sources = ["bverwg", "eu_cellar"]

            jobs = []
            for source in priority_sources:
                if source in self.scrapers:
                    job = ScrapingJob(scraper_name=source, parameters={"days_back": 7, "limit": 50}, priority=1)
                    jobs.append(job)

            results = self.scraper_manager.execute_jobs_parallel(jobs)
            self._process_daily_results(results)

            self.logger.info("Weekend production update completed")

        except Exception as e:
            self.logger.error(f"Weekend update failed: {e}")

    def _run_hourly_update(self):
        """Führt stündliches Update durch (nur prioritäre Quellen)"""
        if not self.config["production_schedule"]["enable_hourly"]:
            return

        try:
            hourly_sources = self.config["production_schedule"]["hourly_sources"]

            jobs = []
            for source in hourly_sources:
                if source in self.scrapers:
                    job = ScrapingJob(scraper_name=source, parameters={"days_back": 1, "limit": 10}, priority=2)
                    jobs.append(job)

            results = self.scraper_manager.execute_jobs_parallel(jobs)

            # Nur bei neuen Dokumenten loggen
            total_docs = sum(len(r.documents) for r in results if r.success)
            if total_docs > 0:
                self.logger.info(f"Hourly update: {total_docs} new documents")

        except Exception as e:
            self.logger.error(f"Hourly update failed: {e}")

    def _create_daily_jobs(self) -> List[ScrapingJob]:
        """Erstellt Jobs für tägliches Update"""
        jobs = []
        limits = self.config["scraping_limits"]["priority_sources"]

        # BVerwG - Höchste Priorität
        jobs.append(
            ScrapingJob(
                scraper_name="bverwg",
                parameters={"use_rss": True, "days_back": 7, "limit": limits.get("bverwg", 300)},
                priority=1,
            )
        )

        # EU Cellar - Hohe Priorität
        jobs.append(
            ScrapingJob(
                scraper_name="eu_cellar",
                parameters={"document_type": "case - law", "days_back": 14, "limit": limits.get("eu_cellar", 300)},
                priority=1,
            )
        )

        # VGH BW - Mittlere Priorität
        jobs.append(
            ScrapingJob(
                scraper_name="vgh_bw",
                parameters={"court": "vgh", "days_back": 7, "limit": limits.get("vgh_bw", 200)},
                priority=2,
            )
        )

        # BW Rechtsprechung - Normale Priorität
        jobs.append(
            ScrapingJob(
                scraper_name="bw_rechtsprechung",
                parameters={"days_back": 7, "limit": limits.get("bw_rechtsprechung", 200)},
                priority=3,
            )
        )

        return jobs

    def _process_daily_results(self, results: List[ScrapingResult]):
        """Verarbeitet Ergebnisse des täglichen Updates"""
        total_documents = 0
        total_errors = 0

        summary = {"timestamp": datetime.now().isoformat(), "sources": {}, "total_documents": 0, "total_errors": 0}

        for result in results:
            source_name = result.scraper_name
            doc_count = len(result.documents) if result.success else 0

            total_documents += doc_count
            if not result.success:
                total_errors += 1

            summary["sources"][source_name] = {
                "success": result.success,
                "documents": doc_count,
                "error": result.error_message if not result.success else None,
                "execution_time": result.execution_time,
            }

            self.logger.info(f"Source {source_name}: {doc_count} documents, " f"{'success' if result.success else 'failed'}")

        summary["total_documents"] = total_documents
        summary["total_errors"] = total_errors

        # Summary speichern
        self._save_daily_summary(summary)

        # Status aktualisieren
        self.production_status["total_documents_today"] = total_documents
        self.production_status["errors_today"] = total_errors

        # Benachrichtigungen
        if total_errors > self.config["notification"]["error_threshold"]:
            self._send_error_notification(summary)

    def _save_daily_summary(self, summary: Dict):
        """Speichert tägliche Zusammenfassung"""
        try:
            summary_dir = Path(self.config["scraper_config"]["data_dir"]) / "summaries"
            summary_dir.mkdir(parents=True, exist_ok=True)

            summary_file = summary_dir / f"daily_summary_{datetime.now().strftime('%Y%m%d')}.json"

            with open(summary_file, "w", encoding="utf-8") as f:
                json.dump(summary, f, indent=2, ensure_ascii=False)

        except Exception as e:
            self.logger.error(f"Failed to save daily summary: {e}")

    def _cleanup_old_data(self):
        """Bereinigt alte Daten"""
        try:
            data_dir = Path(self.config["scraper_config"]["data_dir"])
            retention = self.config["data_retention"]

            # Raw data cleanup
            raw_cutoff = datetime.now() - timedelta(days=retention["raw_data_days"])
            self._cleanup_directory(data_dir / "raw", raw_cutoff)

            # Processed data cleanup
            processed_cutoff = datetime.now() - timedelta(days=retention["processed_data_days"])
            self._cleanup_directory(data_dir / "processed", processed_cutoff)

            # Cache cleanup
            cache_cutoff = datetime.now() - timedelta(hours=retention["cache_hours"])
            self._cleanup_directory(data_dir / "cache", cache_cutoff)

        except Exception as e:
            self.logger.error(f"Cleanup failed: {e}")

    def _cleanup_directory(self, directory: Path, cutoff: datetime):
        """Bereinigt Verzeichnis basierend auf Alter"""
        if not directory.exists():
            return

        deleted_count = 0
        for file_path in directory.rglob("*"):
            if file_path.is_file():
                try:
                    file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                    if file_time < cutoff:
                        file_path.unlink()
                        deleted_count += 1
                except Exception:
                    continue

        if deleted_count > 0:
            self.logger.info(f"Cleaned up {deleted_count} old files from {directory}")

    def _update_production_status(self, results: List[ScrapingResult]):
        """Aktualisiert Production Status"""
        self.production_status["last_run"] = datetime.now().isoformat()
        self.production_status["active_jobs"] = [r.scraper_name for r in results if r.success]

    def _update_next_scheduled(self):
        """Aktualisiert nächste geplante Ausführung"""
        next_job = schedule.next_run()
        if next_job:
            self.production_status["next_scheduled"] = next_job.isoformat()

    def _send_error_notification(self, summary: Dict):
        """Sendet Fehler-Benachrichtigung"""
        if not self.config["notification"]["enable_email"]:
            return

        # Placeholder für E-Mail/Slack Benachrichtigungen
        self.logger.warning(f"High error count: {summary['total_errors']} errors detected")

    def get_production_status(self) -> Dict:
        """Gibt aktuellen Production Status zurück"""
        return self.production_status.copy()

    def run_manual_update(self, sources: List[str] = None, **kwargs) -> List[ScrapingResult]:
        """
        Führt manuelles Update durch

        Args:
            sources: Liste der Quellen (None = alle)
            **kwargs: Parameter für Scraping
        """
        self.logger.info(f"Running manual update for sources: {sources or 'all'}")

        if sources is None:
            sources = list(self.scrapers.keys())

        jobs = []
        for source in sources:
            if source in self.scrapers:
                job = ScrapingJob(
                    scraper_id=source,
                    job_id=f"{source}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    parameters=kwargs,
                    priority=1,
                )
                jobs.append(job)

        results = self.scraper_manager.execute_jobs_parallel(jobs)
        self._process_daily_results(results)

        return results

    def get_scraper_statistics(self) -> Dict:
        """Gibt Scraper-Statistiken zurück"""
        return self.scraper_manager.get_statistics()


# CLI Interface für Production Management
def main():
    """Main entry point für Production Manager"""
    import argparse

    parser = argparse.ArgumentParser(description="VERITAS Production Manager")
    parser.add_argument("--config", help="Configuration file path")
    parser.add_argument("--start-scheduler", action="store_true", help="Start production scheduler")
    parser.add_argument("--manual-update", action="store_true", help="Run manual update")
    parser.add_argument("--sources", nargs="*", help="Specific sources to update")
    parser.add_argument("--days-back", type=int, default=7, help="Days to look back")
    parser.add_argument("--limit", type=int, default=100, help="Document limit per source")

    args = parser.parse_args()

    # Initialize manager
    manager = VERITASProductionManager(args.config)

    if args.manual_update:
        # Manual update
        results = manager.run_manual_update(sources=args.sources, days_back=args.days_back, limit=args.limit)

        total_docs = sum(len(r.documents) for r in results if r.success)
        print(f"Manual update completed: {total_docs} documents processed")

    elif args.start_scheduler:
        # Start scheduler
        manager.start_production_scheduler()
        print("Production scheduler started. Press Ctrl+C to stop.")

        try:
            while True:
                time.sleep(60)
                status = manager.get_production_status()
                print(f"Status: {status['total_documents_today']} docs today, " f"next run: {status['next_scheduled']}")
        except KeyboardInterrupt:
            print("\nStopping scheduler...")
            manager.stop_production_scheduler()
    else:
        # Show status
        status = manager.get_production_status()
        stats = manager.get_scraper_statistics()

        print("VERITAS Production Manager Status:")
        print(f"Last run: {status['last_run']}")
        print(f"Documents today: {status['total_documents_today']}")
        print(f"Errors today: {status['errors_today']}")
        print(f"Next scheduled: {status['next_scheduled']}")
        print(f"Registered scrapers: {len(stats)}")


if __name__ == "__main__":
    main()
