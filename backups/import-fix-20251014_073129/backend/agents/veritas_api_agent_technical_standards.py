"""
VERITAS Technical Standards Agent

Ein spezialisierter Agent für technische Vorschriften, Normen und Standards:
- ISO (International Organization for Standardization)
- DIN (Deutsches Institut für Normung)
- VDE (Verband der Elektrotechnik)
- EN (Europäische Normen)
- ANSI (American National Standards Institute)
- IEC (International Electrotechnical Commission)
- IEEE (Institute of Electrical and Electronics Engineers)
- ASTM (American Society for Testing and Materials)

Hauptfunktionen:
- Normen-Suche und -Abruf
- Compliance-Prüfung und Gap-Analyse
- Aktualitätsprüfung und Änderungsverfolgun
- Normenhierarchie und -abhängigkeiten
- Anwendungsbereich-Analyse
- Zertifizierungsanforderungen

Autor: VERITAS Agent System
Datum: 28. September 2025
Version: 1.0.0
"""

import asyncio
import logging
import time
import uuid
import re
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Union, Tuple
import json
import hashlib

# Mock Standards Database (wird durch echte APIs ersetzt)
try:
    import requests
    import xml.etree.ElementTree as ET
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    print("⚠️  Requests nicht installiert - verwende Mock-Daten")
    print("   Installation: pip install requests")

# Integration mit anderen VERITAS Agents
try:
    from .veritas_api_agent_chemical_data import ChemicalSubstance, ChemicalDataAgent
    CHEMICAL_INTEGRATION_AVAILABLE = True
except ImportError:
    CHEMICAL_INTEGRATION_AVAILABLE = False
    print("⚠️  Chemical Data Agent Integration nicht verfügbar")


# =============================================================================
# TECHNICAL STANDARDS ENUMS UND KONFIGURATION
# =============================================================================

class StandardsOrganization(Enum):
    """Normungsorganisationen"""
    ISO = "iso"                            # International Organization for Standardization
    DIN = "din"                            # Deutsches Institut für Normung
    VDE = "vde"                            # Verband der Elektrotechnik
    EN = "en"                              # Europäische Normen
    ANSI = "ansi"                          # American National Standards Institute
    IEC = "iec"                            # International Electrotechnical Commission
    IEEE = "ieee"                          # Institute of Electrical and Electronics Engineers
    ASTM = "astm"                          # American Society for Testing and Materials
    NFPA = "nfpa"                          # National Fire Protection Association
    UL = "ul"                              # Underwriters Laboratories
    CE = "ce"                              # Conformité Européenne
    FCC = "fcc"                            # Federal Communications Commission
    OSHA = "osha"                          # Occupational Safety and Health Administration
    EPA = "epa"                            # Environmental Protection Agency
    FDA = "fda"                            # Food and Drug Administration


class StandardCategory(Enum):
    """Normenkategorien"""
    SAFETY = "safety"                      # Sicherheitsvorschriften
    ELECTRICAL = "electrical"              # Elektrotechnik
    ENVIRONMENTAL = "environmental"        # Umweltschutz
    QUALITY = "quality"                    # Qualitätsmanagement
    TESTING = "testing"                    # Prüfverfahren
    MATERIALS = "materials"                # Werkstoffnormen
    CONSTRUCTION = "construction"          # Bauwesen
    AUTOMOTIVE = "automotive"              # Fahrzeugtechnik
    MEDICAL = "medical"                    # Medizintechnik
    INFORMATION_TECHNOLOGY = "information_technology"  # IT/Software
    TELECOMMUNICATIONS = "telecommunications"          # Telekommunikation
    ENERGY = "energy"                      # Energietechnik
    MACHINERY = "machinery"                # Maschinenbau
    CHEMICAL = "chemical"                  # Chemische Industrie
    FOOD = "food"                          # Lebensmitteltechnik


class StandardStatus(Enum):
    """Normenstatus"""
    ACTIVE = "active"                      # Aktiv/gültig
    WITHDRAWN = "withdrawn"                # Zurückgezogen
    SUPERSEDED = "superseded"              # Ersetzt
    UNDER_REVIEW = "under_review"          # In Überarbeitung
    DRAFT = "draft"                        # Entwurf
    PUBLISHED = "published"                # Veröffentlicht
    CANCELLED = "cancelled"                # Storniert


class ComplianceLevel(Enum):
    """Compliance-Level"""
    MANDATORY = "mandatory"                # Verpflichtend
    RECOMMENDED = "recommended"            # Empfohlen
    OPTIONAL = "optional"                  # Optional
    INFORMATIVE = "informative"            # Informativ


# =============================================================================
# TECHNICAL STANDARDS STRUKTUREN
# =============================================================================

@dataclass
class StandardIdentifier:
    """Standard-Identifikator"""
    standard_number: str                   # z.B. "ISO 9001", "DIN EN 1234"
    organization: StandardsOrganization
    full_title: str
    version: str = ""                      # z.B. "2015", "2023-01"
    language: str = "de"
    
    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result['organization'] = self.organization.value
        return result


@dataclass
class StandardRequirement:
    """Einzelne Norm-Anforderung"""
    requirement_id: str                    # Eindeutige ID
    section: str                           # Abschnitt in der Norm
    title: str                             # Anforderungstitel
    description: str                       # Detailbeschreibung
    compliance_level: ComplianceLevel
    
    # Verification
    test_methods: List[str] = field(default_factory=list)
    acceptance_criteria: str = ""
    documentation_required: List[str] = field(default_factory=list)
    
    # References
    referenced_standards: List[str] = field(default_factory=list)
    related_requirements: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result['compliance_level'] = self.compliance_level.value
        return result


