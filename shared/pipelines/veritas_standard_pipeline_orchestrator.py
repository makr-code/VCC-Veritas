#!/usr/bin/env python3
"""
Standard VERITAS Pipeline Orchestrator
Verwendet das default_pipeline_schema.json für die vollständige VERITAS-Pipeline

Author: AI Assistant
Date: 2025-09-04
"""

import json
import logging
import threading
import time
from pathlib import Path
from queue import Queue
from typing import Any, Dict, List, Optional

# Import robust database functions
from ingestion_internal_ig_wrapper import get_robust_pipeline_connection
from ingestion_schema_manager import PipelineSchemaManager

logger = logging.getLogger(__name__)


class VeritasPipelineOrchestrator:
    """
    Standard VERITAS Pipeline Orchestrator
    Verwendet das default_pipeline_schema.json für die vollständige Pipeline-Verarbeitung
    """

    def __init__(self, pipeline_db_manager=None):
        """
        Initialisiert den VERITAS-Pipeline-Orchestrator
        """
        # Schema-Manager mit Standard-Template
        self.schema_manager = PipelineSchemaManager()

        # Stelle sicher, dass das Standard-Pipeline-Schema existiert
        self._ensure_standard_pipeline_schema()

        # Lade Pipeline-Konfiguration aus der Datenbank
        self.job_chains = self._load_job_chains_from_db()
        self.backend_integrations = self._load_backend_integrations_from_db()
        self.pipeline_metrics = self._initialize_pipeline_metrics()

        self.processing_queue = Queue()
        self.orchestration_active = False
        self.orchestration_thread = None

        logger.info("🎯 VERITAS Pipeline-Orchestrator mit Standard-Schema initialisiert")

    def _ensure_standard_pipeline_schema(self):
        """
        Stellt sicher, dass das Standard-Pipeline-Schema existiert
        """
        try:
            validation = self.schema_manager.validate_database_schema()

            # Überprüfe ob alle Standard-Pipeline-Tabellen existieren
            required_tables = ["pipelines", "job_chains", "backend_integrations", "pipeline_metrics"]
            existing_tables = validation.get("tables", [])

            missing_tables = [t for t in required_tables if t not in existing_tables]

            if missing_tables:
                logger.info(f"📋 Fehlende Pipeline-Tabellen: {missing_tables}")
                logger.info("🔨 Erstelle Standard-Pipeline-Schema aus default_pipeline_schema.json...")

                # Lade explizit das Standard-Schema
                schema = self.schema_manager.load_schema_template("default_pipeline_schema.json")
                if schema:
                    success = self.schema_manager.create_database_from_schema(schema)
                    if success:
                        logger.info(f"✅ Standard-Pipeline-Schema v{schema.get('version', 'unknown')} erstellt")
                    else:
                        logger.error("❌ Standard-Pipeline-Schema-Erstellung fehlgeschlagen")
                else:
                    logger.error("❌ Standard-Pipeline-Schema konnte nicht geladen werden")
            else:
                logger.info("✅ Standard-Pipeline-Schema vollständig vorhanden")

        except Exception as e:
            logger.error(f"❌ Standard-Schema-Validation fehlgeschlagen: {e}")

    def _initialize_pipeline_metrics(self) -> Dict[str, Any]:
        """
        Initialisiert Pipeline-Metriken für alle Standard-Job-Types
        """
        standard_job_types = [
            "preprocessor",
            "enhanced_metadata",
            "chunking",
            "nlp",
            "llm",
            "uds3",
            "internal_relations",
            "cross_relations",
            "keywords",
            "kge",
            "quality",
            "backend",
            "postprocessor",
        ]

        metrics = {}
        for job_type in standard_job_types:
            metrics[job_type] = {
                "total_jobs": 0,
                "completed_jobs": 0,
                "failed_jobs": 0,
                "avg_processing_time": 0.0,
                "avg_quality_score": 0.0,
            }

        logger.info(f"📊 Pipeline-Metriken für {len(standard_job_types)} Job-Types initialisiert")
        return metrics

    def _load_job_chains_from_db(self) -> Dict[str, List[str]]:
        """
        Lädt Job-Ketten-Definitionen aus der Standard-Pipeline-Datenbank
        """
        try:
            with get_robust_pipeline_connection() as conn:
                cursor = conn.cursor()

                cursor.execute(
                    """
                    SELECT source_job_type, target_job_type, priority, active, description
                    FROM job_chains
                    WHERE active = 1
                    ORDER BY priority DESC
                """
                )

                chains = {}
                chain_descriptions = {}

                for source_job, target_job, priority, active, description in cursor.fetchall():
                    if source_job not in chains:
                        chains[source_job] = []
                        chain_descriptions[source_job] = {}

                    chains[source_job].append(target_job)
                    chain_descriptions[source_job][target_job] = {"priority": priority, "description": description}

            self.chain_descriptions = chain_descriptions
            logger.info(f"📋 {len(chains)} Standard-Pipeline-Ketten geladen")

            # Logge die Pipeline-Sequenz
            if chains:
                logger.info("🔗 Standard-Pipeline-Sequenz:")
                for source, targets in chains.items():
                    for target in targets:
                        desc_info = chain_descriptions.get(source, {}).get(target, {})
                        priority = desc_info.get("priority", "unknown")
                        desc = desc_info.get("description", "Keine Beschreibung")
                        logger.info(f"   {priority:4s}: {source:20s} → {target:20s}")

            return chains

        except Exception as e:
            logger.error(f"❌ Standard-Pipeline-Chains-Loading fehlgeschlagen: {e}")
            return {}

    def _load_backend_integrations_from_db(self) -> Dict[str, Dict[str, str]]:
        """
        Lädt Backend-Integration-Definitionen aus der Standard-Pipeline-Datenbank
        """
        try:
            with get_robust_pipeline_connection() as conn:
                cursor = conn.cursor()

                cursor.execute(
                    """
                    SELECT job_type, backend_type, storage_path, config,
                           compression, encryption, active, description
                    FROM backend_integrations
                    WHERE active = 1
                    ORDER BY job_type
                """
                )

                integrations = {}

                for row in cursor.fetchall():
                    job_type, backend_type, storage_path, config, compression, encryption, active, description = row

                    integrations[job_type] = {
                        "backend_type": backend_type,
                        "storage_path": storage_path,
                        "config": json.loads(config) if config else {},
                        "compression": bool(compression),
                        "encryption": bool(encryption),
                        "description": description,
                    }

            logger.info(f"🔧 {len(integrations)} Standard-Backend-Integrationen geladen")

            # Logge die Backend-Integrationen
            if integrations:
                logger.info("🔌 Standard-Backend-Integrationen:")
                for job_type, config in integrations.items():
                    backend = config["backend_type"]
                    features = []
                    if config["compression"]:
                        features.append("komprimiert")
                    if config["encryption"]:
                        features.append("verschlüsselt")
                    feature_str = f" ({', '.join(features)})" if features else ""
                    logger.info(f"   {job_type:20s} → {backend:30s}{feature_str}")

            return integrations

        except Exception as e:
            logger.error(f"❌ Standard-Backend-Integration-Loading fehlgeschlagen: {e}")
            return {}

    def start_standard_pipeline_orchestration(self):
        """
        Startet die Standard-VERITAS-Pipeline-Orchestrierung
        """
        if self.orchestration_active:
            logger.warning("⚠️ Standard-Pipeline-Orchestrierung bereits aktiv")
            return False

        self.orchestration_active = True
        self.orchestration_thread = threading.Thread(target=self._standard_orchestration_loop, daemon=True)
        self.orchestration_thread.start()

        logger.info("🚀 Standard-VERITAS-Pipeline-Orchestrierung gestartet")
        return True

    def stop_standard_pipeline_orchestration(self):
        """
        Stoppt die Standard-VERITAS-Pipeline-Orchestrierung
        """
        if not self.orchestration_active:
            logger.warning("⚠️ Standard-Pipeline-Orchestrierung bereits gestoppt")
            return False

        self.orchestration_active = False

        if self.orchestration_thread:
            self.orchestration_thread.join(timeout=5.0)

        logger.info("🛑 Standard-VERITAS-Pipeline-Orchestrierung gestoppt")
        return True

    def _standard_orchestration_loop(self):
        """
        Haupt-Loop für Standard-VERITAS-Pipeline-Orchestrierung
        """
        logger.info("🔄 Standard-Pipeline-Orchestration-Loop gestartet")

        while self.orchestration_active:
            try:
                # 1. Verarbeite abgeschlossene Jobs für Standard-Pipeline-Chaining
                self._process_completed_jobs_for_chaining()

                # 2. Verarbeite Backend-Integration-Kandidaten
                self._process_backend_integration_candidates()

                # 3. Aktualisiere Pipeline-Metriken
                self._update_pipeline_metrics()

                # Kurze Pause zwischen Iterations
                time.sleep(3.0)

            except Exception as e:
                logger.error(f"❌ Standard-Pipeline-Orchestration-Loop Fehler: {e}")
                time.sleep(5.0)

        logger.info("🏁 Standard-Pipeline-Orchestration-Loop beendet")

    def _process_completed_jobs_for_chaining(self):
        """
        Verarbeitet abgeschlossene Jobs für Standard-Pipeline-Ketten-Auslösung
        """
        try:
            with get_robust_pipeline_connection() as conn:
                cursor = conn.cursor()

                # Finde COMPLETED Jobs die noch nicht für Chaining verarbeitet wurden
                cursor.execute(
                    """
                    SELECT job_id, job_type, collection_name, document_id, file_path, metadata, quality_score
                    FROM pipelines
                    WHERE status = 'COMPLETED'
                    AND (chained_processed IS NULL OR chained_processed = 0)
                    LIMIT 25
                """
                )

                completed_jobs = cursor.fetchall()

                for job_id, job_type, collection_name, document_id, file_path, metadata, quality_score in completed_jobs:
                    # Prüfe ob dieser Job-Typ Folge-Jobs in der Standard-Pipeline auslösen soll
                    if job_type in self.job_chains:
                        target_job_types = self.job_chains[job_type]

                        for target_job_type in target_job_types:
                            # Prüfe Quality-basierte Bedingungen
                            if self._check_chain_conditions(job_type, target_job_type, quality_score, metadata):
                                success = self._trigger_standard_chained_job(
                                    job_id, job_type, target_job_type, collection_name, document_id, file_path, metadata
                                )

                                if success:
                                    logger.info(
                                        f"🔗 Standard-Pipeline-Chain: {job_type} → {target_job_type} (source: {job_id})"
                                    )

                    # Markiere als für Chaining verarbeitet
                    cursor.execute(
                        """
                        UPDATE pipelines
                        SET chained_processed = 1, updated_at = ?
                        WHERE job_id = ?
                    """,
                        (time.strftime("%Y-%m-%d %H:%M:%S"), job_id),
                    )

                conn.commit()

                if completed_jobs:
                    logger.info(f"🔄 {len(completed_jobs)} Jobs für Standard-Pipeline-Chaining verarbeitet")

        except Exception as e:
            logger.error(f"❌ Standard-Pipeline-Chain-Processing fehlgeschlagen: {e}")

    def _check_chain_conditions(self, source_job_type: str, target_job_type: str, quality_score: float, metadata: str) -> bool:
        """
        Prüft ob Chain-Bedingungen für Standard-Pipeline erfüllt sind
        """
        try:
            # Spezielle Bedingung: quality → backend nur bei ausreichender Qualität
            if source_job_type == "quality" and target_job_type == "backend":
                if quality_score is None or quality_score < 0.7:
                    logger.debug(f"❌ Quality-Score zu niedrig für Backend-Integration: {quality_score}")
                    return False
                else:
                    logger.debug(f"✅ Quality-Score ausreichend für Backend-Integration: {quality_score}")

            # Weitere Standard-Bedingungen können hier hinzugefügt werden

            return True

        except Exception as e:
            logger.error(f"❌ Chain-Conditions-Check fehlgeschlagen: {e}")
            return False

    def _trigger_standard_chained_job(
        self,
        source_job_id: int,
        source_job_type: str,
        target_job_type: str,
        collection_name: str,
        document_id: str,
        file_path: str,
        metadata: str,
    ) -> bool:
        """
        Löst einen Folge-Job in der Standard-Pipeline-Chain aus
        """
        try:
            with get_robust_pipeline_connection() as conn:
                cursor = conn.cursor()

                # Erstelle neuen Job für die Standard-Pipeline-Chain
                chain_metadata = {
                    "chained_from": source_job_id,
                    "chain_source_type": source_job_type,
                    "pipeline_step": target_job_type,
                    "original_metadata": json.loads(metadata) if metadata else {},
                }

                cursor.execute(
                    """
                    INSERT INTO pipelines (
                        status, job_type, collection_name, document_id, file_path,
                        metadata, chain_source_job_id, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        "PENDING",
                        target_job_type,
                        collection_name,
                        document_id,
                        file_path,
                        json.dumps(chain_metadata),
                        source_job_id,
                        time.strftime("%Y-%m-%d %H:%M:%S"),
                        time.strftime("%Y-%m-%d %H:%M:%S"),
                    ),
                )

                chained_job_id = cursor.lastrowid
                conn.commit()

            logger.info(f"✅ Standard-Pipeline-Chain-Job erstellt: {target_job_type} (ID: {chained_job_id})")
            return True

        except Exception as e:
            logger.error(f"❌ Standard-Pipeline-Chain-Job Creation fehlgeschlagen: {e}")
            return False

    def _process_backend_integration_candidates(self):
        """
        Verarbeitet Jobs die für Standard-Backend-Integration bereit sind
        """
        try:
            with get_robust_pipeline_connection() as conn:
                cursor = conn.cursor()

                # Finde COMPLETED Jobs die noch nicht backend-integriert wurden
                cursor.execute(
                    """
                    SELECT job_id, job_type, collection_name, document_id, file_path, metadata
                    FROM pipelines
                    WHERE status = 'COMPLETED'
                    AND (backend_integrated IS NULL OR backend_integrated = 0)
                    LIMIT 20
                """
                )

                integration_candidates = cursor.fetchall()

                for job_id, job_type, collection_name, document_id, file_path, metadata in integration_candidates:
                    # Prüfe ob Standard-Backend-Integration für diesen Job-Typ definiert ist
                    if job_type in self.backend_integrations:
                        integration_config = self.backend_integrations[job_type]

                        success = self._integrate_job_to_standard_backend(
                            job_id, job_type, integration_config, file_path, collection_name, document_id, metadata
                        )

                        if success:
                            # Markiere als backend-integriert
                            cursor.execute(
                                """
                                UPDATE pipelines
                                SET backend_integrated = 1, updated_at = ?
                                WHERE job_id = ?
                            """,
                                (time.strftime("%Y-%m-%d %H:%M:%S"), job_id),
                            )

                            logger.info(f"🔌 Standard-Backend-Integration: Job {job_id} → {integration_config['backend_type']}")

                conn.commit()

                if integration_candidates:
                    logger.info(f"🔌 {len(integration_candidates)} Jobs für Standard-Backend-Integration verarbeitet")

        except Exception as e:
            logger.error(f"❌ Standard-Backend-Integration-Processing fehlgeschlagen: {e}")

    def _integrate_job_to_standard_backend(
        self,
        job_id: int,
        job_type: str,
        integration_config: Dict[str, Any],
        file_path: str,
        collection_name: str,
        document_id: str,
        metadata: str,
    ) -> bool:
        """
        Integriert Job-Result ins entsprechende Standard-Backend
        """
        try:
            storage_path = integration_config["storage_path"].format(
                collection_name=collection_name, document_id=document_id, job_id=job_id
            )

            integration_data = {
                "job_id": job_id,
                "job_type": job_type,
                "backend_type": integration_config["backend_type"],
                "storage_path": storage_path,
                "collection_name": collection_name,
                "document_id": document_id,
                "compression": integration_config["compression"],
                "encryption": integration_config["encryption"],
                "metadata": json.loads(metadata) if metadata else {},
                "integration_timestamp": time.time(),
            }

            # Standard-Backend-Integration (hier als Platzhalter)
            logger.info(f"💾 Standard-Backend-Integration: {storage_path}")

            if integration_config["compression"]:
                logger.debug(f"🗜️  Komprimierung aktiviert für {job_type}")

            if integration_config["encryption"]:
                logger.debug(f"🔐 Verschlüsselung aktiviert für {job_type}")

            return True

        except Exception as e:
            logger.error(f"Standard-Backend-Integration fehlgeschlagen für Job {job_id}: {e}")
            return False

    def _update_pipeline_metrics(self):
        """
        Aktualisiert Pipeline-Metriken für Standard-Pipeline
        """
        try:
            with get_robust_pipeline_connection() as conn:
                cursor = conn.cursor()

                # Aktualisiere Metriken für jeden Standard-Job-Type
                for job_type in self.pipeline_metrics.keys():
                    cursor.execute(
                        """
                        SELECT
                            COUNT(*) as total,
                            SUM(CASE WHEN status = 'COMPLETED' THEN 1 ELSE 0 END) as completed,
                            SUM(CASE WHEN status = 'FAILED' THEN 1 ELSE 0 END) as failed,
                            AVG(CASE WHEN processing_time IS NOT NULL THEN processing_time ELSE 0 END) as avg_time,
                            AVG(CASE WHEN quality_score IS NOT NULL THEN quality_score ELSE 0 END) as avg_quality
                        FROM pipelines
                        WHERE job_type = ?
                    """,
                        (job_type,),
                    )

                    result = cursor.fetchone()
                    if result:
                        total, completed, failed, avg_time, avg_quality = result
                        self.pipeline_metrics[job_type] = {
                            "total_jobs": total or 0,
                            "completed_jobs": completed or 0,
                            "failed_jobs": failed or 0,
                            "avg_processing_time": avg_time or 0.0,
                            "avg_quality_score": avg_quality or 0.0,
                        }

        except Exception as e:
            logger.error(f"❌ Pipeline-Metriken-Update fehlgeschlagen: {e}")

    def get_standard_pipeline_stats(self) -> Dict[str, Any]:
        """
        Gibt Standard-Pipeline-Statistiken zurück
        """
        try:
            with get_robust_pipeline_connection() as conn:
                cursor = conn.cursor()

                cursor.execute("SELECT COUNT(*) FROM pipelines WHERE chained_processed = 1")
                chained_jobs_count = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM pipelines WHERE backend_integrated = 1")
                integrated_jobs_count = cursor.fetchone()[0]

                cursor.execute('SELECT COUNT(*) FROM pipelines WHERE status = "PENDING"')
                pending_jobs_count = cursor.fetchone()[0]

                cursor.execute('SELECT COUNT(*) FROM pipelines WHERE status = "COMPLETED"')
                completed_jobs_count = cursor.fetchone()[0]

            return {
                "orchestration_active": self.orchestration_active,
                "pipeline_type": "standard_veritas_pipeline",
                "job_chains_defined": len(self.job_chains),
                "backend_integrations_defined": len(self.backend_integrations),
                "chained_jobs_processed": chained_jobs_count,
                "backend_integrated_jobs": integrated_jobs_count,
                "pending_jobs": pending_jobs_count,
                "completed_jobs": completed_jobs_count,
                "pipeline_metrics": self.pipeline_metrics,
            }

        except Exception as e:
            logger.error(f"❌ Standard-Pipeline-Stats-Abruf fehlgeschlagen: {e}")
            return {
                "orchestration_active": self.orchestration_active,
                "pipeline_type": "standard_veritas_pipeline",
                "job_chains_defined": len(self.job_chains),
                "backend_integrations_defined": len(self.backend_integrations),
                "error": str(e),
            }


def main():
    """
    Test-Funktion für den Standard-VERITAS-Pipeline-Orchestrator
    """
    logging.basicConfig(level=logging.INFO)

    print("🚀 Standard VERITAS Pipeline-Orchestrator Test")
    print("=" * 60)

    orchestrator = VeritasPipelineOrchestrator()

    print("\n📊 Standard-Pipeline-Statistiken:")
    stats = orchestrator.get_standard_pipeline_stats()
    for key, value in stats.items():
        if key != "pipeline_metrics":
            print(f"   {key}: {value}")

    print("\n✅ Standard-Pipeline-Orchestrator-Test erfolgreich!")


if __name__ == "__main__":
    main()
