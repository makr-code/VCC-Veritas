#!/usr/bin/env python3
"""
VERITAS Construction & Urban Planning Workers
Spezialisierte Worker für Bau- und Stadtplanungsanfragen
"""
import logging
import asyncio
import aiohttp
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from covina_base import BaseWorker, ExternalAPIWorker

class BuildingPermitWorker(ExternalAPIWorker):
    """Worker für Baugenehmigungen und Baurecht"""
    
    def __init__(self):
        from covina_core import WorkerType
        super().__init__(WorkerType.BUILDING_PERMIT, "https://api.bauamt.de/", cache_ttl=3600)  # 1 Stunde Cache
        self.permit_databases = {
            "municipal": "https://api.municipality.de/building_permits/",
            "state": "https://api.state.de/construction/",
            "federal": "https://api.bund.de/baurecht/"
        }
    
    def _extract_location(self, query: str) -> Dict[str, Any]:
        """Extrahiert Standortinformationen aus der Anfrage"""
        location = {
            "name": "München",
            "state": "Bayern", 
            "country": "Deutschland",
            "coordinates": {"lat": 48.1351, "lon": 11.5820}
        }
        
        # Einfache Standorterkennung
        if "berlin" in query.lower():
            location.update({"name": "Berlin", "state": "Berlin", "coordinates": {"lat": 52.5200, "lon": 13.4050}})
        elif "hamburg" in query.lower():
            location.update({"name": "Hamburg", "state": "Hamburg", "coordinates": {"lat": 53.5511, "lon": 9.9937}})
        elif "münchen" in query.lower() or "munich" in query.lower():
            location.update({"name": "München", "state": "Bayern", "coordinates": {"lat": 48.1351, "lon": 11.5820}})
        
        return location
    
    async def _process_internal(self, metadata, user_profile: Dict = None) -> Dict[str, Any]:
        """Analysiert Baugenehmigungen und Bauvorhaben"""
        
        # Extrahiere Bauvorhaben-Details
        building_project = self._extract_building_details(metadata.normalized_query)
        location = self._extract_location(metadata.normalized_query)
        
        if not location:
            return {
                "building_permits": [],
                "zoning_info": {},
                "summary": "Keine Standortangabe für Baurechtsanalyse gefunden",
                "confidence_score": 0.2
            }
        
        try:
            # Hole Baugenehmigungen in der Nähe
            nearby_permits = await self._get_nearby_permits(location, building_project)
            
            # Bestimme Zonierung und Baurecht
            zoning_info = await self._get_zoning_information(location)
            
            # Prüfe Baubeschränkungen
            restrictions = await self._check_building_restrictions(location, building_project)
            
            # Bewerte Genehmigungswahrscheinlichkeit
            approval_assessment = self._assess_approval_probability(building_project, zoning_info, restrictions)
            
            return {
                "building_permits": nearby_permits,
                "zoning_info": zoning_info,
                "restrictions": restrictions,
                "approval_assessment": approval_assessment,
                "summary": f"Baurechtsanalyse für {building_project.get('type', 'Bauvorhaben')} in {location.get('name', 'unbekanntem Gebiet')}",
                "confidence_score": 0.85,
                "sources": [{"type": "building_regulations", "location": location}]
            }
            
        except Exception as e:
            logging.error(f"❌ BuildingPermitWorker Error: {e}")
            return {
                "building_permits": [],
                "zoning_info": {},
                "summary": f"Baurechtsanalyse fehlgeschlagen: {str(e)}",
                "confidence_score": 0.0,
                "error": str(e)
            }
    
    def _extract_building_details(self, query: str) -> Dict[str, Any]:
        """Extrahiert Bauvorhaben-Details aus Query"""
        
        project = {
            "type": "unbekannt",
            "scale": "klein",
            "purpose": "residential",
            "height_stories": 1,
            "special_requirements": []
        }
        
        # Gebäudetyp identifizieren
        building_types = {
            "einfamilienhaus": {"type": "Einfamilienhaus", "scale": "klein", "purpose": "residential"},
            "mehrfamilienhaus": {"type": "Mehrfamilienhaus", "scale": "mittel", "purpose": "residential"},
            "gewerbe": {"type": "Gewerbebau", "scale": "mittel", "purpose": "commercial"},
            "industrie": {"type": "Industriebau", "scale": "groß", "purpose": "industrial"},
            "garage": {"type": "Garage", "scale": "sehr_klein", "purpose": "accessory"},
            "anbau": {"type": "Anbau", "scale": "klein", "purpose": "extension"},
            "dachausbau": {"type": "Dachausbau", "scale": "klein", "purpose": "modification"}
        }
        
        for keyword, details in building_types.items():
            if keyword in query.lower():
                project.update(details)
                break
        
        # Stockwerke
        if "stockwerk" in query or "etage" in query:
            import re
            numbers = re.findall(r'\d+', query)
            if numbers:
                project["height_stories"] = int(numbers[0])
        
        # Besondere Anforderungen
        if "denkmal" in query:
            project["special_requirements"].append("heritage_protection")
        if "energie" in query or "sanierung" in query:
            project["special_requirements"].append("energy_efficiency")
        if "barriere" in query:
            project["special_requirements"].append("accessibility")
        
        return project
    
    async def _get_nearby_permits(self, location: Dict, project: Dict) -> List[Dict]:
        """Holt Baugenehmigungen in der Nähe"""
        await asyncio.sleep(0.5)  # Simuliere API-Call
        
        # Mock-Baugenehmigungen
        permits = [
            {
                "permit_id": "BG-2024-1234",
                "project_type": "Einfamilienhaus",
                "address": "Musterstraße 45",
                "status": "genehmigt",
                "approval_date": "2024-03-15",
                "height_meters": 9.5,
                "building_area_sqm": 120,
                "distance_meters": 250,
                "special_conditions": ["Dachneigung mind. 35°", "Abstand Grenze 3m"]
            },
            {
                "permit_id": "BG-2024-0987",
                "project_type": "Anbau",
                "address": "Beispielweg 12",
                "status": "in_bearbeitung",
                "application_date": "2024-07-20",
                "building_area_sqm": 40,
                "distance_meters": 180,
                "special_conditions": ["Nachbarschaftsanhörung erforderlich"]
            }
        ]
        
        return permits
    
    async def _get_zoning_information(self, location: Dict) -> Dict[str, Any]:
        """Bestimmt Zonierung und Baugebietstyp"""
        await asyncio.sleep(0.3)
        
        # Mock-Zonierungsinformationen
        zoning = {
            "zone_type": "Mischgebiet (MI)",
            "building_coefficient": 0.4,
            "floor_area_ratio": 1.2,
            "max_building_height": 12.0,
            "min_green_space_percent": 30,
            "permitted_uses": [
                "Wohnen",
                "Nicht störendes Gewerbe",
                "Büros",
                "Einzelhandel (begrenzt)"
            ],
            "building_line_regulations": {
                "front_setback_min": 3.0,
                "side_setback_min": 3.0,
                "rear_setback_min": 3.0
            },
            "special_regulations": [
                "Stellplätze nach BayBO",
                "Regenwasser-Versickerung erforderlich",
                "Energieeffizienz nach GEG"
            ]
        }
        
        return zoning
    
    async def _check_building_restrictions(self, location: Dict, project: Dict) -> List[Dict]:
        """Prüft Baubeschränkungen und -auflagen"""
        await asyncio.sleep(0.2)
        
        restrictions = []
        
        # Allgemeine Baubeschränkungen
        restrictions.append({
            "type": "height_restriction",
            "description": "Maximale Gebäudehöhe 12m",
            "severity": "mandatory",
            "compliance": project.get("height_stories", 1) * 3 <= 12
        })
        
        restrictions.append({
            "type": "setback_requirements",
            "description": "Mindestabstand zu Grundstücksgrenzen 3m",
            "severity": "mandatory",
            "compliance": True  # Standardannahme
        })
        
        # Spezielle Beschränkungen basierend auf Projekttyp
        if "heritage_protection" in project.get("special_requirements", []):
            restrictions.append({
                "type": "heritage_protection",
                "description": "Denkmalschutz-Auflagen beachten",
                "severity": "critical",
                "compliance": None,  # Bedarf weiterer Prüfung
                "authority": "Denkmalschutzbehörde"
            })
        
        if project.get("purpose") == "commercial":
            restrictions.append({
                "type": "noise_protection",
                "description": "Lärmschutzauflagen nach TA Lärm",
                "severity": "mandatory",
                "compliance": None
            })
        
        return restrictions
    
    def _assess_approval_probability(self, project: Dict, zoning: Dict, restrictions: List) -> Dict[str, Any]:
        """Bewertet Wahrscheinlichkeit der Baugenehmigung"""
        
        # Compliance-Check
        compliant_restrictions = [r for r in restrictions if r.get("compliance") is True]
        non_compliant = [r for r in restrictions if r.get("compliance") is False]
        needs_review = [r for r in restrictions if r.get("compliance") is None]
        
        # Wahrscheinlichkeits-Score
        if non_compliant:
            probability = 0.2  # Niedrig bei Nicht-Erfüllung
            assessment = "problematisch"
        elif needs_review:
            probability = 0.6  # Mittel bei unklaren Punkten
            assessment = "weitere Prüfung erforderlich"
        else:
            probability = 0.9  # Hoch bei vollständiger Erfüllung
            assessment = "sehr wahrscheinlich"
        
        # Zeitsschätzung
        estimated_time = self._estimate_approval_time(project, needs_review)
        
        return {
            "probability": probability,
            "assessment": assessment,
            "estimated_processing_time_weeks": estimated_time,
            "compliance_summary": {
                "compliant": len(compliant_restrictions),
                "non_compliant": len(non_compliant),
                "needs_review": len(needs_review)
            },
            "next_steps": self._generate_next_steps(project, restrictions),
            "required_documents": self._list_required_documents(project)
        }
    
    def _estimate_approval_time(self, project: Dict, unclear_points: List) -> int:
        """Schätzt Bearbeitungszeit für Baugenehmigung"""
        
        base_time = {
            "sehr_klein": 3,  # 3 Wochen
            "klein": 6,       # 6 Wochen
            "mittel": 12,     # 12 Wochen
            "groß": 20        # 20 Wochen
        }
        
        time_weeks = base_time.get(project.get("scale", "klein"), 6)
        
        # Komplexitäts-Faktoren
        if unclear_points:
            time_weeks += len(unclear_points) * 2
        
        if "heritage_protection" in project.get("special_requirements", []):
            time_weeks += 8  # Denkmalschutz verlängert Verfahren
        
        return time_weeks
    
    def _generate_next_steps(self, project: Dict, restrictions: List) -> List[str]:
        """Generiert konkrete nächste Schritte"""
        
        steps = [
            "Bauantrag bei der Bauaufsichtsbehörde einreichen",
            "Vollständige Bauzeichnungen erstellen lassen"
        ]
        
        # Spezifische Schritte basierend auf Beschränkungen
        for restriction in restrictions:
            if restriction.get("compliance") is None:
                if restriction["type"] == "heritage_protection":
                    steps.append("Denkmalschutzbehörde kontaktieren")
                elif restriction["type"] == "noise_protection":
                    steps.append("Lärmgutachten erstellen lassen")
        
        # Standardschritte
        steps.extend([
            "Nachbarn über Bauvorhaben informieren",
            "Bauherr und Architekt bestimmen",
            "Finanzierung sicherstellen"
        ])
        
        return steps
    
    def _list_required_documents(self, project: Dict) -> List[str]:
        """Listet erforderliche Dokumente auf"""
        
        documents = [
            "Bauantrag (amtliches Formular)",
            "Bauzeichnungen (Grundrisse, Schnitte, Ansichten)",
            "Lageplan",
            "Baubeschreibung",
            "Statische Berechnung",
            "Nachweis der Standsicherheit"
        ]
        
        # Projektspezifische Dokumente
        if project.get("purpose") == "commercial":
            documents.extend([
                "Brandschutzkonzept",
                "Lärmschutznachweis"
            ])
        
        if "energy_efficiency" in project.get("special_requirements", []):
            documents.append("Energieausweis / GEG-Nachweis")
        
        if "heritage_protection" in project.get("special_requirements", []):
            documents.append("Stellungnahme Denkmalschutzbehörde")
        
        return documents