@dataclass
class StandardApplication:
    """Anwendungsbereich einer Norm"""
    application_id: str
    scope_description: str                 # Anwendungsbereich
    included_products: List[str] = field(default_factory=list)
    excluded_products: List[str] = field(default_factory=list)
    geographical_scope: List[str] = field(default_factory=list)  # Länder/Regionen
    industry_sectors: List[StandardCategory] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result['industry_sectors'] = [sector.value for sector in self.industry_sectors]
        return result


@dataclass
class StandardRevision:
    """Norm-Revision/Änderung"""
    revision_date: str
    version_number: str
    change_summary: str
    major_changes: List[str] = field(default_factory=list)
    transition_period_months: Optional[int] = None
    predecessor_standard: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class CertificationInfo:
    """Zertifizierungsinformationen"""
    certification_body: str               # Zertifizierungsstelle
    certificate_type: str                 # Art des Zertifikats
    validity_period_months: Optional[int] = None
    renewal_requirements: List[str] = field(default_factory=list)
    assessment_criteria: List[str] = field(default_factory=list)
    costs_estimate: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class TechnicalStandard:
    """Vollständige technische Norm"""
    standard_id: str
    identifier: StandardIdentifier
    status: StandardStatus
    
    # Basis-Informationen
    publication_date: str
    last_review_date: str = ""
    next_review_date: str = ""
    
    # Inhalt
    abstract: str = ""
    scope_and_application: Optional[StandardApplication] = None
    requirements: List[StandardRequirement] = field(default_factory=list)
    
    # Struktur
    sections: List[str] = field(default_factory=list)
    annexes: List[str] = field(default_factory=list)
    page_count: Optional[int] = None
    
    # Beziehungen
    supersedes: List[str] = field(default_factory=list)
    superseded_by: List[str] = field(default_factory=list)
    related_standards: List[str] = field(default_factory=list)
    referenced_by: List[str] = field(default_factory=list)
    
    # Revision
    revisions: List[StandardRevision] = field(default_factory=list)
    
    # Zertifizierung
    certification_info: Optional[CertificationInfo] = None
    
    # Metadaten
    categories: List[StandardCategory] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)
    technical_committees: List[str] = field(default_factory=list)
    
    # Verfügbarkeit
    purchase_url: str = ""
    preview_available: bool = False
    free_access: bool = False
    price_estimate: str = ""
    
    # Qualität
    relevance_score: float = 0.0           # 0.0-1.0
    data_sources: List[str] = field(default_factory=list)
    last_updated: str = ""
    
    def get_current_version(self) -> str:
        """Aktuelle Version ermitteln"""
        if self.revisions:
            latest = max(self.revisions, key=lambda r: r.revision_date)
            return latest.version_number
        return self.identifier.version
    
    def is_current(self) -> bool:
        """Prüfen ob Norm aktuell ist"""
        return self.status == StandardStatus.ACTIVE
    
    def get_mandatory_requirements(self) -> List[StandardRequirement]:
        """Verpflichtende Anforderungen abrufen"""
        return [req for req in self.requirements if req.compliance_level == ComplianceLevel.MANDATORY]
    
    def get_requirements_by_section(self, section: str) -> List[StandardRequirement]:
        """Anforderungen nach Abschnitt filtern"""
        return [req for req in self.requirements if req.section == section]
    
    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result['identifier'] = self.identifier.to_dict()
        result['status'] = self.status.value
        if self.scope_and_application:
            result['scope_and_application'] = self.scope_and_application.to_dict()
        result['requirements'] = [req.to_dict() for req in self.requirements]
        result['revisions'] = [rev.to_dict() for rev in self.revisions]
        result['categories'] = [cat.value for cat in self.categories]
        if self.certification_info:
            result['certification_info'] = self.certification_info.to_dict()
        return result


# =============================================================================
# STANDARDS REQUEST/RESPONSE
# =============================================================================

@dataclass
class StandardsSearchRequest:
    """Request für Standards Agent"""
    query_id: str
    query_text: str
    
    # Suchparameter
    search_term: str                       # Nummer, Titel, Stichwort
    organization: Optional[StandardsOrganization] = None
    category: Optional[StandardCategory] = None
    
    # Filter
    status_filter: List[StandardStatus] = field(default_factory=lambda: [StandardStatus.ACTIVE])
    publication_year_from: Optional[int] = None
    publication_year_to: Optional[int] = None
    language: str = "de"
    
    # Inhaltsanforderungen
    include_requirements: bool = True
    include_revisions: bool = False
    include_related_standards: bool = True
    include_certification_info: bool = False
    
    # Spezifische Abfragen
    product_scope: str = ""                # Produktbereich
    industry_sector: Optional[StandardCategory] = None
    compliance_level: Optional[ComplianceLevel] = None
    
    # Ergebnissteuerung
    max_results: int = 10
    min_relevance_score: float = 0.5
    include_superseded: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        if self.organization:
            result['organization'] = self.organization.value
        if self.category:
            result['category'] = self.category.value
        result['status_filter'] = [status.value for status in self.status_filter]
        if self.industry_sector:
            result['industry_sector'] = self.industry_sector.value
        if self.compliance_level:
            result['compliance_level'] = self.compliance_level.value
        return result


