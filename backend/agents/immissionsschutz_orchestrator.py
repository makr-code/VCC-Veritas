"""
Immissionsschutz Multi-Agent Orchestrator

Koordiniert DatabaseAgentTestServerExtension und ImmissionsschutzAgentTestServerExtension
für komplexe Workflows im Immissionsschutz-Bereich.

Design:
    - Workflow-basierte Orchestrierung
    - State Management für Multi-Step Analysen
    - Parallele Agent-Queries
    - Strukturierte Result-Aggregation

Version: 1.0
Autor: VERITAS Team
Datum: 18. Oktober 2025
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

try:
    from .database_agent_testserver_extension import (
        ComplianceResult,
        DatabaseAgentTestServerExtension,
        EntityType,
        QueryResult,
        get_database_agent,
    )
    from .immissionsschutz_agent_testserver_extension import (
        ComplianceReport,
        GrenzwertPruefung,
        ImmissionsschutzAgentTestServerExtension,
        RisikoAnalyse,
        RisikoKlasse,
        TrendAnalyse,
        get_immissionsschutz_agent,
    )
    from .test_server_client import TestServerConfig
except ImportError:
    from database_agent_testserver_extension import (
        ComplianceResult,
        DatabaseAgentTestServerExtension,
        EntityType,
        QueryResult,
        get_database_agent,
    )
    from immissionsschutz_agent_testserver_extension import (
        ComplianceReport,
        GrenzwertPruefung,
        ImmissionsschutzAgentTestServerExtension,
        RisikoAnalyse,
        RisikoKlasse,
        TrendAnalyse,
        get_immissionsschutz_agent,
    )
    from test_server_client import TestServerConfig


# ============================================================================
# WORKFLOW ENUMS
# ============================================================================


class WorkflowType(str, Enum):
    """Typen von Workflows"""

    COMPREHENSIVE_ANALYSIS = "comprehensive_analysis"
    COMPLIANCE_CHECK = "compliance_check"
    MAINTENANCE_PLANNING = "maintenance_planning"
    EMISSION_MONITORING = "emission_monitoring"
    RISK_ASSESSMENT = "risk_assessment"


class WorkflowStatus(str, Enum):
    """Status eines Workflows"""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL_SUCCESS = "partial_success"


class PriorityLevel(str, Enum):
    """Prioritätsstufen"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# ============================================================================
# WORKFLOW RESULT OBJECTS
# ============================================================================


@dataclass
class WorkflowStep:
    """Ein Schritt in einem Workflow"""

    step_id: int
    name: str
    status: WorkflowStatus
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    duration_seconds: float = 0.0
    result: Any = None
    error: Optional[str] = None

    @property
    def is_completed(self) -> bool:
        return self.status == WorkflowStatus.COMPLETED

    @property
    def has_error(self) -> bool:
        return self.error is not None


@dataclass
class WorkflowResult:
    """Ergebnis eines kompletten Workflows"""

    workflow_id: str
    workflow_type: WorkflowType
    bst_nr: str
    anl_nr: str
    status: WorkflowStatus
    priority: PriorityLevel
    steps: List[WorkflowStep]
    result_data: Dict[str, Any]
    recommendations: List[str]
    summary: str
    started_at: str
    completed_at: Optional[str] = None
    total_duration_seconds: float = 0.0

    @property
    def is_completed(self) -> bool:
        return self.status == WorkflowStatus.COMPLETED

    @property
    def has_critical_findings(self) -> bool:
        return self.priority in [PriorityLevel.HIGH, PriorityLevel.CRITICAL]

    @property
    def success_rate(self) -> float:
        """Prozentuale Erfolgsrate der Steps"""
        if not self.steps:
            return 0.0
        completed = sum(1 for s in self.steps if s.is_completed)
        return (completed / len(self.steps)) * 100


@dataclass
class ComprehensiveAnalysisResult:
    """Ergebnis der Comprehensive Analysis"""

    bst_nr: str
    anl_nr: str
    anlagen_name: str

    # Basis-Daten (DatabaseAgent)
    entity_data: Any  # AnlageExtended

    # Compliance (ImmissionsschutzAgent)
    compliance_report: ComplianceReport

    # Risiko (ImmissionsschutzAgent)
    risiko_analyse: RisikoAnalyse

    # Grenzwerte (ImmissionsschutzAgent)
    grenzwert_status: Dict[str, List[GrenzwertPruefung]]

    # Zusammenfassung
    gesamtbewertung: str
    handlungsempfehlungen: List[str]
    prioritaet: PriorityLevel
    naechste_schritte: List[str]

    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