class UrbanPlanningWorker(BaseWorker):
    """Worker für Stadtplanung und Flächennutzung"""
    
    def __init__(self):
        from covina_core import WorkerType
        super().__init__(WorkerType.URBAN_PLANNING, cache_ttl=7200)  # 2 Stunden Cache
    
    def _extract_location(self, query: str) -> Dict[str, Any]:
        """Extrahiert Standortinformationen aus der Anfrage"""
        location = {
            "name": "München",
            "state": "Bayern", 
            "country": "Deutschland",
            "coordinates": {"lat": 48.1351, "lon": 11.5820}
        }
        
        # Einfache Standorterkennung
        if "berlin" in query.lower():
            location.update({"name": "Berlin", "state": "Berlin", "coordinates": {"lat": 52.5200, "lon": 13.4050}})
        elif "hamburg" in query.lower():
            location.update({"name": "Hamburg", "state": "Hamburg", "coordinates": {"lat": 53.5511, "lon": 9.9937}})
        elif "münchen" in query.lower() or "munich" in query.lower():
            location.update({"name": "München", "state": "Bayern", "coordinates": {"lat": 48.1351, "lon": 11.5820}})
        
        return location
    
    async def _process_internal(self, metadata, user_profile: Dict = None) -> Dict[str, Any]:
        """Analysiert Stadtplanung und Flächennutzungsplanung"""
        
        location = self._extract_location(metadata.normalized_query)
        planning_concern = self._extract_planning_concern(metadata.normalized_query)
        
        try:
            # Aktuelle Flächennutzung analysieren
            current_land_use = await self._analyze_current_land_use(location)
            
            # Geplante Änderungen identifizieren
            planned_changes = await self._get_planned_changes(location)
            
            # Auswirkungen bewerten
            impact_assessment = await self._assess_planning_impact(location, planned_changes, planning_concern)
            
            # Beteiligungsmöglichkeiten finden
            participation_options = self._identify_participation_options(planned_changes)
            
            return {
                "current_land_use": current_land_use,
                "planned_changes": planned_changes,
                "impact_assessment": impact_assessment,
                "participation_options": participation_options,
                "summary": f"Stadtplanungsanalyse für {location.get('name', 'Gebiet')}: {len(planned_changes)} geplante Änderungen",
                "confidence_score": 0.8,
                "sources": [{"type": "urban_planning_data", "location": location}]
            }
            
        except Exception as e:
            logging.error(f"❌ UrbanPlanningWorker Error: {e}")
            return {
                "current_land_use": {},
                "planned_changes": [],
                "summary": f"Stadtplanungsanalyse fehlgeschlagen: {str(e)}",
                "confidence_score": 0.0,
                "error": str(e)
            }
    
    def _extract_planning_concern(self, query: str) -> Dict[str, Any]:
        """Extrahiert Planungsanliegen aus Query"""
        
        concerns = {
            "type": "general",
            "focus": [],
            "timeline": "current"
        }
        
        # Anliegen-Kategorien
        if any(word in query.lower() for word in ["verkehr", "straße", "parkplatz"]):
            concerns["focus"].append("traffic")
        if any(word in query.lower() for word in ["grün", "park", "spielplatz"]):
            concerns["focus"].append("green_space")
        if any(word in query.lower() for word in ["wohnen", "miete", "immobilien"]):
            concerns["focus"].append("housing")
        if any(word in query.lower() for word in ["gewerbe", "industrie", "arbeitsplatz"]):
            concerns["focus"].append("commercial")
        if any(word in query.lower() for word in ["lärmschutz", "umwelt"]):
            concerns["focus"].append("environmental")
        
        # Zeitbezug
        if any(word in query.lower() for word in ["zukunft", "geplant", "soll"]):
            concerns["timeline"] = "future"
        
        return concerns
    
    async def _analyze_current_land_use(self, location: Dict) -> Dict[str, Any]:
        """Analysiert aktuelle Flächennutzung"""
        await asyncio.sleep(0.4)
        
        # Mock-Flächennutzungsanalyse
        land_use = {
            "zone_designation": "Mischgebiet",
            "current_usage": {
                "residential": 45,  # Prozent
                "commercial": 25,
                "green_space": 20,
                "traffic": 10
            },
            "building_density": "medium",
            "infrastructure_quality": {
                "public_transport": "good",
                "parking": "limited",
                "green_areas": "adequate",
                "noise_level": "moderate"
            },
            "development_potential": {
                "buildable_area_remaining": 15,  # Prozent
                "height_increase_possible": True,
                "use_intensification": "limited"
            }
        }
        
        return land_use
    
    async def _get_planned_changes(self, location: Dict) -> List[Dict]:
        """Identifiziert geplante Stadtplanungsänderungen"""
        await asyncio.sleep(0.5)
        
        # Mock-Planungsvorhaben
        changes = [
            {
                "project_id": "SP-2025-042",
                "title": "Neubaugebiet Süd",
                "type": "residential_development",
                "status": "planning_phase",
                "timeline": {
                    "planning_start": "2025-01-01",
                    "public_participation": "2025-03-15",
                    "decision_expected": "2025-06-30",
                    "construction_start": "2026-01-01"
                },
                "description": "Entwicklung von 200 Wohneinheiten",
                "area_hectares": 12.5,
                "impact_radius_km": 2.0,
                "key_features": [
                    "200 Wohneinheiten",
                    "Kindergarten",
                    "Nahversorgung",
                    "Grünflächen 30%"
                ]
            },
            {
                "project_id": "SP-2025-018", 
                "title": "Verkehrsberuhigung Hauptstraße",
                "type": "traffic_modification",
                "status": "approved",
                "timeline": {
                    "planning_start": "2024-09-01",
                    "construction_start": "2025-04-01",
                    "completion": "2025-08-31"
                },
                "description": "Tempo 30 und Fahrradwege",
                "impact_radius_km": 1.5,
                "key_features": [
                    "Tempo-30-Zone",
                    "Geschützte Radwege",
                    "Mehr Zebrastreifen",
                    "Parkplatz-Reduzierung"
                ]
            }
        ]
        
        return changes
    
    async def _assess_planning_impact(self, location: Dict, changes: List, concern: Dict) -> Dict[str, Any]:
        """Bewertet Auswirkungen der Planungsänderungen"""
        await asyncio.sleep(0.3)
        
        impact = {
            "overall_impact": "positive",
            "detailed_impacts": {},
            "concerns": [],
            "benefits": []
        }
        
        for change in changes:
            change_type = change.get("type", "")
            
            if change_type == "residential_development":
                impact["detailed_impacts"]["housing"] = {
                    "impact": "positive",
                    "description": "Mehr Wohnraum verfügbar",
                    "magnitude": "high"
                }
                impact["detailed_impacts"]["traffic"] = {
                    "impact": "negative",
                    "description": "Erhöhtes Verkehrsaufkommen",
                    "magnitude": "medium"
                }
                impact["concerns"].append("Verkehrszunahme um ca. 30%")
                impact["benefits"].append("200 neue Wohnungen für ca. 400 Bewohner")
            
            elif change_type == "traffic_modification":
                impact["detailed_impacts"]["traffic"] = {
                    "impact": "positive",
                    "description": "Verkehrsberuhigung und Sicherheit",
                    "magnitude": "medium"
                }
                impact["detailed_impacts"]["environment"] = {
                    "impact": "positive",
                    "description": "Weniger Lärm und Abgase",
                    "magnitude": "low"
                }
                impact["benefits"].extend([
                    "Erhöhte Verkehrssicherheit",
                    "Bessere Luftqualität",
                    "Mehr Platz für Fußgänger und Radfahrer"
                ])
        
        return impact
    
    def _identify_participation_options(self, changes: List) -> List[Dict]:
        """Identifiziert Bürgerbeteiligungsmöglichkeiten"""
        
        options = []
        
        for change in changes:
            if change.get("status") == "planning_phase":
                options.append({
                    "project": change["title"],
                    "participation_type": "public_hearing",
                    "date": change["timeline"].get("public_participation"),
                    "description": "Öffentliche Anhörung zum Bebauungsplan",
                    "how_to_participate": [
                        "Teilnahme an öffentlicher Versammlung",
                        "Schriftliche Stellungnahme einreichen",
                        "Online-Beteiligung nutzen"
                    ],
                    "deadline": "30 Tage nach Bekanntmachung",
                    "contact": "stadtplanung@municipality.de"
                })
        
        # Allgemeine Beteiligungsoptionen
        options.append({
            "project": "Allgemeine Stadtentwicklung",
            "participation_type": "citizen_initiative",
            "description": "Bürgerinitiative gründen",
            "how_to_participate": [
                "Mindestens 10 Unterstützer sammeln",
                "Anliegen formulieren",
                "Bei Stadtrat einreichen"
            ],
            "contact": "buergerbuero@municipality.de"
        })
        
        return options

