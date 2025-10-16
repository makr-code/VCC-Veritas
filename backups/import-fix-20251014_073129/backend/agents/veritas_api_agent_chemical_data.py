"""
VERITAS Chemical Data Agent

Ein spezialisierter Agent für chemische Stoffdaten, Sicherheitsdatenblätter (SDS),
Stoffeigenschaften und regulatorische Informationen.

Hauptfunktionen:
- Sicherheitsdatenblatt-Abruf (SDS/MSDS)
- Chemische und physikalische Eigenschaften
- Toxikologische Daten (LD50, LC50, etc.)
- Umwelteigenschaften (Bioabbaubarkeit, etc.)
- Regulatorische Daten (CLP, REACH, etc.)
- GHS-Klassifikation und Piktogramme
- Expositionsgrenzwerte (MAK, TLV, etc.)
- CAS/EC-Nummern Suche

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

# Mock Chemical Database (wird durch echte APIs ersetzt)
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
    from .veritas_api_agent_atmospheric_flow import (
        EmissionSource, AtmosphericFlowAgent, FlowModelType
    )
    ATMOSPHERIC_INTEGRATION_AVAILABLE = True
except ImportError:
    ATMOSPHERIC_INTEGRATION_AVAILABLE = False
    print("⚠️  Atmospheric Flow Agent Integration nicht verfügbar")


# =============================================================================
# CHEMICAL DATA ENUMS UND KONFIGURATION
# =============================================================================

class ChemicalIdentifierType(Enum):
    """Chemische Identifikatoren"""
    CAS_NUMBER = "cas_number"              # Chemical Abstracts Service
    EC_NUMBER = "ec_number"                # European Community number
    EINECS = "einecs"                      # European Inventory
    ELINCS = "elincs"                      # European List
    IUPAC_NAME = "iupac_name"             # IUPAC Bezeichnung
    COMMON_NAME = "common_name"            # Trivialname
    TRADE_NAME = "trade_name"              # Handelsname
    SMILES = "smiles"                      # Chemical Structure
    INCHI = "inchi"                        # International Chemical Identifier


class GHSHazardClass(Enum):
    """GHS Gefahrenklassen"""
    EXPLOSIVE = "explosive"                 # Explosiv
    FLAMMABLE_GAS = "flammable_gas"        # Entzündbares Gas
    OXIDIZING_GAS = "oxidizing_gas"        # Oxidierendes Gas
    FLAMMABLE_LIQUID = "flammable_liquid"  # Entzündbare Flüssigkeit
    FLAMMABLE_SOLID = "flammable_solid"    # Entzündbarer Feststoff
    OXIDIZING_SOLID = "oxidizing_solid"    # Oxidierender Feststoff
    ORGANIC_PEROXIDE = "organic_peroxide"  # Organisches Peroxid
    ACUTE_TOXICITY = "acute_toxicity"      # Akute Toxizität
    SKIN_CORROSION = "skin_corrosion"      # Ätzwirkung auf die Haut
    EYE_DAMAGE = "eye_damage"              # Schwere Augenschädigung
    RESPIRATORY_SENSITIZATION = "respiratory_sensitization"  # Sensibilisierung der Atemwege
    SKIN_SENSITIZATION = "skin_sensitization"                # Sensibilisierung der Haut
    GERM_CELL_MUTAGENICITY = "germ_cell_mutagenicity"       # Keimzellmutagenität
    CARCINOGENICITY = "carcinogenicity"    # Karzinogenität
    REPRODUCTIVE_TOXICITY = "reproductive_toxicity"          # Reproduktionstoxizität
    SPECIFIC_TARGET_ORGAN_TOXICITY = "specific_target_organ_toxicity"  # Spezifische Zielorgan-Toxizität
    ASPIRATION_HAZARD = "aspiration_hazard"                  # Aspirationsgefahr
    AQUATIC_TOXICITY = "aquatic_toxicity"  # Gewässergefährdung


class PhysicalState(Enum):
    """Aggregatzustände"""
    SOLID = "solid"                        # Feststoff
    LIQUID = "liquid"                      # Flüssigkeit
    GAS = "gas"                           # Gas
    VAPOR = "vapor"                       # Dampf
    AEROSOL = "aerosol"                   # Aerosol
    POWDER = "powder"                     # Pulver
    GRANULES = "granules"                 # Granulat


class RegulationDatabase(Enum):
    """Regulatorische Datenbanken"""
    REACH = "reach"                        # EU REACH
    CLP = "clp"                           # EU CLP
    OSHA = "osha"                         # US OSHA
    NIOSH = "niosh"                       # US NIOSH
    ACGIH = "acgih"                       # American Conference
    DFG = "dfg"                           # Deutsche Forschungsgemeinschaft
    ECHA = "echa"                         # European Chemicals Agency
    EPA = "epa"                           # US Environmental Protection Agency
    WHO = "who"                           # World Health Organization


# =============================================================================
# CHEMICAL DATA STRUKTUREN
# =============================================================================

@dataclass
class ChemicalIdentifier:
    """Chemische Identifikatoren"""
    identifier_type: ChemicalIdentifierType
    value: str
    verified: bool = False
    source: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result['identifier_type'] = self.identifier_type.value
        return result


@dataclass
class PhysicalProperty:
    """Physikalische Eigenschaft"""
    property_name: str                     # z.B. "melting_point", "density"
    value: float
    unit: str
    temperature_c: Optional[float] = None  # Referenztemperatur
    pressure_hpa: Optional[float] = None   # Referenzdruck
    uncertainty: Optional[float] = None    # Messunsicherheit
    method: str = ""                       # Testmethode
    source: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ToxicologicalData:
    """Toxikologische Daten"""
    endpoint: str                          # z.B. "LD50_oral", "LC50_inhalation"
    value: float
    unit: str                             # mg/kg, mg/L, etc.
    species: str = ""                     # Ratte, Maus, etc.
    exposure_route: str = ""              # oral, dermal, inhalation
    exposure_duration: str = ""           # 4h, 24h, etc.
    classification: str = ""              # GHS Kategorie
    source: str = ""
    study_reference: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class EnvironmentalData:
    """Umweltdaten"""
    parameter: str                         # z.B. "biodegradability", "bioconcentration"
    value: Optional[float] = None
    unit: str = ""
    classification: str = ""               # readily biodegradable, etc.
    half_life_days: Optional[float] = None
    log_kow: Optional[float] = None        # Octanol-Wasser-Verteilungskoeffizient
    henry_constant: Optional[float] = None # Henry-Konstante
    source: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ExposureLimit:
    """Arbeitsplatz-Grenzwerte"""
    limit_type: str                        # MAK, TLV, PEL, etc.
    value: float
    unit: str                             # mg/m³, ppm, etc.
    averaging_time: str                   # 8h-TWA, 15min-STEL, etc.
    regulation: RegulationDatabase
    country: str = ""
    year: Optional[int] = None
    notes: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result['regulation'] = self.regulation.value
        return result


@dataclass
class GHSClassification:
    """GHS-Klassifikation"""
    hazard_class: GHSHazardClass
    hazard_category: str                   # 1, 2, 3, etc.
    hazard_statement: str                  # H200, H225, etc.
    hazard_statement_text: str             # "Explosiv, Massenexplosionsgefahr"
    precautionary_statements: List[str] = field(default_factory=list)  # P280, P210, etc.
    signal_word: str = ""                  # "Gefahr", "Achtung"
    pictogram_codes: List[str] = field(default_factory=list)  # GHS01, GHS02, etc.
    
    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result['hazard_class'] = self.hazard_class.value
        return result


@dataclass
class SafetyDataSheet:
    """Sicherheitsdatenblatt (SDS)"""
    sds_id: str
    document_title: str
    version: str = "1.0"
    revision_date: str = ""
    
    # SDS Sections (nach UN GHS)
    section_1_identification: Dict[str, Any] = field(default_factory=dict)
    section_2_hazards: Dict[str, Any] = field(default_factory=dict)
    section_3_composition: Dict[str, Any] = field(default_factory=dict)
    section_4_first_aid: Dict[str, Any] = field(default_factory=dict)
    section_5_fire_fighting: Dict[str, Any] = field(default_factory=dict)
    section_6_accidental_release: Dict[str, Any] = field(default_factory=dict)
    section_7_handling_storage: Dict[str, Any] = field(default_factory=dict)
    section_8_exposure_controls: Dict[str, Any] = field(default_factory=dict)
    section_9_physical_chemical: Dict[str, Any] = field(default_factory=dict)
    section_10_stability_reactivity: Dict[str, Any] = field(default_factory=dict)
    section_11_toxicological: Dict[str, Any] = field(default_factory=dict)
    section_12_ecological: Dict[str, Any] = field(default_factory=dict)
    section_13_disposal: Dict[str, Any] = field(default_factory=dict)
    section_14_transport: Dict[str, Any] = field(default_factory=dict)
    section_15_regulatory: Dict[str, Any] = field(default_factory=dict)
    section_16_other: Dict[str, Any] = field(default_factory=dict)
    
    # Metadaten
    supplier: str = ""
    emergency_phone: str = ""
    language: str = "de"
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ChemicalSubstance:
    """Vollständige chemische Substanz"""
    substance_id: str
    primary_name: str
    
    # Identifikatoren
    identifiers: List[ChemicalIdentifier] = field(default_factory=list)
    
    # Grundlegende Eigenschaften
    molecular_formula: str = ""
    molecular_weight_gmol: Optional[float] = None
    physical_state: Optional[PhysicalState] = None
    appearance: str = ""                   # Aussehen bei Raumtemperatur
    odor: str = ""
    
    # Physikalische Eigenschaften
    physical_properties: List[PhysicalProperty] = field(default_factory=list)
    
    # Sicherheitsdaten
    ghs_classifications: List[GHSClassification] = field(default_factory=list)
    toxicological_data: List[ToxicologicalData] = field(default_factory=list)
    environmental_data: List[EnvironmentalData] = field(default_factory=list)
    exposure_limits: List[ExposureLimit] = field(default_factory=list)
    
    # Sicherheitsdatenblatt
    safety_data_sheet: Optional[SafetyDataSheet] = None
    
    # Zusätzliche Informationen
    synonyms: List[str] = field(default_factory=list)
    uses: List[str] = field(default_factory=list)
    incompatible_materials: List[str] = field(default_factory=list)
    
    # Metadaten
    data_sources: List[str] = field(default_factory=list)
    last_updated: str = ""
    quality_score: float = 0.0             # 0.0-1.0
    
    def get_identifier(self, identifier_type: ChemicalIdentifierType) -> Optional[ChemicalIdentifier]:
        """Spezifischen Identifikator abrufen"""
        for identifier in self.identifiers:
            if identifier.identifier_type == identifier_type:
                return identifier
        return None
    
    def get_cas_number(self) -> Optional[str]:
        """CAS-Nummer abrufen"""
        cas = self.get_identifier(ChemicalIdentifierType.CAS_NUMBER)
        return cas.value if cas else None
    
    def get_property(self, property_name: str) -> Optional[PhysicalProperty]:
        """Spezifische physikalische Eigenschaft abrufen"""
        for prop in self.physical_properties:
            if prop.property_name == property_name:
                return prop
        return None
    
    def get_exposure_limit(self, regulation: RegulationDatabase, limit_type: str = "") -> Optional[ExposureLimit]:
        """Spezifischen Grenzwert abrufen"""
        for limit in self.exposure_limits:
            if limit.regulation == regulation:
                if not limit_type or limit.limit_type == limit_type:
                    return limit
        return None
    
    def is_hazardous(self) -> bool:
        """Prüfen ob Stoff als gefährlich eingestuft ist"""
        return len(self.ghs_classifications) > 0
    
    def get_signal_word(self) -> str:
        """Höchstes GHS-Signalwort ermitteln"""
        signal_words = [ghs.signal_word for ghs in self.ghs_classifications if ghs.signal_word]
        if "Gefahr" in signal_words:
            return "Gefahr"
        elif "Achtung" in signal_words:
            return "Achtung"
        return ""
    
    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result['identifiers'] = [i.to_dict() for i in self.identifiers]
        result['physical_state'] = self.physical_state.value if self.physical_state else None
        result['physical_properties'] = [p.to_dict() for p in self.physical_properties]
        result['ghs_classifications'] = [g.to_dict() for g in self.ghs_classifications]
        result['toxicological_data'] = [t.to_dict() for t in self.toxicological_data]
        result['environmental_data'] = [e.to_dict() for e in self.environmental_data]
        result['exposure_limits'] = [l.to_dict() for l in self.exposure_limits]
        if self.safety_data_sheet:
            result['safety_data_sheet'] = self.safety_data_sheet.to_dict()
        return result


# =============================================================================
# CHEMICAL DATA REQUEST/RESPONSE
# =============================================================================

@dataclass
class ChemicalDataRequest:
    """Request für Chemical Data Agent"""
    query_id: str
    query_text: str
    
    # Suchparameter
    search_term: str                       # Name, CAS, etc.
    identifier_type: Optional[ChemicalIdentifierType] = None
    
    # Gewünschte Daten
    include_physical_properties: bool = True
    include_toxicological_data: bool = True
    include_environmental_data: bool = True
    include_exposure_limits: bool = True
    include_ghs_classification: bool = True
    include_safety_data_sheet: bool = False  # SDS ist groß, optional
    
    # Spezifische Abfragen
    requested_properties: List[str] = field(default_factory=list)  # ["density", "melting_point"]
    requested_regulations: List[RegulationDatabase] = field(default_factory=list)
    
    # Filter
    max_results: int = 10
    min_quality_score: float = 0.5
    preferred_language: str = "de"
    
    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        if self.identifier_type:
            result['identifier_type'] = self.identifier_type.value
        result['requested_regulations'] = [r.value for r in self.requested_regulations]
        return result


@dataclass
class ChemicalDataResponse:
    """Response für Chemical Data Agent"""
    query_id: str
    success: bool
    
    # Ergebnisse
    substances: List[ChemicalSubstance] = field(default_factory=list)
    
    # Suchinformationen
    search_term_used: str = ""
    substances_found: int = 0
    exact_matches: int = 0
    
    # Datenqualität
    average_quality_score: float = 0.0
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
    
    def get_best_match(self) -> Optional[ChemicalSubstance]:
        """Beste Übereinstimmung abrufen"""
        if not self.substances:
            return None
        return max(self.substances, key=lambda s: s.quality_score)
    
    def get_substances_by_hazard(self, hazard_class: GHSHazardClass) -> List[ChemicalSubstance]:
        """Stoffe nach Gefahrenklasse filtern"""
        return [
            substance for substance in self.substances
            if any(ghs.hazard_class == hazard_class for ghs in substance.ghs_classifications)
        ]
    
    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result['substances'] = [s.to_dict() for s in self.substances]
        return result


# =============================================================================
# CHEMICAL DATA AGENT KONFIGURATION
# =============================================================================

@dataclass
class ChemicalDataConfig:
    """Chemical Data Agent Konfiguration"""
    
    # Datenquellen
    enabled_databases: List[str] = field(default_factory=lambda: [
        "pubchem", "chemspider", "echa_chem", "gestis", "nist_webbook"
    ])
    
    # API-Konfiguration  
    pubchem_base_url: str = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"
    chemspider_api_key: str = ""
    echa_base_url: str = "https://echa.europa.eu/api"
    gestis_base_url: str = "https://gestis-database.dguv.de/api"
    
    # Cache-Einstellungen
    cache_enabled: bool = True
    cache_ttl_seconds: int = 7200          # 2 Stunden
    max_cache_size: int = 1000
    
    # Performance
    max_concurrent_requests: int = 5
    request_timeout_seconds: int = 30
    max_retries: int = 3
    rate_limit_delay: float = 0.2
    
    # Datenqualität
    min_quality_threshold: float = 0.3
    require_cas_number: bool = False
    verify_molecular_formula: bool = True
    
    # Sprache
    default_language: str = "de"
    supported_languages: List[str] = field(default_factory=lambda: ["de", "en", "fr"])
    
    # SDS-Konfiguration
    sds_providers: List[str] = field(default_factory=lambda: [
        "sigma_aldrich", "merck", "fisher_scientific", "vwr"
    ])
    sds_max_age_days: int = 365           # Max. Alter eines SDS
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# =============================================================================
# CHEMICAL DATA AGENT HAUPTKLASSE
# =============================================================================

class ChemicalDataAgent:
    """
    VERITAS Chemical Data Agent
    
    Spezialisierter Agent für chemische Stoffdaten und Sicherheitsinformationen:
    - Sicherheitsdatenblätter (SDS/MSDS)
    - Physikalische und chemische Eigenschaften
    - Toxikologische und Umweltdaten
    - GHS-Klassifikation und Piktogramme
    - Arbeitsplatz-Grenzwerte (MAK, TLV, etc.)
    - Regulatorische Informationen
    """
    
    def __init__(self, config: ChemicalDataConfig = None):
        self.config = config or ChemicalDataConfig()
        self.logger = logging.getLogger(f"{__name__}.ChemicalDataAgent")
        
        # Caches
        self._substance_cache: Dict[str, ChemicalSubstance] = {}
        self._search_cache: Dict[str, ChemicalDataResponse] = {}
        self._sds_cache: Dict[str, SafetyDataSheet] = {}
        
        # Performance tracking
        self._stats = {
            'queries_processed': 0,
            'substances_found': 0,
            'api_calls_made': 0,
            'cache_hits': 0,
            'errors': 0,
            'avg_processing_time_ms': 0,
            'total_processing_time_ms': 0,
            'data_sources_used': set()
        }
        
        self.logger.info(f"✅ Chemical Data Agent initialized with {len(self.config.enabled_databases)} databases")
    
    # =========================================================================
    # HAUPT-QUERY-METHODEN
    # =========================================================================
    
    async def query_chemical_data_async(self, request: ChemicalDataRequest) -> ChemicalDataResponse:
        """Asynchrone chemische Datenabfrage (Haupt-Methode)"""
        start_time = time.time()
        
        try:
            self.logger.info(f"🧪 Processing chemical data query: {request.query_text}")
            
            # Cache-Check
            cache_key = self._generate_cache_key(request)
            if self.config.cache_enabled and cache_key in self._search_cache:
                self.logger.debug("📋 Using cached chemical data result")
                self._stats['cache_hits'] += 1
                cached_response = self._search_cache[cache_key]
                cached_response.processing_time_ms = int((time.time() - start_time) * 1000)
                return cached_response
            
            # Chemische Substanzen suchen
            substances = await self._search_chemical_substances(request)
            
            # Response erstellen
            response = ChemicalDataResponse(
                query_id=request.query_id,
                success=len(substances) > 0,
                substances=substances,
                search_term_used=request.search_term,
                substances_found=len(substances),
                exact_matches=len([s for s in substances if s.quality_score > 0.9])
            )
            
            # Statistiken berechnen
            if substances:
                response.average_quality_score = sum(s.quality_score for s in substances) / len(substances)
                response.confidence_score = min(0.95, response.average_quality_score)
                
                # Alle verwendeten Datenquellen sammeln
                all_sources = set()
                for substance in substances:
                    all_sources.update(substance.data_sources)
                response.data_sources_used = list(all_sources)
            
            # Processing time
            processing_time = int((time.time() - start_time) * 1000)
            response.processing_time_ms = processing_time
            
            # Stats update
            self._update_stats(processing_time, len(substances))
            
            # Cache-Speicherung
            if self.config.cache_enabled and response.success:
                self._search_cache[cache_key] = response
                self._cleanup_cache()
            
            self.logger.info(f"✅ Chemical data query completed: {len(substances)} substances in {processing_time}ms")
            return response
            
        except Exception as e:
            error_msg = f"Chemical data query error: {str(e)}"
            self.logger.error(error_msg)
            self._stats['errors'] += 1
            
            return ChemicalDataResponse(
                query_id=request.query_id,
                success=False,
                error_message=error_msg,
                processing_time_ms=int((time.time() - start_time) * 1000)
            )
    
    def query_chemical_data(self, request: ChemicalDataRequest) -> ChemicalDataResponse:
        """Synchrone chemische Datenabfrage"""
        return asyncio.run(self.query_chemical_data_async(request))
    
    # =========================================================================
    # CHEMISCHE SUBSTANZ-SUCHE
    # =========================================================================
    
    async def _search_chemical_substances(self, request: ChemicalDataRequest) -> List[ChemicalSubstance]:
        """Suche nach chemischen Substanzen"""
        substances = []
        
        try:
            # 1. Exakte Suche nach Identifikatoren
            if request.identifier_type == ChemicalIdentifierType.CAS_NUMBER:
                substance = await self._search_by_cas(request.search_term)
                if substance:
                    substances.append(substance)
            
            # 2. Name-basierte Suche
            if not substances or len(substances) < request.max_results:
                name_substances = await self._search_by_name(request.search_term, request.max_results)
                substances.extend(name_substances)
            
            # 3. Strukturbasierte Suche (SMILES, InChI)
            if request.identifier_type in [ChemicalIdentifierType.SMILES, ChemicalIdentifierType.INCHI]:
                structure_substance = await self._search_by_structure(request.search_term, request.identifier_type)
                if structure_substance:
                    substances.append(structure_substance)
            
            # 4. Zusätzliche Daten laden
            for substance in substances:
                if request.include_safety_data_sheet:
                    substance.safety_data_sheet = await self._get_safety_data_sheet(substance)
                
                if request.requested_properties:
                    await self._enrich_properties(substance, request.requested_properties)
                
                if request.requested_regulations:
                    await self._enrich_regulatory_data(substance, request.requested_regulations)
            
            # 5. Qualitätsfilterung
            substances = [s for s in substances if s.quality_score >= request.min_quality_score]
            
            # 6. Nach Qualität sortieren
            substances.sort(key=lambda s: s.quality_score, reverse=True)
            
            return substances[:request.max_results]
            
        except Exception as e:
            self.logger.error(f"Chemical substance search error: {e}")
            return []
    
    async def _search_by_cas(self, cas_number: str) -> Optional[ChemicalSubstance]:
        """Suche nach CAS-Nummer"""
        # Für Demo: Mock-Daten für bekannte CAS-Nummern
        mock_cas_data = {
            "7732-18-5": {  # Wasser
                "name": "Wasser",
                "formula": "H2O",
                "mw": 18.015,
                "state": PhysicalState.LIQUID
            },
            "64-19-7": {   # Essigsäure
                "name": "Essigsäure",
                "formula": "C2H4O2",
                "mw": 60.052,
                "state": PhysicalState.LIQUID
            },
            "67-56-1": {   # Methanol
                "name": "Methanol",
                "formula": "CH4O",
                "mw": 32.042,
                "state": PhysicalState.LIQUID
            },
            "7664-93-9": { # Schwefelsäure
                "name": "Schwefelsäure",
                "formula": "H2SO4",
                "mw": 98.079,
                "state": PhysicalState.LIQUID
            },
            "1344-28-1": { # Aluminiumoxid
                "name": "Aluminiumoxid",
                "formula": "Al2O3",
                "mw": 101.961,
                "state": PhysicalState.SOLID
            },
            "71-43-2": {   # Benzol
                "name": "Benzol",
                "formula": "C6H6",
                "mw": 78.114,
                "state": PhysicalState.LIQUID
            },
            "108-88-3": {  # Toluol
                "name": "Toluol", 
                "formula": "C7H8",
                "mw": 92.140,
                "state": PhysicalState.LIQUID
            },
            "67-64-1": {   # Aceton
                "name": "Aceton",
                "formula": "C3H6O",
                "mw": 58.080,
                "state": PhysicalState.LIQUID
            },
            "64-17-5": {   # Ethanol
                "name": "Ethanol",
                "formula": "C2H6O",
                "mw": 46.069,
                "state": PhysicalState.LIQUID
            }
        }
        
        if cas_number in mock_cas_data:
            data = mock_cas_data[cas_number]
            
            substance = ChemicalSubstance(
                substance_id=f"cas_{cas_number.replace('-', '_')}",
                primary_name=data["name"],
                molecular_formula=data["formula"],
                molecular_weight_gmol=data["mw"],
                physical_state=data["state"],
                quality_score=0.95,
                last_updated=datetime.now().isoformat(),
                data_sources=["mock_database"]
            )
            
            # CAS-Nummer hinzufügen
            substance.identifiers.append(
                ChemicalIdentifier(
                    identifier_type=ChemicalIdentifierType.CAS_NUMBER,
                    value=cas_number,
                    verified=True,
                    source="mock_database"
                )
            )
            
            # Mock physikalische Eigenschaften
            await self._add_mock_properties(substance)
            
            # Mock GHS-Klassifikation
            await self._add_mock_ghs_classification(substance)
            
            # Mock Grenzwerte
            await self._add_mock_exposure_limits(substance)
            
            return substance
        
        return None
    
    async def _search_by_name(self, name: str, max_results: int) -> List[ChemicalSubstance]:
        """Suche nach Namen"""
        substances = []
        
        # Mock-Daten für häufige Chemikalien
        mock_name_data = {
            "benzol": {"cas": "71-43-2", "formula": "C6H6", "hazardous": True},
            "toluol": {"cas": "108-88-3", "formula": "C7H8", "hazardous": True},
            "aceton": {"cas": "67-64-1", "formula": "C3H6O", "hazardous": False},
            "ethanol": {"cas": "64-17-5", "formula": "C2H6O", "hazardous": False},
            "schwefelsäure": {"cas": "7664-93-9", "formula": "H2SO4", "hazardous": True},
            "salzsäure": {"cas": "7647-01-0", "formula": "HCl", "hazardous": True},
            "natriumhydroxid": {"cas": "1310-73-2", "formula": "NaOH", "hazardous": True},
            "ammoniak": {"cas": "7664-41-7", "formula": "NH3", "hazardous": True},
            "methanol": {"cas": "67-56-1", "formula": "CH4O", "hazardous": True},
            "wasser": {"cas": "7732-18-5", "formula": "H2O", "hazardous": False}
        }
        
        name_lower = name.lower()
        matches = []
        
        # Suche nach exakten und teilweisen Übereinstimmungen
        for substance_name, data in mock_name_data.items():
            if name_lower in substance_name or substance_name in name_lower:
                quality = 0.9 if name_lower == substance_name else 0.7
                matches.append((substance_name, data, quality))
        
        # Nach Qualität sortieren
        matches.sort(key=lambda x: x[2], reverse=True)
        
        for substance_name, data, quality in matches[:max_results]:
            # Versuche CAS-basierte Suche
            substance = await self._search_by_cas(data["cas"])
            if substance:
                substance.quality_score = quality
                substance.synonyms.append(substance_name)
                substances.append(substance)
        
        return substances
    
    async def _search_by_structure(self, structure: str, identifier_type: ChemicalIdentifierType) -> Optional[ChemicalSubstance]:
        """Suche nach Strukturidentifikatoren"""
        # Mock-Implementierung für Demo
        self.logger.debug(f"Structure search not implemented in mock mode: {structure}")
        return None
    
    # =========================================================================
    # DATEN-ANREICHERUNG
    # =========================================================================
    
    async def _add_mock_properties(self, substance: ChemicalSubstance):
        """Mock physikalische Eigenschaften hinzufügen"""
        cas = substance.get_cas_number()
        
        # Beispiel-Properties basierend auf bekannten Stoffen
        property_data = {
            "7732-18-5": {  # Wasser
                "density": (1.0, "g/cm³", 20.0),
                "melting_point": (0.0, "°C", 1013.25),
                "boiling_point": (100.0, "°C", 1013.25),
                "vapor_pressure": (2337.0, "Pa", 20.0)
            },
            "67-56-1": {   # Methanol
                "density": (0.7918, "g/cm³", 20.0),
                "melting_point": (-97.6, "°C", 1013.25),
                "boiling_point": (64.7, "°C", 1013.25),
                "vapor_pressure": (16940.0, "Pa", 25.0)
            },
            "7664-93-9": { # Schwefelsäure
                "density": (1.84, "g/cm³", 20.0),
                "melting_point": (10.31, "°C", 1013.25),
                "boiling_point": (337.0, "°C", 1013.25),
                "vapor_pressure": (0.13, "Pa", 25.0)
            },
            "71-43-2": {   # Benzol
                "density": (0.8765, "g/cm³", 20.0),
                "melting_point": (5.5, "°C", 1013.25),
                "boiling_point": (80.1, "°C", 1013.25),
                "vapor_pressure": (12700.0, "Pa", 25.0)
            }
        }
        
        if cas in property_data:
            for prop_name, (value, unit, temp) in property_data[cas].items():
                substance.physical_properties.append(
                    PhysicalProperty(
                        property_name=prop_name,
                        value=value,
                        unit=unit,
                        temperature_c=temp,
                        source="mock_database"
                    )
                )
    
    async def _add_mock_ghs_classification(self, substance: ChemicalSubstance):
        """Mock GHS-Klassifikation hinzufügen"""
        cas = substance.get_cas_number()
        
        # Beispiel GHS-Klassifikationen
        ghs_data = {
            "67-56-1": [  # Methanol
                (GHSHazardClass.FLAMMABLE_LIQUID, "2", "H225", "Flüssigkeit und Dampf leicht entzündbar"),
                (GHSHazardClass.ACUTE_TOXICITY, "3", "H301", "Giftig bei Verschlucken"),
                (GHSHazardClass.ACUTE_TOXICITY, "3", "H311", "Giftig bei Hautkontakt"),
                (GHSHazardClass.ACUTE_TOXICITY, "3", "H331", "Giftig bei Einatmen")
            ],
            "7664-93-9": [ # Schwefelsäure
                (GHSHazardClass.SKIN_CORROSION, "1A", "H314", "Verursacht schwere Verätzungen der Haut und schwere Augenschäden")
            ],
            "71-43-2": [  # Benzol
                (GHSHazardClass.FLAMMABLE_LIQUID, "2", "H225", "Flüssigkeit und Dampf leicht entzündbar"),
                (GHSHazardClass.CARCINOGENICITY, "1A", "H350", "Kann Krebs erzeugen"),
                (GHSHazardClass.GERM_CELL_MUTAGENICITY, "1B", "H340", "Kann genetische Defekte verursachen"),
                (GHSHazardClass.SPECIFIC_TARGET_ORGAN_TOXICITY, "1", "H372", "Schädigt Organe bei längerer oder wiederholter Exposition")
            ]
        }
        
        if cas in ghs_data:
            for hazard_class, category, h_code, h_text in ghs_data[cas]:
                signal_word = "Gefahr" if category in ["1", "1A", "1B", "2"] else "Achtung"
                
                substance.ghs_classifications.append(
                    GHSClassification(
                        hazard_class=hazard_class,
                        hazard_category=category,
                        hazard_statement=h_code,
                        hazard_statement_text=h_text,
                        signal_word=signal_word,
                        pictogram_codes=[f"GHS0{hash(hazard_class.value) % 9 + 1}"]
                    )
                )
    
    async def _add_mock_exposure_limits(self, substance: ChemicalSubstance):
        """Mock Arbeitsplatz-Grenzwerte hinzufügen"""
        cas = substance.get_cas_number()
        
        # Beispiel-Grenzwerte
        limit_data = {
            "67-56-1": [  # Methanol
                ("MAK", 200.0, "ml/m³", "8h-TWA", RegulationDatabase.DFG, "Deutschland"),
                ("TLV-TWA", 200.0, "ppm", "8h-TWA", RegulationDatabase.ACGIH, "USA")
            ],
            "7664-93-9": [ # Schwefelsäure
                ("MAK", 0.1, "mg/m³", "8h-TWA", RegulationDatabase.DFG, "Deutschland"),
                ("TLV-TWA", 0.2, "mg/m³", "8h-TWA", RegulationDatabase.ACGIH, "USA")
            ]
        }
        
        if cas in limit_data:
            for limit_type, value, unit, averaging_time, regulation, country in limit_data[cas]:
                substance.exposure_limits.append(
                    ExposureLimit(
                        limit_type=limit_type,
                        value=value,
                        unit=unit,
                        averaging_time=averaging_time,
                        regulation=regulation,
                        country=country,
                        year=2024
                    )
                )
    
    async def _enrich_properties(self, substance: ChemicalSubstance, requested_properties: List[str]):
        """Zusätzliche Eigenschaften anreichern"""
        for prop_name in requested_properties:
            if not substance.get_property(prop_name):
                # Mock-Eigenschaft hinzufügen falls nicht vorhanden
                if prop_name == "flash_point" and substance.physical_state == PhysicalState.LIQUID:
                    substance.physical_properties.append(
                        PhysicalProperty(
                            property_name=prop_name,
                            value=25.0,  # Mock Flash Point
                            unit="°C",
                            method="closed cup",
                            source="estimated"
                        )
                    )
    
    async def _enrich_regulatory_data(self, substance: ChemicalSubstance, regulations: List[RegulationDatabase]):
        """Regulatorische Daten anreichern"""
        for regulation in regulations:
            if not substance.get_exposure_limit(regulation):
                # Mock-Grenzwert hinzufügen
                substance.exposure_limits.append(
                    ExposureLimit(
                        limit_type="OEL",
                        value=10.0,  # Mock Wert
                        unit="mg/m³",
                        averaging_time="8h-TWA",
                        regulation=regulation,
                        year=2024,
                        notes="Mock regulatory data"
                    )
                )
    
    async def _get_safety_data_sheet(self, substance: ChemicalSubstance) -> Optional[SafetyDataSheet]:
        """Sicherheitsdatenblatt abrufen"""
        cas = substance.get_cas_number()
        if not cas:
            return None
        
        # Mock SDS für Demo
        sds = SafetyDataSheet(
            sds_id=f"sds_{cas.replace('-', '_')}",
            document_title=f"Sicherheitsdatenblatt - {substance.primary_name}",
            version="1.0",
            revision_date=datetime.now().strftime("%Y-%m-%d"),
            supplier="Mock Chemical Company",
            emergency_phone="+49-180-2273-456",
            language="de"
        )
        
        # SDS Sektionen mit Mock-Daten
        sds.section_1_identification = {
            "product_name": substance.primary_name,
            "cas_number": cas,
            "supplier": "Mock Chemical Company",
            "emergency_phone": "+49-180-2273-456"
        }
        
        sds.section_2_hazards = {
            "ghs_classification": [ghs.hazard_statement for ghs in substance.ghs_classifications],
            "signal_word": substance.get_signal_word(),
            "hazard_statements": [ghs.hazard_statement_text for ghs in substance.ghs_classifications]
        }
        
        sds.section_9_physical_chemical = {
            prop.property_name: f"{prop.value} {prop.unit}"
            for prop in substance.physical_properties
        }
        
        return sds
    
    # =========================================================================
    # UTILITY-METHODEN
    # =========================================================================
    
    def _generate_cache_key(self, request: ChemicalDataRequest) -> str:
        """Cache-Schlüssel generieren"""
        key_parts = [
            request.search_term,
            request.identifier_type.value if request.identifier_type else "",
            str(request.max_results),
            str(request.include_safety_data_sheet)
        ]
        key_string = "|".join(key_parts)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def _update_stats(self, processing_time: int, substances_found: int):
        """Statistiken aktualisieren"""
        self._stats['queries_processed'] += 1
        self._stats['substances_found'] += substances_found
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
            "agent_type": "chemical_data",
            "version": "1.0.0",
            "status": "active",
            "requests_available": REQUESTS_AVAILABLE,
            "config": self.config.to_dict(),
            "performance": {
                "queries_processed": self._stats['queries_processed'],
                "substances_found": self._stats['substances_found'],
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
                "substance_cache_size": len(self._substance_cache),
                "search_cache_size": len(self._search_cache),
                "sds_cache_size": len(self._sds_cache)
            },
            "capabilities": {
                "supported_databases": self.config.enabled_databases,
                "supported_identifiers": [id_type.value for id_type in ChemicalIdentifierType],
                "supported_regulations": [reg.value for reg in RegulationDatabase],
                "data_sources_used": list(self._stats['data_sources_used'])
            },
            "timestamp": datetime.now().isoformat()
        }


# =============================================================================
# FACTORY-FUNKTION
# =============================================================================

def create_chemical_data_agent(config: ChemicalDataConfig = None) -> ChemicalDataAgent:
    """Factory-Funktion für Chemical Data Agent"""
    if config is None:
        config = ChemicalDataConfig()
    
    agent = ChemicalDataAgent(config)
    return agent


# =============================================================================
# HAUPTFUNKTION FÜR STANDALONE-TESTING
# =============================================================================

async def main():
    """Hauptfunktion für Testing"""
    print("🧪 VERITAS Chemical Data Agent - Test Suite")
    print("=" * 60)
    
    # Agent erstellen
    config = ChemicalDataConfig(
        cache_enabled=True,
        min_quality_threshold=0.5
    )
    agent = create_chemical_data_agent(config)
    
    # Test-Queries
    test_queries = [
        {
            'search_term': '67-56-1',
            'identifier_type': ChemicalIdentifierType.CAS_NUMBER,
            'description': 'CAS-Suche: Methanol'
        },
        {
            'search_term': 'schwefelsäure',
            'identifier_type': None,
            'description': 'Name-Suche: Schwefelsäure'
        },
        {
            'search_term': 'benzol',
            'identifier_type': None,
            'description': 'Name-Suche: Benzol (gefährlich)'
        },
        {
            'search_term': '7732-18-5',
            'identifier_type': ChemicalIdentifierType.CAS_NUMBER,
            'description': 'CAS-Suche: Wasser'
        }
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n📋 Test {i}: {query['description']}")
        print(f"   Search: '{query['search_term']}'")
        
        # Request erstellen
        request = ChemicalDataRequest(
            query_id=f"test-{i}",
            query_text=query['description'],
            search_term=query['search_term'],
            identifier_type=query['identifier_type'],
            include_physical_properties=True,
            include_ghs_classification=True,
            include_exposure_limits=True,
            include_safety_data_sheet=(i == 1),  # Nur für ersten Test SDS
            max_results=3
        )
        
        # Query ausführen
        start_time = time.time()
        response = await agent.query_chemical_data_async(request)
        execution_time = int((time.time() - start_time) * 1000)
        
        # Ergebnisse anzeigen
        if response.success:
            print(f"   ✅ Success: {response.substances_found} substances in {execution_time}ms")
            print(f"   📊 Quality: {response.average_quality_score:.2f}")
            print(f"   🎯 Confidence: {response.confidence_score:.2f}")
            
            # Erste Substanz detailliert
            if response.substances:
                substance = response.substances[0]
                print(f"      📄 {substance.primary_name}")
                
                cas = substance.get_cas_number()
                if cas:
                    print(f"         CAS: {cas}")
                
                if substance.molecular_formula:
                    print(f"         Formel: {substance.molecular_formula}")
                    if substance.molecular_weight_gmol:
                        print(f"         MW: {substance.molecular_weight_gmol:.3f} g/mol")
                
                if substance.physical_state:
                    print(f"         Zustand: {substance.physical_state.value}")
                
                # Physikalische Eigenschaften
                if substance.physical_properties:
                    props = substance.physical_properties[:3]  # Erste 3
                    print(f"         Eigenschaften: {len(substance.physical_properties)} gefunden")
                    for prop in props:
                        print(f"           - {prop.property_name}: {prop.value} {prop.unit}")
                
                # GHS-Klassifikation
                if substance.ghs_classifications:
                    print(f"         GHS: {len(substance.ghs_classifications)} Gefahrenklassen")
                    signal_word = substance.get_signal_word()
                    if signal_word:
                        print(f"           Signalwort: {signal_word}")
                    
                    for ghs in substance.ghs_classifications[:2]:  # Erste 2
                        print(f"           - {ghs.hazard_statement}: {ghs.hazard_statement_text}")
                
                # Grenzwerte
                if substance.exposure_limits:
                    print(f"         Grenzwerte: {len(substance.exposure_limits)} gefunden")
                    for limit in substance.exposure_limits[:2]:  # Erste 2
                        print(f"           - {limit.limit_type}: {limit.value} {limit.unit} ({limit.regulation.value})")
                
                # SDS
                if substance.safety_data_sheet:
                    sds = substance.safety_data_sheet
                    print(f"         📋 SDS: {sds.document_title}")
                    print(f"           Version: {sds.version}, Überarbeitet: {sds.revision_date}")
                    print(f"           Anbieter: {sds.supplier}")
        else:
            print(f"   ❌ Error: {response.error_message}")
    
    # Integration Test: Chemical + Atmospheric Flow
    if ATMOSPHERIC_INTEGRATION_AVAILABLE:
        print(f"\n🔗 Integration Test: Chemical Data → Atmospheric Flow")
        
        # Benzol-Daten für Emissionsberechnung
        benzol_request = ChemicalDataRequest(
            query_id="integration-benzol",
            query_text="Benzol für Emissionsberechnung",
            search_term="71-43-2",  # Benzol CAS
            identifier_type=ChemicalIdentifierType.CAS_NUMBER,
            include_physical_properties=True
        )
        
        benzol_response = await agent.query_chemical_data_async(benzol_request)
        
        if benzol_response.success and benzol_response.substances:
            benzol = benzol_response.substances[0]
            print(f"   📄 Gefunden: {benzol.primary_name}")
            print(f"   ⚠️  Gefährlich: {'Ja' if benzol.is_hazardous() else 'Nein'}")
            
            # Vapor pressure für Verdampfungsrate
            vapor_pressure = benzol.get_property("vapor_pressure")
            if vapor_pressure:
                print(f"   💨 Dampfdruck: {vapor_pressure.value} {vapor_pressure.unit}")
                print(f"      → Hohe Verdampfungsrate erwartet")
            
            # GHS-Klassifikation für Risikobewertung
            if benzol.ghs_classifications:
                print(f"   ⚠️  GHS-Gefahren: {len(benzol.ghs_classifications)} Klassen")
                for ghs in benzol.ghs_classifications[:2]:
                    print(f"      - {ghs.hazard_statement_text}")
    
    # Agent-Status
    print(f"\n📊 Agent Status:")
    status = agent.get_status()
    print(f"   Queries processed: {status['performance']['queries_processed']}")
    print(f"   Substances found: {status['performance']['substances_found']}")
    print(f"   Avg processing time: {status['performance']['avg_processing_time_ms']:.1f}ms")
    print(f"   Success rate: {status['performance']['success_rate']:.2%}")
    print(f"   Supported databases: {', '.join(status['capabilities']['supported_databases'])}")
    print(f"   Requests available: {'Yes' if status['requests_available'] else 'No'}")
    
    print("\n✅ Chemical Data Agent test completed!")


if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run tests
    asyncio.run(main())