# ============================================================================
# ORCHESTRATOR
# ============================================================================


class ImmissionsschutzOrchestrator:
    """
    Multi-Agent Orchestrator für Immissionsschutz-Workflows.

    Koordiniert:
        - DatabaseAgentTestServerExtension (Daten-Zugriff)
        - ImmissionsschutzAgentTestServerExtension (Domain-Logik)

    Features:
        - Workflow State Management
        - Parallele Agent-Queries
        - Result Aggregation
        - Error Handling & Recovery
    """

    def __init__(self, config: Optional[TestServerConfig] = None):
        self.config = config

        # Agents initialisieren
        self.db_agent = get_database_agent(config)
        self.immi_agent = get_immissionsschutz_agent(config)

        # Logger
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.setLevel(logging.INFO)

        # Workflow State
        self.active_workflows: Dict[str, WorkflowResult] = {}
        self.workflow_counter = 0

        self.logger.info("ImmissionsschutzOrchestrator initialisiert")

    async def close(self):
        """Cleanup"""
        await self.db_agent.close()
        await self.immi_agent.close()
        self.logger.info("Orchestrator geschlossen")

    # ========================================================================
    # WORKFLOW MANAGEMENT
    # ========================================================================

    def _create_workflow_id(self, workflow_type: WorkflowType, bst_nr: str, anl_nr: str) -> str:
        """Generiert eindeutige Workflow-ID"""
        self.workflow_counter += 1
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        return f"{workflow_type.value}_{bst_nr}_{anl_nr}_{timestamp}_{self.workflow_counter}"

    def _create_workflow_result(
        self, workflow_type: WorkflowType, bst_nr: str, anl_nr: str, steps: List[str]
    ) -> WorkflowResult:
        """Erstellt WorkflowResult mit Steps"""
        workflow_id = self._create_workflow_id(workflow_type, bst_nr, anl_nr)

        workflow_steps = [
            WorkflowStep(step_id=i + 1, name=step, status=WorkflowStatus.PENDING) for i, step in enumerate(steps)
        ]

        workflow = WorkflowResult(
            workflow_id=workflow_id,
            workflow_type=workflow_type,
            bst_nr=bst_nr,
            anl_nr=anl_nr,
            status=WorkflowStatus.PENDING,
            priority=PriorityLevel.MEDIUM,
            steps=workflow_steps,
            result_data={},
            recommendations=[],
            summary="",
            started_at=datetime.now().isoformat(),
        )

        self.active_workflows[workflow_id] = workflow
        return workflow

    async def _execute_step(self, workflow: WorkflowResult, step_index: int, step_func, *args, **kwargs) -> Any:
        """Führt einen Workflow-Step aus"""
        step = workflow.steps[step_index]
        step.status = WorkflowStatus.IN_PROGRESS
        step.started_at = datetime.now().isoformat()

        start_time = asyncio.get_event_loop().time()

        try:
            result = await step_func(*args, **kwargs)
            step.result = result
            step.status = WorkflowStatus.COMPLETED
            self.logger.info(f"✅ Step {step.step_id} completed: {step.name}")
            return result

        except Exception as e:
            step.error = str(e)
            step.status = WorkflowStatus.FAILED
            self.logger.error(f"❌ Step {step.step_id} failed: {step.name} - {e}")
            return None

        finally:
            end_time = asyncio.get_event_loop().time()
            step.duration_seconds = end_time - start_time
            step.completed_at = datetime.now().isoformat()

    def _finalize_workflow(self, workflow: WorkflowResult):
        """Finalisiert Workflow"""
        workflow.completed_at = datetime.now().isoformat()

        # Status bestimmen
        failed_steps = sum(1 for s in workflow.steps if s.status == WorkflowStatus.FAILED)
        completed_steps = sum(1 for s in workflow.steps if s.status == WorkflowStatus.COMPLETED)

        if failed_steps == 0:
            workflow.status = WorkflowStatus.COMPLETED
        elif completed_steps > 0:
            workflow.status = WorkflowStatus.PARTIAL_SUCCESS
        else:
            workflow.status = WorkflowStatus.FAILED

        # Duration
        if workflow.started_at and workflow.completed_at:
            start = datetime.fromisoformat(workflow.started_at)
            end = datetime.fromisoformat(workflow.completed_at)
            workflow.total_duration_seconds = (end - start).total_seconds()

        self.logger.info(
            f"Workflow {workflow.workflow_id} finalized: {workflow.status.value} " f"({workflow.success_rate:.1f}% success)"
        )

    # ========================================================================
    # COMPREHENSIVE ANALYSIS WORKFLOW
    # ========================================================================

    async def comprehensive_analysis(self, bst_nr: str, anl_nr: str) -> ComprehensiveAnalysisResult:
        """
        Umfassende Analyse einer Anlage.

        Workflow:
            1. Basis-Daten laden (DatabaseAgent)
            2. Compliance-Report generieren (ImmissionsschutzAgent)
            3. Risiko-Analyse durchführen (ImmissionsschutzAgent)
            4. Grenzwerte prüfen (ImmissionsschutzAgent)
            5. Ergebnisse aggregieren und bewerten

        Returns:
            ComprehensiveAnalysisResult mit allen Analysen
        """
        self.logger.info(f"🔍 Starte Comprehensive Analysis für {bst_nr}/{anl_nr}")

        # Workflow erstellen
        workflow = self._create_workflow_result(
            WorkflowType.COMPREHENSIVE_ANALYSIS,
            bst_nr,
            anl_nr,
            steps=[
                "Basis-Daten laden",
                "Compliance-Report generieren",
                "Risiko-Analyse durchführen",
                "Grenzwerte prüfen",
                "Ergebnisse aggregieren",
            ],
        )

        workflow.status = WorkflowStatus.IN_PROGRESS

        try:
            # Step 1: Basis-Daten
            entity_result = await self._execute_step(workflow, 0, self.db_agent.get_complete_entity, bst_nr, anl_nr, True)

            if not entity_result or not entity_result.success:
                raise ValueError(f"Anlage nicht gefunden: {bst_nr}/{anl_nr}")

            entity_data = entity_result.data

            # Step 2: Compliance-Report
            compliance_report = await self._execute_step(
                workflow, 1, self.immi_agent.generate_compliance_report, bst_nr, anl_nr
            )

            # Step 3: Risiko-Analyse
            risiko_analyse = await self._execute_step(workflow, 2, self.immi_agent.calculate_risk_score, bst_nr, anl_nr)

            # Step 4: Grenzwerte
            grenzwert_status = await self._execute_step(workflow, 3, self.immi_agent.check_grenzwerte, bst_nr, anl_nr)

            # Step 5: Aggregation
            result = await self._execute_step(
                workflow,
                4,
                self._aggregate_comprehensive_analysis,
                entity_data,
                compliance_report,
                risiko_analyse,
                grenzwert_status,
            )

            # Workflow finalisieren
            workflow.result_data = {
                "compliance_score": compliance_report.compliance_score if compliance_report else 0.0,
                "risiko_score": risiko_analyse.risiko_score if risiko_analyse else 0.0,
                "grenzwert_ueberschreitungen": len(
                    [p for kategorie in (grenzwert_status or {}).values() for p in kategorie if p.ist_kritisch]
                )
                if grenzwert_status
                else 0,
            }

            workflow.summary = result.gesamtbewertung if result else "Analyse fehlgeschlagen"
            workflow.recommendations = result.handlungsempfehlungen[:5] if result else []
            workflow.priority = result.prioritaet if result else PriorityLevel.MEDIUM

            self._finalize_workflow(workflow)

            return result

        except Exception as e:
            self.logger.error(f"Comprehensive Analysis failed: {e}")
            workflow.status = WorkflowStatus.FAILED
            self._finalize_workflow(workflow)
            raise

    async def _aggregate_comprehensive_analysis(
        self,
        entity_data,
        compliance_report: Optional[ComplianceReport],
        risiko_analyse: Optional[RisikoAnalyse],
        grenzwert_status: Optional[Dict],
    ) -> ComprehensiveAnalysisResult:
        """Aggregiert Ergebnisse der Comprehensive Analysis"""

        # Gesamtbewertung erstellen
        bewertungs_teile = []
        handlungsempfehlungen = []
        naechste_schritte = []

        # Compliance
        if compliance_report:
            if compliance_report.ist_konform:
                bewertungs_teile.append(f"✅ Compliance konform ({compliance_report.compliance_score:.0%})")
            else:
                bewertungs_teile.append(f"⚠️ Compliance-Probleme ({compliance_report.compliance_score:.0%})")
                handlungsempfehlungen.extend(compliance_report.empfehlungen[:3])

        # Risiko
        if risiko_analyse:
            risiko_emoji = {
                RisikoKlasse.SEHR_GERING: "✅",
                RisikoKlasse.GERING: "✅",
                RisikoKlasse.MITTEL: "⚠️",
                RisikoKlasse.HOCH: "🔴",
                RisikoKlasse.SEHR_HOCH: "🔴",
            }.get(risiko_analyse.risiko_klasse, "❓")

            bewertungs_teile.append(
                f"{risiko_emoji} Risiko: {risiko_analyse.risiko_klasse.value} " f"({risiko_analyse.risiko_score:.0%})"
            )

            if risiko_analyse.risiko_klasse in [RisikoKlasse.HOCH, RisikoKlasse.SEHR_HOCH]:
                handlungsempfehlungen.extend(risiko_analyse.empfehlungen[:2])
                naechste_schritte.append("Sofortige Risikoanalyse und Maßnahmenplan")

        # Grenzwerte
        if grenzwert_status:
            alle_pruefungen = []
            for kategorie in grenzwert_status.values():
                alle_pruefungen.extend(kategorie)

            kritische = [p for p in alle_pruefungen if p.ist_kritisch]

            if kritische:
                bewertungs_teile.append(f"🔴 {len(kritische)} Grenzwertüberschreitungen")
                for pruefung in kritische[:2]:
                    handlungsempfehlungen.append(f"Grenzwertüberschreitung {pruefung.messart} beheben")
                naechste_schritte.append("Emissionsminderung priorisieren")
            else:
                bewertungs_teile.append("✅ Alle Grenzwerte eingehalten")

        # Priorität bestimmen
        prioritaet = PriorityLevel.LOW

        if risiko_analyse and risiko_analyse.risiko_klasse == RisikoKlasse.SEHR_HOCH:
            prioritaet = PriorityLevel.CRITICAL
        elif risiko_analyse and risiko_analyse.risiko_klasse == RisikoKlasse.HOCH:
            prioritaet = PriorityLevel.HIGH
        elif grenzwert_status and any(p.ist_kritisch for kategorie in grenzwert_status.values() for p in kategorie):
            prioritaet = PriorityLevel.HIGH
        elif compliance_report and not compliance_report.ist_konform:
            prioritaet = PriorityLevel.MEDIUM

        # Nächste Schritte
        if not naechste_schritte:
            if prioritaet == PriorityLevel.LOW:
                naechste_schritte.append("Routinemäßige Überwachung fortsetzen")
            else:
                naechste_schritte.append("Detaillierte Prüfung durchführen")

        naechste_schritte.append("Nächste Compliance-Prüfung vorbereiten")

        return ComprehensiveAnalysisResult(
            bst_nr=entity_data.anlage.bst_nr,
            anl_nr=entity_data.anlage.anl_nr,
            anlagen_name=entity_data.anlage.bst_name,
            entity_data=entity_data,
            compliance_report=compliance_report,
            risiko_analyse=risiko_analyse,
            grenzwert_status=grenzwert_status or {},
            gesamtbewertung=" | ".join(bewertungs_teile),
            handlungsempfehlungen=handlungsempfehlungen[:10],
            prioritaet=prioritaet,
            naechste_schritte=naechste_schritte,
        )

    # ========================================================================
    # COMPLIANCE WORKFLOW
    # ========================================================================

    async def compliance_workflow(self, bst_nr: str, anl_nr: str) -> Dict[str, Any]:
        """
        Compliance-fokussierter Workflow.

        Workflow:
            1. Basis-Compliance prüfen
            2. Verfahrensstatus abrufen
            3. Auflagen-Status prüfen
            4. Mängel analysieren
            5. Compliance-Score berechnen

        Returns:
            Dict mit Compliance-Details
        """
        self.logger.info(f"📋 Starte Compliance Workflow für {bst_nr}/{anl_nr}")

        workflow = self._create_workflow_result(
            WorkflowType.COMPLIANCE_CHECK,
            bst_nr,
            anl_nr,
            steps=[
                "Basis-Compliance prüfen",
                "Verfahrensstatus abrufen",
                "Auflagen-Status prüfen",
                "Mängel analysieren",
                "Score berechnen",
            ],
        )

        workflow.status = WorkflowStatus.IN_PROGRESS

        try:
            # Step 1: Basis-Compliance
            base_compliance = await self._execute_step(workflow, 0, self.db_agent.analyze_compliance, bst_nr, anl_nr)

            # Step 2: Verfahren (parallel zu Step 3)
            verfahren_task = self._execute_step(workflow, 1, self.db_agent.query_verfahren, bst_nr, anl_nr)

            # Step 3: Auflagen (parallel zu Step 2)
            auflagen_task = self._execute_step(workflow, 2, self.db_agent.check_auflagen_status, bst_nr, anl_nr)

            # Parallel ausführen
            verfahren, auflagen = await asyncio.gather(verfahren_task, auflagen_task)

            # Step 4: Mängel
            maengel = await self._execute_step(
                workflow,
                3,
                self.db_agent.query_entity,
                EntityType.MANGEL,
                {"bst_nr": bst_nr, "anl_nr": anl_nr, "status": "offen"},
            )

            # Step 5: Aggregation
            result = await self._execute_step(
                workflow, 4, self._aggregate_compliance_workflow, base_compliance, verfahren, auflagen, maengel
            )

            # Workflow finalisieren
            if result:
                workflow.result_data = result
                workflow.summary = f"Compliance-Score: {result.get('compliance_score', 0):.0%}"
                workflow.recommendations = result.get("empfehlungen", [])[:5]

                if result.get("compliance_score", 0) < 0.7:
                    workflow.priority = PriorityLevel.HIGH
            else:
                workflow.result_data = {}
                workflow.summary = "Aggregation fehlgeschlagen"

            self._finalize_workflow(workflow)

            return result

        except Exception as e:
            self.logger.error(f"Compliance Workflow failed: {e}")
            workflow.status = WorkflowStatus.FAILED
            self._finalize_workflow(workflow)
            raise

    async def _aggregate_compliance_workflow(
        self,
        base_compliance: Optional[ComplianceResult],
        verfahren: Optional[List],
        auflagen: Optional[Dict],
        maengel: Optional[QueryResult],
    ) -> Dict[str, Any]:
        """Aggregiert Compliance Workflow Ergebnisse"""

        # Verfahren verarbeiten
        verfahren_list = verfahren if isinstance(verfahren, list) else []

        result = {
            "compliance_score": base_compliance.score if base_compliance else 0.0,
            "compliance_status": base_compliance.status.value if base_compliance else "unknown",
            "verfahren": {
                "total": len(verfahren_list),
                "genehmigt": sum(1 for v in verfahren_list if isinstance(v, dict) and v.get("status") == "genehmigt"),
            },
            "auflagen": auflagen if isinstance(auflagen, dict) else {},
            "maengel_offen": len(maengel.data) if maengel and maengel.success and maengel.data else 0,
            "empfehlungen": base_compliance.recommendations if base_compliance else [],
        }

        return result

    # ========================================================================
    # MAINTENANCE PLANNING WORKFLOW
    # ========================================================================

    async def maintenance_planning(self, bst_nr: str, anl_nr: str, planungszeitraum_tage: int = 90) -> Dict[str, Any]:
        """
        Wartungsplanungs-Workflow.

        Workflow:
            1. Wartungshistorie abrufen
            2. Geplante Wartungen abrufen
            3. Mängel-Status prüfen
            4. Überwachungs-Status prüfen
            5. Wartungsplan erstellen

        Returns:
            Dict mit Wartungsplanung
        """
        self.logger.info(f"🔧 Starte Maintenance Planning für {bst_nr}/{anl_nr}")

        workflow = self._create_workflow_result(
            WorkflowType.MAINTENANCE_PLANNING,
            bst_nr,
            anl_nr,
            steps=[
                "Wartungshistorie abrufen",
                "Geplante Wartungen abrufen",
                "Mängel-Status prüfen",
                "Überwachungs-Status prüfen",
                "Wartungsplan erstellen",
            ],
        )

        workflow.status = WorkflowStatus.IN_PROGRESS

        try:
            # Step 1 & 2: Wartungen (parallel)
            historie_task = self._execute_step(
                workflow,
                0,
                self.db_agent.query_entity,
                EntityType.WARTUNG,
                {"bst_nr": bst_nr, "anl_nr": anl_nr, "status": "durchgeführt"},
                100,
            )

            geplant_task = self._execute_step(
                workflow,
                1,
                self.db_agent.query_entity,
                EntityType.WARTUNG,
                {"bst_nr": bst_nr, "anl_nr": anl_nr, "status": "geplant"},
                100,
            )

            historie_result, geplant_result = await asyncio.gather(historie_task, geplant_task)

            # Step 3: Mängel
            maengel_result = await self._execute_step(
                workflow,
                2,
                self.db_agent.query_entity,
                EntityType.MANGEL,
                {"bst_nr": bst_nr, "anl_nr": anl_nr, "status": "offen"},
            )

            # Step 4: Überwachungen
            ueberwachung_result = await self._execute_step(
                workflow, 3, self.db_agent.query_entity, EntityType.UEBERWACHUNG, {"bst_nr": bst_nr, "anl_nr": anl_nr}, 50
            )

            # Step 5: Plan erstellen
            result = await self._execute_step(
                workflow,
                4,
                self._create_maintenance_plan,
                historie_result,
                geplant_result,
                maengel_result,
                ueberwachung_result,
                planungszeitraum_tage,
            )

            # Workflow finalisieren
            if result:
                workflow.result_data = result
                workflow.summary = f"{result.get('wartungen_geplant', 0)} Wartungen geplant"
                workflow.recommendations = result.get("empfehlungen", [])[:5]

                if result.get("kritische_wartungen", 0) > 0:
                    workflow.priority = PriorityLevel.HIGH
            else:
                workflow.result_data = {}
                workflow.summary = "Planung fehlgeschlagen"

            self._finalize_workflow(workflow)

            return result

        except Exception as e:
            self.logger.error(f"Maintenance Planning failed: {e}")
            workflow.status = WorkflowStatus.FAILED
            self._finalize_workflow(workflow)
            raise

    async def _create_maintenance_plan(
        self, historie_result, geplant_result, maengel_result, ueberwachung_result, planungszeitraum_tage: int
    ) -> Dict[str, Any]:
        """Erstellt Wartungsplan"""

        # Sichere Extraktion der Daten
        historie = []
        if historie_result and hasattr(historie_result, "success") and historie_result.success:
            historie = historie_result.data if historie_result.data else []

        geplant = []
        if geplant_result and hasattr(geplant_result, "success") and geplant_result.success:
            geplant = geplant_result.data if geplant_result.data else []

        maengel = []
        if maengel_result and hasattr(maengel_result, "success") and maengel_result.success:
            maengel = maengel_result.data if maengel_result.data else []

        # Analyse
        kritische_maengel = []
        for m in maengel:
            if isinstance(m, dict) and m.get("kategorie") == "kritisch":
                kritische_maengel.append(m)

        empfehlungen = []

        if len(geplant) > 5:
            empfehlungen.append(f"⚠️ {len(geplant)} Wartungen ausstehend - Priorisierung erforderlich")

        if kritische_maengel:
            empfehlungen.append(f"🔴 {len(kritische_maengel)} kritische Mängel - sofortige Wartung")

        if len(historie) < 5:
            empfehlungen.append("💡 Wartungsintervalle überprüfen")

        return {
            "wartungen_durchgefuehrt": len(historie),
            "wartungen_geplant": len(geplant),
            "kritische_wartungen": len(kritische_maengel),
            "planungszeitraum_tage": planungszeitraum_tage,
            "empfehlungen": empfehlungen,
            "naechste_wartungen": geplant[:5] if geplant else [],
        }

    # ========================================================================
    # EMISSION MONITORING WORKFLOW
    # ========================================================================

    async def emission_monitoring(self, bst_nr: str, anl_nr: str) -> Dict[str, Any]:
        """
        Emissions-Überwachungs-Workflow.

        Workflow:
            1. Aktuelle Messungen abrufen
            2. Grenzwerte prüfen
            3. Trends analysieren
            4. Messreihen auswerten
            5. Monitoring-Report erstellen

        Returns:
            Dict mit Emissions-Monitoring
        """
        self.logger.info(f"🌫️ Starte Emission Monitoring für {bst_nr}/{anl_nr}")

        workflow = self._create_workflow_result(
            WorkflowType.EMISSION_MONITORING,
            bst_nr,
            anl_nr,
            steps=[
                "Aktuelle Messungen abrufen",
                "Grenzwerte prüfen",
                "Trends analysieren",
                "Messreihen auswerten",
                "Monitoring-Report erstellen",
            ],
        )

        workflow.status = WorkflowStatus.IN_PROGRESS

        try:
            # Step 1: Messungen
            messungen = await self._execute_step(workflow, 0, self.db_agent.query_messungen, bst_nr, anl_nr, None, None, 200)

            # Step 2: Grenzwerte
            grenzwerte = await self._execute_step(workflow, 1, self.immi_agent.check_grenzwerte, bst_nr, anl_nr)

            # Step 3 & 4: Trends + Messreihen (parallel)
            # Finde häufigste Messarten für Trend-Analyse
            messarten_count = {}
            for m in messungen or []:
                art = m.get("messart", "Unbekannt")
                messarten_count[art] = messarten_count.get(art, 0) + 1

            top_messarten = sorted(messarten_count.items(), key=lambda x: x[1], reverse=True)[:3]

            trend_tasks = []
            for messart, _ in top_messarten:
                task = self._execute_step(workflow, 2, self.immi_agent.analyze_trend, bst_nr, anl_nr, messart, 90)
                trend_tasks.append(task)

            messreihen_task = self._execute_step(
                workflow, 3, self.db_agent.query_entity, EntityType.MESSREIHE, {"bst_nr": bst_nr, "anl_nr": anl_nr}, 50
            )

            # Warten auf alle
            results = await asyncio.gather(*trend_tasks, messreihen_task, return_exceptions=True)
            trends = [r for r in results[:-1] if r and not isinstance(r, Exception)]
            messreihen_result = results[-1] if not isinstance(results[-1], Exception) else None

            # Step 5: Report
            result = await self._execute_step(
                workflow, 4, self._create_emission_monitoring_report, messungen, grenzwerte, trends, messreihen_result
            )

            # Workflow finalisieren
            if result:
                workflow.result_data = result
                workflow.summary = (
                    f"{result.get('messungen_total', 0)} Messungen, {result.get('ueberschreitungen', 0)} Überschreitungen"
                )
                workflow.recommendations = result.get("empfehlungen", [])[:5]

                if result.get("ueberschreitungen", 0) > 0:
                    workflow.priority = PriorityLevel.HIGH
            else:
                workflow.result_data = {}
                workflow.summary = "Report fehlgeschlagen"

            self._finalize_workflow(workflow)

            return result

        except Exception as e:
            self.logger.error(f"Emission Monitoring failed: {e}")
            workflow.status = WorkflowStatus.FAILED
            self._finalize_workflow(workflow)
            raise

    async def _create_emission_monitoring_report(self, messungen, grenzwerte, trends, messreihen_result) -> Dict[str, Any]:
        """Erstellt Emissions-Monitoring Report"""

        # Überschreitungen zählen
        ueberschreitungen = 0
        if grenzwerte:
            for kategorie in grenzwerte.values():
                ueberschreitungen += sum(1 for p in kategorie if p.ist_kritisch)

        # Kritische Trends
        kritische_trends = [t for t in trends if hasattr(t, "ist_kritischer_trend") and t.ist_kritischer_trend]

        # Empfehlungen
        empfehlungen = []

        if ueberschreitungen > 0:
            empfehlungen.append(f"🔴 {ueberschreitungen} Grenzwertüberschreitungen - Maßnahmen einleiten")

        if kritische_trends:
            empfehlungen.append(f"📈 {len(kritische_trends)} kritische Trends - Ursachenanalyse")

        if len(messungen or []) < 10:
            empfehlungen.append("💡 Messfrequenz erhöhen")

        return {
            "messungen_total": len(messungen) if messungen else 0,
            "ueberschreitungen": ueberschreitungen,
            "kritische_trends": len(kritische_trends),
            "messreihen_total": len(messreihen_result.data) if messreihen_result and messreihen_result.success else 0,
            "empfehlungen": empfehlungen,
            "grenzwert_details": grenzwerte or {},
        }

    # ========================================================================
    # WORKFLOW STATUS QUERIES
    # ========================================================================

    def get_workflow_status(self, workflow_id: str) -> Optional[WorkflowResult]:
        """Gibt Status eines Workflows zurück"""
        return self.active_workflows.get(workflow_id)

    def list_active_workflows(self) -> List[WorkflowResult]:
        """Listet alle aktiven Workflows"""
        return list(self.active_workflows.values())