class HeritageProtectionWorker(BaseWorker):
    """Worker für Denkmalschutz und historische Gebäude"""
    
    def __init__(self):
        from covina_core import WorkerType
        super().__init__(WorkerType.HERITAGE_PROTECTION, cache_ttl=7200)  # 2 Stunden Cache
    
    def _extract_location(self, query: str) -> Dict[str, Any]:
        """Extrahiert Standortinformationen aus der Anfrage"""
        location = {
            "name": "München",
            "state": "Bayern", 
            "country": "Deutschland",
            "coordinates": {"lat": 48.1351, "lon": 11.5820}
        }
        
        # Einfache Standorterkennung
        if "berlin" in query.lower():
            location.update({"name": "Berlin", "state": "Berlin", "coordinates": {"lat": 52.5200, "lon": 13.4050}})
        elif "hamburg" in query.lower():
            location.update({"name": "Hamburg", "state": "Hamburg", "coordinates": {"lat": 53.5511, "lon": 9.9937}})
        elif "münchen" in query.lower() or "munich" in query.lower():
            location.update({"name": "München", "state": "Bayern", "coordinates": {"lat": 48.1351, "lon": 11.5820}})
        
        return location
    
    async def _process_internal(self, metadata, user_profile: Dict = None) -> Dict[str, Any]:
        """Analysiert Denkmalschutz-Angelegenheiten"""
        
        location = self._extract_location(metadata.normalized_query)
        building_info = self._extract_building_info(metadata.normalized_query)
        
        try:
            # Denkmalschutz-Status prüfen
            heritage_status = await self._check_heritage_status(location, building_info)
            
            # Genehmigungsanforderungen ermitteln
            permit_requirements = await self._determine_permit_requirements(heritage_status, building_info)
            
            # Förderungen identifizieren
            funding_options = await self._identify_funding_options(heritage_status, building_info)
            
            # Compliance-Richtlinien bereitstellen
            compliance_guidelines = self._generate_compliance_guidelines(heritage_status)
            
            return {
                "heritage_status": heritage_status,
                "permit_requirements": permit_requirements,
                "funding_options": funding_options,
                "compliance_guidelines": compliance_guidelines,
                "summary": f"Denkmalschutzanalyse: {heritage_status.get('protection_level', 'nicht geschützt')}",
                "confidence_score": 0.85,
                "sources": [{"type": "heritage_protection_database", "location": location}]
            }
            
        except Exception as e:
            logging.error(f"❌ HeritageProtectionWorker Error: {e}")
            return {
                "heritage_status": {},
                "summary": f"Denkmalschutzanalyse fehlgeschlagen: {str(e)}",
                "confidence_score": 0.0,
                "error": str(e)
            }
    
    def _extract_building_info(self, query: str) -> Dict[str, Any]:
        """Extrahiert Gebäudeinformationen aus Query"""
        
        building = {
            "construction_year": None,
            "building_type": "unknown",
            "planned_work": "renovation"
        }
        
        # Jahr extrahieren
        import re
        years = re.findall(r'\b(18\d{2}|19\d{2}|20\d{2})\b', query)
        if years:
            building["construction_year"] = int(years[0])
        
        # Gebäudetyp
        if any(word in query.lower() for word in ["villa", "herrenhaus"]):
            building["building_type"] = "villa"
        elif any(word in query.lower() for word in ["bauernhaus", "fachwerkhaus"]):
            building["building_type"] = "traditional_house"
        elif any(word in query.lower() for word in ["kirche", "kapelle"]):
            building["building_type"] = "religious"
        elif any(word in query.lower() for word in ["fabrik", "industrie"]):
            building["building_type"] = "industrial"
        
        # Geplante Arbeiten
        if any(word in query.lower() for word in ["sanierung", "renovierung"]):
            building["planned_work"] = "renovation"
        elif any(word in query.lower() for word in ["energie", "dämmung"]):
            building["planned_work"] = "energy_retrofit"
        elif any(word in query.lower() for word in ["anbau", "erweiterung"]):
            building["planned_work"] = "extension"
        
        return building
    
    async def _check_heritage_status(self, location: Dict, building: Dict) -> Dict[str, Any]:
        """Prüft Denkmalschutz-Status"""
        await asyncio.sleep(0.3)
        
        # Mock-Denkmalschutz-Bewertung
        construction_year = building.get("construction_year")
        building_type = building.get("building_type", "unknown")
        
        if construction_year and construction_year < 1900:
            protection_level = "listed_monument"
            protection_reason = "Historische Bedeutung (vor 1900)"
        elif construction_year and construction_year < 1950 and building_type in ["villa", "traditional_house"]:
            protection_level = "architectural_interest" 
            protection_reason = "Architektonische Bedeutung"
        else:
            protection_level = "not_protected"
            protection_reason = "Keine Schutzkriterien erfüllt"
        
        status = {
            "protection_level": protection_level,
            "protection_reason": protection_reason,
            "listing_date": "1995-03-15" if protection_level == "listed_monument" else None,
            "responsible_authority": "Bayerisches Landesamt für Denkmalpflege",
            "monument_id": "D-1-84-000-123" if protection_level == "listed_monument" else None,
            "protection_scope": {
                "exterior": True if protection_level in ["listed_monument", "architectural_interest"] else False,
                "interior": True if protection_level == "listed_monument" else False,
                "garden": True if building_type == "villa" and protection_level == "listed_monument" else False
            }
        }
        
        return status
    
    async def _determine_permit_requirements(self, heritage_status: Dict, building: Dict) -> Dict[str, Any]:
        """Ermittelt Genehmigungsanforderungen"""
        await asyncio.sleep(0.2)
        
        protection_level = heritage_status.get("protection_level", "not_protected")
        planned_work = building.get("planned_work", "renovation")
        
        requirements = {
            "permit_required": False,
            "permit_type": None,
            "required_documents": [],
            "approval_authority": None,
            "estimated_processing_time_weeks": 0,
            "special_requirements": []
        }
        
        if protection_level == "listed_monument":
            requirements.update({
                "permit_required": True,
                "permit_type": "Denkmalschutzrechtliche Erlaubnis",
                "approval_authority": "Untere Denkmalschutzbehörde",
                "estimated_processing_time_weeks": 8,
                "required_documents": [
                    "Antrag auf denkmalschutzrechtliche Erlaubnis",
                    "Detaillierte Baupläne",
                    "Bauhistorische Dokumentation", 
                    "Materialangaben",
                    "Fotos aktueller Zustand"
                ],
                "special_requirements": [
                    "Verwendung historischer Materialien bevorzugt",
                    "Erhaltung der Originalsubstanz",
                    "Baubegleitung durch Denkmalpfleger möglich"
                ]
            })
            
            if planned_work == "energy_retrofit":
                requirements["special_requirements"].extend([
                    "Energetische Maßnahmen nur mit Sondergenehmigung",
                    "Innendämmung bevorzugt",
                    "Historische Fenster möglichst erhalten"
                ])
        
        elif protection_level == "architectural_interest":
            requirements.update({
                "permit_required": True,
                "permit_type": "Bauantrag mit Denkmalschutz-Prüfung",
                "approval_authority": "Bauaufsichtsbehörde (mit Stellungnahme Denkmalschutz)",
                "estimated_processing_time_weeks": 6,
                "required_documents": [
                    "Regulärer Bauantrag",
                    "Stellungnahme Denkmalschutzbehörde"
                ]
            })
        
        return requirements
    
    async def _identify_funding_options(self, heritage_status: Dict, building: Dict) -> List[Dict]:
        """Identifiziert Förderungsmöglichkeiten"""
        await asyncio.sleep(0.3)
        
        protection_level = heritage_status.get("protection_level", "not_protected")
        planned_work = building.get("planned_work", "renovation")
        
        funding_options = []
        
        if protection_level == "listed_monument":
            funding_options.extend([
                {
                    "program": "Denkmalschutz-AfA",
                    "type": "tax_deduction",
                    "amount": "bis zu 90% der Sanierungskosten über 12 Jahre",
                    "requirements": [
                        "Denkmalgeschütztes Gebäude",
                        "Eigennutzung oder Vermietung",
                        "Abstimmung mit Denkmalschutzbehörde"
                    ],
                    "application_process": "Über Steuerberater bei Finanzamt"
                },
                {
                    "program": "Bayerisches Denkmalschutz-Sonderprogramm",
                    "type": "direct_subsidy",
                    "amount": "bis zu 40% der förderfähigen Kosten, max. 100.000€",
                    "requirements": [
                        "Außergewöhnliche Denkmalbedeutung",
                        "Wirtschaftliche Unzumutbarkeit",
                        "Vorherige Antragstellung"
                    ],
                    "application_process": "Bayerisches Landesamt für Denkmalpflege"
                }
            ])
        
        if planned_work == "energy_retrofit":
            funding_options.append({
                "program": "KfW-Effizienzhaus Denkmal",
                "type": "low_interest_loan",
                "amount": "bis zu 150.000€ + Tilgungszuschuss bis 37.500€",
                "requirements": [
                    "Effizienzhaus Denkmal Standard erreichen",
                    "Energieberater einbeziehen",
                    "Antrag vor Baubeginnen"
                ],
                "application_process": "KfW über Hausbank"
            })
        
        # Kommunale Förderungen
        funding_options.append({
            "program": "Kommunales Altstadtförderprogramm",
            "type": "municipal_grant",
            "amount": "bis zu 25% der Sanierungskosten",
            "requirements": [
                "Gebäude in Altstadt-Sanierungsgebiet",
                "Verbesserung des Straßenbildes"
            ],
            "application_process": "Stadtverwaltung / Bauamt"
        })
        
        return funding_options
    
    def _generate_compliance_guidelines(self, heritage_status: Dict) -> List[str]:
        """Generiert Compliance-Richtlinien"""
        
        protection_level = heritage_status.get("protection_level", "not_protected")
        
        guidelines = []
        
        if protection_level == "listed_monument":
            guidelines.extend([
                "Alle Änderungen bedürfen der denkmalschutzrechtlichen Erlaubnis",
                "Originalsubstanz ist zu erhalten und zu pflegen",
                "Historische Materialien sind zu bevorzugen",
                "Baumaßnahmen sind fachgerecht zu dokumentieren",
                "Regelmäßige Wartung ist zur Schadensvorbeugung erforderlich"
            ])
        
        elif protection_level == "architectural_interest":
            guidelines.extend([
                "Charakteristische Merkmale der Architektur sind zu erhalten",
                "Änderungen an der Außenansicht sind anzuzeigen",
                "Historische Elemente sollten erhalten werden"
            ])
        
        # Allgemeine Richtlinien
        guidelines.extend([
            "Vor Beginn jeder Maßnahme ist fachlicher Rat einzuholen",
            "Dokumentation des Ist-Zustands vor Baumaßnahmen",
            "Verwendung traditioneller Handwerkstechniken bevorzugt"
        ])
        
        return guidelines

# Registrierung der Worker
CONSTRUCTION_WORKERS = {
    "building_permit": BuildingPermitWorker,
    "urban_planning": UrbanPlanningWorker,
    "heritage_protection": HeritageProtectionWorker
}

__all__ = ["BuildingPermitWorker", "UrbanPlanningWorker", "HeritageProtectionWorker", "CONSTRUCTION_WORKERS"]