@dataclass
class ComplianceAssessment:
    """Compliance-Bewertung"""
    assessment_id: str
    target_standard: str                   # Ziel-Norm
    assessment_date: str
    
    # Bewertungsergebnis
    overall_compliance_level: float        # 0.0-1.0
    compliant_requirements: int
    non_compliant_requirements: int
    partial_compliance: int
    total_requirements: int
    
    # Details
    compliance_gaps: List[Dict[str, Any]] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    priority_actions: List[str] = field(default_factory=list)
    
    # Zertifizierung
    certification_readiness: float = 0.0   # 0.0-1.0
    estimated_effort_days: Optional[int] = None
    cost_estimate: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class StandardsSearchResponse:
    """Response für Standards Agent"""
    query_id: str
    success: bool
    
    # Ergebnisse
    standards: List[TechnicalStandard] = field(default_factory=list)
    
    # Suchinformationen
    search_term_used: str = ""
    standards_found: int = 0
    exact_matches: int = 0
    
    # Compliance-Analyse (optional)
    compliance_assessment: Optional[ComplianceAssessment] = None
    
    # Datenqualität
    average_relevance_score: float = 0.0
    data_sources_used: List[str] = field(default_factory=list)
    
    # Performance
    processing_time_ms: int = 0
    api_calls_made: int = 0
    cache_hits: int = 0
    
    # Confidence & Warnings
    confidence_score: float = 0.0
    warnings: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)  # Alternative Suchbegriffe
    
    # Error handling
    error_message: Optional[str] = None
    
    def get_by_organization(self, org: StandardsOrganization) -> List[TechnicalStandard]:
        """Standards nach Organisation filtern"""
        return [std for std in self.standards if std.identifier.organization == org]
    
    def get_by_category(self, category: StandardCategory) -> List[TechnicalStandard]:
        """Standards nach Kategorie filtern"""
        return [std for std in self.standards if category in std.categories]
    
    def get_mandatory_standards(self) -> List[TechnicalStandard]:
        """Verpflichtende Standards abrufen"""
        return [std for std in self.standards 
                if any(req.compliance_level == ComplianceLevel.MANDATORY 
                       for req in std.requirements)]
    
    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result['standards'] = [std.to_dict() for std in self.standards]
        if self.compliance_assessment:
            result['compliance_assessment'] = self.compliance_assessment.to_dict()
        return result


# =============================================================================
# TECHNICAL STANDARDS AGENT KONFIGURATION
# =============================================================================

@dataclass
class TechnicalStandardsConfig:
    """Technical Standards Agent Konfiguration"""
    
    # Datenquellen
    enabled_organizations: List[StandardsOrganization] = field(default_factory=lambda: [
        StandardsOrganization.ISO, StandardsOrganization.DIN, StandardsOrganization.VDE,
        StandardsOrganization.EN, StandardsOrganization.IEC, StandardsOrganization.IEEE
    ])
    
    # API-Konfiguration
    iso_base_url: str = "https://www.iso.org/api"
    din_base_url: str = "https://www.din.de/api"
    vde_base_url: str = "https://www.vde.com/api"
    iec_base_url: str = "https://webstore.iec.ch/api"
    ieee_base_url: str = "https://standards.ieee.org/api"
    
    # Cache-Einstellungen
    cache_enabled: bool = True
    cache_ttl_seconds: int = 14400          # 4 Stunden
    max_cache_size: int = 2000
    
    # Performance
    max_concurrent_requests: int = 3
    request_timeout_seconds: int = 45
    max_retries: int = 2
    rate_limit_delay: float = 1.0          # Normen-APIs sind oft langsamer
    
    # Datenqualität
    min_relevance_threshold: float = 0.4
    require_current_standards: bool = True
    verify_organization: bool = True
    
    # Sprache
    default_language: str = "de"
    supported_languages: List[str] = field(default_factory=lambda: ["de", "en"])
    
    # Compliance
    compliance_threshold: float = 0.8       # 80% für "compliant"
    assessment_detail_level: str = "standard"  # "basic", "standard", "detailed"
    
    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result['enabled_organizations'] = [org.value for org in self.enabled_organizations]
        return result


# =============================================================================
# TECHNICAL STANDARDS AGENT HAUPTKLASSE
# =============================================================================