# ============================================================================
# SINGLETON HELPER
# ============================================================================

_orchestrator_instance: Optional[ImmissionsschutzOrchestrator] = None


def get_orchestrator(config: Optional[TestServerConfig] = None) -> ImmissionsschutzOrchestrator:
    """Singleton-Zugriff auf Orchestrator"""
    global _orchestrator_instance

    if _orchestrator_instance is None:
        _orchestrator_instance = ImmissionsschutzOrchestrator(config)

    return _orchestrator_instance


# ============================================================================
# EXAMPLE USAGE
# ============================================================================


async def example_usage():
    """Beispiele für Orchestrator"""
    print("=" * 80)
    print("ImmissionsschutzOrchestrator - Examples")
    print("=" * 80)

    orchestrator = get_orchestrator()

    try:
        # Test-Anlage
        bst_nr = "10686360000"
        anl_nr = "4001"

        # 1. Comprehensive Analysis
        print("\n1️⃣ Comprehensive Analysis")
        print("-" * 60)

        analysis = await orchestrator.comprehensive_analysis(bst_nr, anl_nr)

        print(f"Anlage: {analysis.anlagen_name}")
        print(f"Priorität: {analysis.prioritaet.value}")
        print(f"\nGesamtbewertung:\n{analysis.gesamtbewertung}")

        print(f"\n📊 Compliance: {analysis.compliance_report.compliance_score:.0%}")
        print(f"📊 Risiko: {analysis.risiko_analyse.risiko_score:.0%} ({analysis.risiko_analyse.risiko_klasse.value})")

        print("\n💡 Top Empfehlungen:")
        for i, emp in enumerate(analysis.handlungsempfehlungen[:3], 1):
            print(f"  {i}. {emp}")

        # 2. Compliance Workflow
        print("\n2️⃣ Compliance Workflow")
        print("-" * 60)

        compliance = await orchestrator.compliance_workflow(bst_nr, anl_nr)

        print(f"Compliance-Score: {compliance['compliance_score']:.0%}")
        print(f"Status: {compliance['compliance_status']}")
        print(f"Verfahren: {compliance['verfahren']['genehmigt']}/{compliance['verfahren']['total']} genehmigt")
        print(f"Offene Mängel: {compliance['maengel_offen']}")

        # 3. Maintenance Planning
        print("\n3️⃣ Maintenance Planning")
        print("-" * 60)

        maintenance = await orchestrator.maintenance_planning(bst_nr, anl_nr, 90)

        print(f"Durchgeführt: {maintenance['wartungen_durchgefuehrt']}")
        print(f"Geplant: {maintenance['wartungen_geplant']}")
        print(f"Kritisch: {maintenance['kritische_wartungen']}")

        if maintenance["empfehlungen"]:
            print("\nEmpfehlungen:")
            for emp in maintenance["empfehlungen"]:
                print(f"  • {emp}")

        # 4. Emission Monitoring
        print("\n4️⃣ Emission Monitoring")
        print("-" * 60)

        monitoring = await orchestrator.emission_monitoring(bst_nr, anl_nr)

        print(f"Messungen: {monitoring['messungen_total']}")
        print(f"Überschreitungen: {monitoring['ueberschreitungen']}")
        print(f"Kritische Trends: {monitoring['kritische_trends']}")
        print(f"Messreihen: {monitoring['messreihen_total']}")

        # 5. Workflow Status
        print("\n5️⃣ Workflow Status")
        print("-" * 60)

        active_workflows = orchestrator.list_active_workflows()
        print(f"Aktive Workflows: {len(active_workflows)}")

        for wf in active_workflows[-3:]:  # Letzte 3
            print(f"\n  {wf.workflow_type.value}:")
            print(f"    Status: {wf.status.value}")
            print(f"    Success Rate: {wf.success_rate:.1f}%")
            print(f"    Duration: {wf.total_duration_seconds:.2f}s")

        print("\n" + "=" * 80)
        print("✅ Alle Examples erfolgreich!")

    except Exception as e:
        print(f"❌ Fehler: {e}")
        import traceback

        traceback.print_exc()

    finally:
        await orchestrator.close()


if __name__ == "__main__":
    asyncio.run(example_usage())