class TechnicalStandardsAgent:
    """
    VERITAS Technical Standards Agent
    
    Spezialisierter Agent für technische Normen und Vorschriften:
    - ISO, DIN, VDE, EN, IEC, IEEE, ASTM Standards
    - Compliance-Prüfung und Gap-Analyse
    - Aktualitätsprüfung und Änderungsverfolgung
    - Normenhierarchie und -abhängigkeiten
    - Zertifizierungsanforderungen
    """
    
    def __init__(self, config: TechnicalStandardsConfig = None):
        self.config = config or TechnicalStandardsConfig()
        self.logger = logging.getLogger(f"{__name__}.TechnicalStandardsAgent")
        
        # Caches
        self._standards_cache: Dict[str, TechnicalStandard] = {}
        self._search_cache: Dict[str, StandardsSearchResponse] = {}
        self._compliance_cache: Dict[str, ComplianceAssessment] = {}
        
        # Performance tracking
        self._stats = {
            'queries_processed': 0,
            'standards_found': 0,
            'compliance_assessments': 0,
            'api_calls_made': 0,
            'cache_hits': 0,
            'errors': 0,
            'avg_processing_time_ms': 0,
            'total_processing_time_ms': 0,
            'organizations_queried': set()
        }
        
        self.logger.info(f"✅ Technical Standards Agent initialized with {len(self.config.enabled_organizations)} organizations")
    
    # =========================================================================
    # HAUPT-QUERY-METHODEN
    # =========================================================================
    
    async def search_standards_async(self, request: StandardsSearchRequest) -> StandardsSearchResponse:
        """Asynchrone Standards-Suche (Haupt-Methode)"""
        start_time = time.time()
        
        try:
            self.logger.info(f"🔍 Processing standards search: {request.query_text}")
            
            # Cache-Check
            cache_key = self._generate_cache_key(request)
            if self.config.cache_enabled and cache_key in self._search_cache:
                self.logger.debug("📋 Using cached standards result")
                self._stats['cache_hits'] += 1
                cached_response = self._search_cache[cache_key]
                cached_response.processing_time_ms = int((time.time() - start_time) * 1000)
                return cached_response
            
            # Standards suchen
            standards = await self._search_technical_standards(request)
            
            # Compliance-Bewertung (wenn spezifische Anforderungen)
            compliance_assessment = None
            if request.product_scope and standards:
                compliance_assessment = await self._assess_compliance(standards[0], request.product_scope)
            
            # Response erstellen
            response = StandardsSearchResponse(
                query_id=request.query_id,
                success=len(standards) > 0,
                standards=standards,
                search_term_used=request.search_term,
                standards_found=len(standards),
                exact_matches=len([s for s in standards if s.relevance_score > 0.9]),
                compliance_assessment=compliance_assessment
            )
            
            # Statistiken berechnen
            if standards:
                response.average_relevance_score = sum(s.relevance_score for s in standards) / len(standards)
                response.confidence_score = min(0.95, response.average_relevance_score)
                
                # Alle verwendeten Datenquellen sammeln
                all_sources = set()
                for standard in standards:
                    all_sources.update(standard.data_sources)
                response.data_sources_used = list(all_sources)
            
            # Processing time
            processing_time = int((time.time() - start_time) * 1000)
            response.processing_time_ms = processing_time
            
            # Stats update
            self._update_stats(processing_time, len(standards))
            
            # Cache-Speicherung
            if self.config.cache_enabled and response.success:
                self._search_cache[cache_key] = response
                self._cleanup_cache()
            
            self.logger.info(f"✅ Standards search completed: {len(standards)} standards in {processing_time}ms")
            return response
            
        except Exception as e:
            error_msg = f"Standards search error: {str(e)}"
            self.logger.error(error_msg)
            self._stats['errors'] += 1
            
            return StandardsSearchResponse(
                query_id=request.query_id,
                success=False,
                error_message=error_msg,
                processing_time_ms=int((time.time() - start_time) * 1000)
            )
    
    def search_standards(self, request: StandardsSearchRequest) -> StandardsSearchResponse:
        """Synchrone Standards-Suche"""
        return asyncio.run(self.search_standards_async(request))
    
    # =========================================================================
    # STANDARDS-SUCHE
    # =========================================================================
    
    async def _search_technical_standards(self, request: StandardsSearchRequest) -> List[TechnicalStandard]:
        """Suche nach technischen Standards"""
        standards = []
        
        try:
            # 1. Direkte Nummern-Suche
            if self._is_standard_number(request.search_term):
                standard = await self._search_by_number(request.search_term)
                if standard:
                    standards.append(standard)
            
            # 2. Organisation-spezifische Suche
            if request.organization:
                org_standards = await self._search_by_organization(
                    request.organization, request.search_term, request.max_results
                )
                standards.extend(org_standards)
            else:
                # Alle aktivierten Organisationen durchsuchen
                for org in self.config.enabled_organizations:
                    org_standards = await self._search_by_organization(
                        org, request.search_term, max(1, request.max_results // len(self.config.enabled_organizations))
                    )
                    standards.extend(org_standards)
            
            # 3. Kategorie-basierte Suche
            if request.category:
                category_standards = await self._search_by_category(request.category, request.search_term)
                standards.extend(category_standards)
            
            # 4. Filter anwenden
            standards = self._apply_filters(standards, request)
            
            # 5. Nach Relevanz sortieren
            standards.sort(key=lambda s: s.relevance_score, reverse=True)
            
            return standards[:request.max_results]
            
        except Exception as e:
            self.logger.error(f"Technical standards search error: {e}")
            return []
    
    def _is_standard_number(self, term: str) -> bool:
        """Prüfen ob Term eine Standard-Nummer ist"""
        # Patterns für Standard-Nummern
        patterns = [
            r'^ISO\s*\d+',                  # ISO 9001
            r'^DIN\s*(EN\s*)?\d+',          # DIN 1234, DIN EN 1234
            r'^VDE\s*\d+',                  # VDE 0100
            r'^EN\s*\d+',                   # EN 1234
            r'^IEC\s*\d+',                  # IEC 61508
            r'^IEEE\s*\d+',                 # IEEE 802.11
            r'^ASTM\s*[A-Z]\d+',           # ASTM D1234
            r'^ANSI\s*[A-Z]*\d+'           # ANSI Z136.1
        ]
        
        for pattern in patterns:
            if re.match(pattern, term.upper().strip()):
                return True
        return False
    
    async def _search_by_number(self, standard_number: str) -> Optional[TechnicalStandard]:
        """Suche nach Standard-Nummer"""
        # Für Demo: Mock-Daten für bekannte Standards
        mock_standards = {
            "ISO 9001": {
                "title": "Qualitätsmanagementsysteme - Anforderungen",
                "org": StandardsOrganization.ISO,
                "category": StandardCategory.QUALITY,
                "status": StandardStatus.ACTIVE,
                "version": "2015"
            },
            "DIN EN 1090": {
                "title": "Ausführung von Stahl- und Aluminiumtragwerken",
                "org": StandardsOrganization.DIN,
                "category": StandardCategory.CONSTRUCTION,
                "status": StandardStatus.ACTIVE,
                "version": "2018"
            },
            "VDE 0100": {
                "title": "Errichten von Niederspannungsanlagen",
                "org": StandardsOrganization.VDE,
                "category": StandardCategory.ELECTRICAL,
                "status": StandardStatus.ACTIVE,
                "version": "2021"
            },
            "IEC 61508": {
                "title": "Funktionale Sicherheit sicherheitsbezogener elektrischer/elektronischer/programmierbarer elektronischer Systeme",
                "org": StandardsOrganization.IEC,
                "category": StandardCategory.SAFETY,
                "status": StandardStatus.ACTIVE,
                "version": "2010"
            },
            "IEEE 802.11": {
                "title": "Wireless LAN Medium Access Control (MAC) and Physical Layer (PHY) Specifications",
                "org": StandardsOrganization.IEEE,
                "category": StandardCategory.TELECOMMUNICATIONS,
                "status": StandardStatus.ACTIVE,
                "version": "2020"
            }
        }
        
        # Normalisiere Sucheingabe
        search_key = standard_number.upper().strip()
        for key, data in mock_standards.items():
            if key.upper() in search_key or search_key in key.upper():
                return await self._create_mock_standard(key, data)
        
        return None
    
    async def _search_by_organization(self, org: StandardsOrganization, search_term: str, max_results: int) -> List[TechnicalStandard]:
        """Suche nach Organisation"""
        standards = []
        self._stats['organizations_queried'].add(org.value)
        
        # Mock-Daten für verschiedene Organisationen
        org_standards = {
            StandardsOrganization.ISO: [
                ("ISO 9001", "Qualitätsmanagementsysteme", StandardCategory.QUALITY),
                ("ISO 14001", "Umweltmanagementsysteme", StandardCategory.ENVIRONMENTAL),
                ("ISO 27001", "Informationssicherheitsmanagementsysteme", StandardCategory.INFORMATION_TECHNOLOGY),
                ("ISO 45001", "Arbeitsschutz- und Sicherheitsmanagementsysteme", StandardCategory.SAFETY)
            ],
            StandardsOrganization.DIN: [
                ("DIN EN 1090", "Ausführung von Stahl- und Aluminiumtragwerken", StandardCategory.CONSTRUCTION),
                ("DIN 18040", "Barrierefreies Bauen", StandardCategory.CONSTRUCTION),
                ("DIN 4109", "Schallschutz im Hochbau", StandardCategory.CONSTRUCTION),
                ("DIN 1052", "Entwurf, Berechnung und Bemessung von Holzbauwerken", StandardCategory.CONSTRUCTION)
            ],
            StandardsOrganization.VDE: [
                ("VDE 0100", "Errichten von Niederspannungsanlagen", StandardCategory.ELECTRICAL),
                ("VDE 0113", "Sicherheit von Maschinen - Elektrische Ausrüstung", StandardCategory.ELECTRICAL),
                ("VDE 0701", "Prüfung nach Instandsetzung elektrischer Geräte", StandardCategory.TESTING),
                ("VDE 0105", "Betrieb von elektrischen Anlagen", StandardCategory.ELECTRICAL)
            ],
            StandardsOrganization.IEC: [
                ("IEC 61508", "Funktionale Sicherheit", StandardCategory.SAFETY),
                ("IEC 60364", "Niederspannungsanlagen", StandardCategory.ELECTRICAL),
                ("IEC 62304", "Medizingeräte-Software", StandardCategory.MEDICAL),
                ("IEC 61131", "Speicherprogrammierbare Steuerungen", StandardCategory.MACHINERY)
            ]
        }
        
        if org in org_standards:
            search_lower = search_term.lower()
            matches = []
            
            for number, title, category in org_standards[org]:
                relevance = 0.0
                
                # Exakte Nummer-Übereinstimmung
                if search_lower in number.lower():
                    relevance = 0.95
                # Titel-Übereinstimmung
                elif any(word in title.lower() for word in search_lower.split()):
                    relevance = 0.7
                # Kategorie-Übereinstimmung
                elif search_lower in category.value:
                    relevance = 0.5
                
                if relevance > 0:
                    matches.append((number, title, category, relevance))
            
            # Nach Relevanz sortieren
            matches.sort(key=lambda x: x[3], reverse=True)
            
            for number, title, category, relevance in matches[:max_results]:
                standard_data = {
                    "title": title,
                    "org": org,
                    "category": category,
                    "status": StandardStatus.ACTIVE,
                    "version": "2023"
                }
                
                standard = await self._create_mock_standard(number, standard_data)
                if standard:
                    standard.relevance_score = relevance
                    standards.append(standard)
        
        return standards
    
    async def _search_by_category(self, category: StandardCategory, search_term: str) -> List[TechnicalStandard]:
        """Suche nach Kategorie"""
        standards = []
        
        # Mock-Standards für verschiedene Kategorien
        category_standards = {
            StandardCategory.SAFETY: [
                ("ISO 45001", "Arbeitsschutz- und Sicherheitsmanagementsysteme", StandardsOrganization.ISO),
                ("IEC 61508", "Funktionale Sicherheit", StandardsOrganization.IEC),
                ("OSHA 29 CFR 1910", "Allgemeine Industrie-Sicherheitsstandards", StandardsOrganization.OSHA)
            ],
            StandardCategory.ELECTRICAL: [
                ("VDE 0100", "Errichten von Niederspannungsanlagen", StandardsOrganization.VDE),
                ("IEC 60364", "Niederspannungsanlagen", StandardsOrganization.IEC),
                ("IEEE 802.11", "Wireless LAN Standards", StandardsOrganization.IEEE)
            ],
            StandardCategory.ENVIRONMENTAL: [
                ("ISO 14001", "Umweltmanagementsysteme", StandardsOrganization.ISO),
                ("EPA 40 CFR", "Environmental Protection Regulations", StandardsOrganization.EPA)
            ]
        }
        
        if category in category_standards:
            for number, title, org in category_standards[category]:
                standard_data = {
                    "title": title,
                    "org": org,
                    "category": category,
                    "status": StandardStatus.ACTIVE,
                    "version": "2023"
                }
                
                standard = await self._create_mock_standard(number, standard_data)
                if standard:
                    standard.relevance_score = 0.8
                    standards.append(standard)
        
        return standards
    
    async def _create_mock_standard(self, number: str, data: Dict[str, Any]) -> TechnicalStandard:
        """Mock-Standard erstellen"""
        
        # Standard-Identifier
        identifier = StandardIdentifier(
            standard_number=number,
            organization=data["org"],
            full_title=f"{number}:{data['version']} {data['title']}",
            version=data["version"],
            language="de"
        )
        
        # Application Scope
        scope = StandardApplication(
            application_id=f"scope_{number.replace(' ', '_').lower()}",
            scope_description=f"Anwendungsbereich für {data['title']}",
            industry_sectors=[data["category"]]
        )
        
        # Mock Requirements
        requirements = await self._create_mock_requirements(number, data["category"])
        
        # Standard erstellen
        standard = TechnicalStandard(
            standard_id=f"std_{number.replace(' ', '_').lower()}",
            identifier=identifier,
            status=data["status"],
            publication_date=f"{data['version']}-01-01",
            last_review_date=f"{data['version']}-01-01",
            next_review_date=f"{int(data['version']) + 5}-01-01",
            abstract=f"Diese Norm legt {data['title'].lower()} fest.",
            scope_and_application=scope,
            requirements=requirements,
            sections=["1 Anwendungsbereich", "2 Normative Verweisungen", "3 Begriffe", "4 Anforderungen", "5 Prüfung"],
            categories=[data["category"]],
            keywords=[data['title'].lower(), number.lower()],
            technical_committees=[f"TC {data['org'].value.upper()}"],
            relevance_score=0.9,
            data_sources=["mock_standards_db"],
            last_updated=datetime.now().isoformat(),
            free_access=False,
            price_estimate="50-200 EUR"
        )
        
        return standard
    
    async def _create_mock_requirements(self, standard_number: str, category: StandardCategory) -> List[StandardRequirement]:
        """Mock-Anforderungen für Standard erstellen"""
        requirements = []
        
        # Standard-spezifische Anforderungen
        if "9001" in standard_number:  # ISO 9001 QMS
            requirements = [
                StandardRequirement(
                    requirement_id="ISO9001-4.1",
                    section="4.1",
                    title="Verstehen der Organisation und ihres Kontextes",
                    description="Die Organisation muss interne und externe Themen bestimmen, die für ihren Zweck relevant sind.",
                    compliance_level=ComplianceLevel.MANDATORY,
                    acceptance_criteria="Dokumentierte Kontextanalyse vorhanden",
                    documentation_required=["Kontextanalyse", "SWOT-Analyse"]
                ),
                StandardRequirement(
                    requirement_id="ISO9001-5.2",
                    section="5.2",
                    title="Politik",
                    description="Die oberste Leitung muss eine Qualitätspolitik erstellen und aufrechterhalten.",
                    compliance_level=ComplianceLevel.MANDATORY,
                    acceptance_criteria="Qualitätspolitik dokumentiert und kommuniziert",
                    documentation_required=["Qualitätspolitik"]
                )
            ]
        elif "VDE" in standard_number:  # VDE Elektrische Sicherheit
            requirements = [
                StandardRequirement(
                    requirement_id="VDE-001",
                    section="4.2.1",
                    title="Schutz gegen elektrischen Schlag",
                    description="Schutzmaßnahmen gegen direktes und indirektes Berühren unter Spannung stehender Teile.",
                    compliance_level=ComplianceLevel.MANDATORY,
                    test_methods=["Isolationsprüfung", "Schutzleiterprüfung"],
                    acceptance_criteria="Isolationswiderstand > 1 MΩ"
                ),
                StandardRequirement(
                    requirement_id="VDE-002", 
                    section="5.1",
                    title="Leitungsverlegung",
                    description="Vorschriften für die Installation von Kabeln und Leitungen.",
                    compliance_level=ComplianceLevel.MANDATORY,
                    documentation_required=["Installationsplan", "Leitungsverzeichnis"]
                )
            ]
        elif "61508" in standard_number:  # IEC 61508 Funktionale Sicherheit
            requirements = [
                StandardRequirement(
                    requirement_id="IEC61508-1",
                    section="7.4.2",
                    title="Sicherheits-Integritätslevel (SIL)",
                    description="Bestimmung und Nachweis des erforderlichen SIL für sicherheitsbezogene Systeme.",
                    compliance_level=ComplianceLevel.MANDATORY,
                    test_methods=["SIL-Bewertung", "FMEDA", "Markov-Analyse"],
                    acceptance_criteria="SIL-Nachweis entsprechend Risikoanalyse"
                )
            ]
        else:
            # Generische Anforderungen
            requirements = [
                StandardRequirement(
                    requirement_id=f"{standard_number.replace(' ', '')}-GEN-001",
                    section="4.1",
                    title="Allgemeine Anforderungen",
                    description=f"Grundlegende Anforderungen für {category.value} Standards.",
                    compliance_level=ComplianceLevel.MANDATORY,
                    acceptance_criteria="Erfüllung der Grundanforderungen nachgewiesen"
                )
            ]
        
        return requirements
    
    def _apply_filters(self, standards: List[TechnicalStandard], request: StandardsSearchRequest) -> List[TechnicalStandard]:
        """Filter auf Standards anwenden"""
        filtered = standards
        
        # Status Filter
        if request.status_filter:
            filtered = [s for s in filtered if s.status in request.status_filter]
        
        # Publikationsjahr Filter
        if request.publication_year_from:
            filtered = [s for s in filtered if int(s.publication_date[:4]) >= request.publication_year_from]
        
        if request.publication_year_to:
            filtered = [s for s in filtered if int(s.publication_date[:4]) <= request.publication_year_to]
        
        # Relevanz Filter
        filtered = [s for s in filtered if s.relevance_score >= request.min_relevance_score]
        
        # Superseded ausschließen
        if not request.include_superseded:
            filtered = [s for s in filtered if s.status != StandardStatus.SUPERSEDED]
        
        return filtered
    
    # =========================================================================
    # COMPLIANCE-BEWERTUNG
    # =========================================================================
    
    async def _assess_compliance(self, standard: TechnicalStandard, product_scope: str) -> ComplianceAssessment:
        """Compliance-Bewertung für Standard"""
        
        # Mock Compliance Assessment
        total_requirements = len(standard.requirements)
        
        # Simuliere Compliance-Level basierend auf Standard-Typ
        if standard.identifier.organization == StandardsOrganization.ISO:
            compliance_rate = 0.85  # Typisch für ISO Standards
        elif standard.identifier.organization == StandardsOrganization.VDE:
            compliance_rate = 0.75  # Elektrische Sicherheit ist anspruchsvoll
        else:
            compliance_rate = 0.80
        
        compliant = int(total_requirements * compliance_rate)
        non_compliant = int(total_requirements * 0.1)
        partial = total_requirements - compliant - non_compliant
        
        # Gap-Analyse
        gaps = []
        if non_compliant > 0:
            gaps.append({
                "requirement_id": f"{standard.identifier.standard_number}-GAP-001",
                "gap_description": "Dokumentation unvollständig",
                "priority": "high",
                "estimated_effort_days": 5
            })
        
        assessment = ComplianceAssessment(
            assessment_id=f"assess_{standard.standard_id}_{int(time.time())}",
            target_standard=standard.identifier.standard_number,
            assessment_date=datetime.now().isoformat(),
            overall_compliance_level=compliance_rate,
            compliant_requirements=compliant,
            non_compliant_requirements=non_compliant,
            partial_compliance=partial,
            total_requirements=total_requirements,
            compliance_gaps=gaps,
            recommendations=[
                f"Vervollständigung der Dokumentation für {standard.identifier.standard_number}",
                "Implementierung fehrender Prüfverfahren",
                "Schulung der Mitarbeiter zu den Anforderungen"
            ],
            priority_actions=[
                "Sofortige Behebung sicherheitskritischer Mängel"
            ],
            certification_readiness=compliance_rate * 0.9,
            estimated_effort_days=gaps[0]["estimated_effort_days"] if gaps else 0,
            cost_estimate=f"{5000 + len(gaps) * 2000}-{10000 + len(gaps) * 5000} EUR"
        )
        
        self._stats['compliance_assessments'] += 1
        return assessment
    
    # =========================================================================
    # UTILITY-METHODEN
    # =========================================================================
    
    def _generate_cache_key(self, request: StandardsSearchRequest) -> str:
        """Cache-Schlüssel generieren"""
        key_parts = [
            request.search_term,
            request.organization.value if request.organization else "",
            request.category.value if request.category else "",
            str(request.max_results)
        ]
        key_string = "|".join(key_parts)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def _update_stats(self, processing_time: int, standards_found: int):
        """Statistiken aktualisieren"""
        self._stats['queries_processed'] += 1
        self._stats['standards_found'] += standards_found
        self._stats['total_processing_time_ms'] += processing_time
        
        # Durchschnittliche Processing-Time
        self._stats['avg_processing_time_ms'] = (
            self._stats['total_processing_time_ms'] / self._stats['queries_processed']
        )
    
    def _cleanup_cache(self):
        """Cache-Cleanup bei Überlauf"""
        if len(self._search_cache) > self.config.max_cache_size:
            # Entferne 20% der ältesten Einträge
            items_to_remove = len(self._search_cache) // 5
            keys_to_remove = list(self._search_cache.keys())[:items_to_remove]
            for key in keys_to_remove:
                del self._search_cache[key]
    
    def get_status(self) -> Dict[str, Any]:
        """Agent-Status abrufen"""
        return {
            "agent_type": "technical_standards",
            "version": "1.0.0",
            "status": "active",
            "requests_available": REQUESTS_AVAILABLE,
            "config": self.config.to_dict(),
            "performance": {
                "queries_processed": self._stats['queries_processed'],
                "standards_found": self._stats['standards_found'],
                "compliance_assessments": self._stats['compliance_assessments'],
                "avg_processing_time_ms": round(self._stats['avg_processing_time_ms'], 2),
                "api_calls_made": self._stats['api_calls_made'],
                "cache_hits": self._stats['cache_hits'],
                "errors": self._stats['errors'],
                "success_rate": (
                    (self._stats['queries_processed'] - self._stats['errors']) / 
                    max(1, self._stats['queries_processed'])
                )
            },
            "cache": {
                "standards_cache_size": len(self._standards_cache),
                "search_cache_size": len(self._search_cache),
                "compliance_cache_size": len(self._compliance_cache)
            },
            "capabilities": {
                "supported_organizations": [org.value for org in self.config.enabled_organizations],
                "supported_categories": [cat.value for cat in StandardCategory],
                "compliance_assessment": True,
                "organizations_queried": list(self._stats['organizations_queried'])
            },
            "timestamp": datetime.now().isoformat()
        }


# =============================================================================
# FACTORY-FUNKTION
# =============================================================================

def create_technical_standards_agent(config: TechnicalStandardsConfig = None) -> TechnicalStandardsAgent:
    """Factory-Funktion für Technical Standards Agent"""
    if config is None:
        config = TechnicalStandardsConfig()
    
    agent = TechnicalStandardsAgent(config)
    return agent


# =============================================================================
# HAUPTFUNKTION FÜR STANDALONE-TESTING
# =============================================================================

async def main():
    """Hauptfunktion für Testing"""
    print("🔍 VERITAS Technical Standards Agent - Test Suite")
    print("=" * 60)
    
    # Agent erstellen
    config = TechnicalStandardsConfig(
        cache_enabled=True,
        min_relevance_threshold=0.4
    )
    agent = create_technical_standards_agent(config)
    
    # Test-Queries
    test_queries = [
        {
            'search_term': 'ISO 9001',
            'organization': StandardsOrganization.ISO,
            'description': 'ISO-Standard Suche: Qualitätsmanagement'
        },
        {
            'search_term': 'VDE 0100',
            'organization': StandardsOrganization.VDE,
            'description': 'VDE-Standard: Elektrotechnik'
        },
        {
            'search_term': 'Sicherheit',
            'category': StandardCategory.SAFETY,
            'description': 'Kategorie-Suche: Sicherheitsnormen'
        },
        {
            'search_term': 'Qualität',
            'organization': None,
            'description': 'Allgemeine Suche: Qualitätsstandards'
        }
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n📋 Test {i}: {query['description']}")
        print(f"   Search: '{query['search_term']}'")
        
        # Request erstellen
        request = StandardsSearchRequest(
            query_id=f"test-{i}",
            query_text=query['description'],
            search_term=query['search_term'],
            organization=query.get('organization'),
            category=query.get('category'),
            include_requirements=True,
            include_related_standards=True,
            max_results=5
        )
        
        # Query ausführen
        start_time = time.time()
        response = await agent.search_standards_async(request)
        execution_time = int((time.time() - start_time) * 1000)
        
        # Ergebnisse anzeigen
        if response.success:
            print(f"   ✅ Success: {response.standards_found} standards in {execution_time}ms")
            print(f"   📊 Relevance: {response.average_relevance_score:.2f}")
            print(f"   🎯 Confidence: {response.confidence_score:.2f}")
            
            # Erste Standard detailliert
            if response.standards:
                standard = response.standards[0]
                print(f"      📄 {standard.identifier.standard_number}: {standard.identifier.full_title}")
                print(f"         Organisation: {standard.identifier.organization.value.upper()}")
                print(f"         Status: {standard.status.value}")
                print(f"         Version: {standard.get_current_version()}")
                print(f"         Kategorie: {', '.join([cat.value for cat in standard.categories])}")
                
                # Requirements
                if standard.requirements:
                    mandatory_reqs = standard.get_mandatory_requirements()
                    print(f"         Anforderungen: {len(standard.requirements)} total, {len(mandatory_reqs)} verpflichtend")
                    
                    for req in standard.requirements[:2]:  # Erste 2
                        print(f"           - {req.section}: {req.title} ({req.compliance_level.value})")
                
                # Related Standards
                if standard.related_standards:
                    print(f"         Verwandte Normen: {len(standard.related_standards)}")
                    for related in standard.related_standards[:3]:
                        print(f"           - {related}")
        else:
            print(f"   ❌ Error: {response.error_message}")
    
    # Compliance Test
    if response.success and response.standards:
        print(f"\n🔍 Compliance Test: {response.standards[0].identifier.standard_number}")
        
        compliance_request = StandardsSearchRequest(
            query_id="compliance-test",
            query_text="Compliance Assessment Test",
            search_term=response.standards[0].identifier.standard_number,
            product_scope="Industrielle Automatisierungssysteme",
            max_results=1
        )
        
        compliance_response = await agent.search_standards_async(compliance_request)
        
        if compliance_response.compliance_assessment:
            assessment = compliance_response.compliance_assessment
            print(f"   📊 Overall Compliance: {assessment.overall_compliance_level:.1%}")
            print(f"   ✅ Compliant: {assessment.compliant_requirements}/{assessment.total_requirements}")
            print(f"   ❌ Non-compliant: {assessment.non_compliant_requirements}")
            print(f"   🔄 Partial: {assessment.partial_compliance}")
            print(f"   🎯 Certification Readiness: {assessment.certification_readiness:.1%}")
            
            if assessment.compliance_gaps:
                print(f"   ⚠️  Gaps: {len(assessment.compliance_gaps)} gefunden")
                for gap in assessment.compliance_gaps[:2]:
                    print(f"      - {gap['gap_description']} (Priority: {gap['priority']})")
            
            if assessment.recommendations:
                print(f"   💡 Recommendations:")
                for rec in assessment.recommendations[:2]:
                    print(f"      - {rec}")
    
    # Agent-Status
    print(f"\n📊 Agent Status:")
    status = agent.get_status()
    print(f"   Queries processed: {status['performance']['queries_processed']}")
    print(f"   Standards found: {status['performance']['standards_found']}")
    print(f"   Compliance assessments: {status['performance']['compliance_assessments']}")
    print(f"   Avg processing time: {status['performance']['avg_processing_time_ms']:.1f}ms")
    print(f"   Success rate: {status['performance']['success_rate']:.2%}")
    print(f"   Organizations: {', '.join(status['capabilities']['organizations_queried'])}")
    print(f"   Requests available: {'Yes' if status['requests_available'] else 'No'}")
    
    print("\n✅ Technical Standards Agent test completed!")


if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run tests
    asyncio.run(main())