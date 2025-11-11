#!/usr/bin/env python3
"""
VERITAS Traffic & Transport Workers
Spezialisierte Worker für Verkehrs- und Transportanfragen
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import aiohttp

# Import base classes from framework
try:
    from backend.agents.framework.base_agent import BaseAgent as BaseWorker
except ImportError:
    import os
    import sys

    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from backend.agents.framework.base_agent import BaseAgent as BaseWorker

# ExternalAPIWorker is same as BaseWorker for now
ExternalAPIWorker = BaseWorker


class TrafficManagementWorker(ExternalAPIWorker):
    """Worker für Verkehrsmanagement und Verkehrsplanung"""

    def __init__(self):
        from covina_core import WorkerType

        super().__init__(WorkerType.TRAFFIC_MANAGEMENT, "https://api.verkehr.de/", cache_ttl=900)  # 15 Minuten Cache
        self.traffic_apis = {
            "municipal_traffic": "https://api.municipality.de / traffic/",
            "state_traffic": "https://api.state.de / verkehr/",
            "federal_traffic": "https://api.bast.de / ",
        }

    def _extract_location(self, query: str) -> Dict[str, Any]:
        """Extrahiert Standortinformationen aus der Anfrage"""
        location = {
            "name": "München",
            "state": "Bayern",
            "country": "Deutschland",
            "coordinates": {"lat": 48.1351, "lon": 11.5820},
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
        """Analysiert Verkehrssituation und Verkehrsplanung"""

        location = self._extract_location(metadata.normalized_query)
        traffic_concern = self._extract_traffic_concern(metadata.normalized_query)

        if not location:
            return {
                "traffic_analysis": {},
                "measures": [],
                "summary": "Keine Standortangabe für Verkehrsanalyse gefunden",
                "confidence_score": 0.2,
            }

        try:
            # Aktuelle Verkehrssituation analysieren
            current_traffic = await self._analyze_current_traffic(location)

            # Verkehrsprobleme identifizieren
            traffic_issues = await self._identify_traffic_issues(location, traffic_concern)

            # Mögliche Maßnahmen bewerten
            potential_measures = await self._evaluate_traffic_measures(location, traffic_issues)

            # Antragsverfahren ermitteln
            application_process = self._determine_application_process(potential_measures)

            return {
                "current_traffic": current_traffic,
                "traffic_issues": traffic_issues,
                "potential_measures": potential_measures,
                "application_process": application_process,
                "summary": f"Verkehrsanalyse für {location.get('name', 'Gebiet')}: {len(traffic_issues)} identifizierte Probleme",
                "confidence_score": 0.8,
                "sources": [{"type": "traffic_management_data", "location": location}],
            }

        except Exception as e:
            logging.error(f"❌ TrafficManagementWorker Error: {e}")
            return {
                "current_traffic": {},
                "traffic_issues": [],
                "summary": f"Verkehrsanalyse fehlgeschlagen: {str(e)}",
                "confidence_score": 0.0,
                "error": str(e),
            }

    def _extract_traffic_concern(self, query: str) -> Dict[str, Any]:
        """Extrahiert Verkehrsanliegen aus Query"""

        concern = {"type": "general", "specific_issues": [], "proposed_solution": None}

        # Verkehrsprobleme identifizieren
        if any(word in query.lower() for word in ["raser", "schnell", "geschwindigkeit"]):
            concern["specific_issues"].append("speeding")
        if any(word in query.lower() for word in ["laut", "lärm", "ruhig"]):
            concern["specific_issues"].append("noise")
        if any(word in query.lower() for word in ["gefährlich", "unfall", "sicherheit"]):
            concern["specific_issues"].append("safety")
        if any(word in query.lower() for word in ["parkplatz", "parken", "stau"]):
            concern["specific_issues"].append("parking")
        if any(word in query.lower() for word in ["fahrrad", "radweg"]):
            concern["specific_issues"].append("cycling_infrastructure")
        if any(word in query.lower() for word in ["fußgänger", "gehweg", "zebrastreifen"]):
            concern["specific_issues"].append("pedestrian_safety")

        # Lösungsvorschläge
        if any(word in query.lower() for word in ["tempo 30", "tempo-30"]):
            concern["proposed_solution"] = "speed_limit_30"
        elif any(word in query.lower() for word in ["ampel", "lichtsignalanlage"]):
            concern["proposed_solution"] = "traffic_lights"
        elif any(word in query.lower() for word in ["zebrastreifen", "überquerung"]):
            concern["proposed_solution"] = "pedestrian_crossing"
        elif any(word in query.lower() for word in ["verkehrsberuhigung", "beruhigt"]):
            concern["proposed_solution"] = "traffic_calming"

        return concern

    async def _analyze_current_traffic(self, location: Dict) -> Dict[str, Any]:
        """Analysiert aktuelle Verkehrssituation"""
        await asyncio.sleep(0.4)

        # Mock-Verkehrsanalyse
        traffic_data = {
            "daily_traffic_volume": 8500,  # Kfz / Tag
            "peak_hours": ["07:00 - 09:00", "17:00 - 19:00"],
            "average_speed_kmh": 35,
            "speed_violations_per_week": 15,
            "accident_rate_per_year": 3,
            "road_classification": "Hauptverkehrsstraße",
            "current_speed_limit": 50,
            "traffic_composition": {"cars": 75, "trucks": 15, "buses": 5, "motorcycles": 3, "bicycles": 2},  # Prozent
            "noise_level_db": {"day": 58, "night": 52},
            "pedestrian_infrastructure": {
                "sidewalks": "adequate",
                "crossings": "limited",
                "accessibility": "partially_accessible",
            },
        }

        return traffic_data

    async def _identify_traffic_issues(self, location: Dict, concern: Dict) -> List[Dict]:
        """Identifiziert spezifische Verkehrsprobleme"""
        await asyncio.sleep(0.3)

        issues = []

        # Basierend auf Traffic-Daten und Concerns
        current_traffic = await self._analyze_current_traffic(location)

        if current_traffic["speed_violations_per_week"] > 10:
            issues.append(
                {
                    "type": "speeding",
                    "severity": "high",
                    "description": f"{current_traffic['speed_violations_per_week']} Geschwindigkeitsverstöße pro Woche",
                    "evidence": "Radarkontrollen zeigen regelmäßige Überschreitungen",
                    "affected_area": "Hauptstraße zwischen Kreuzung A und B",
                }
            )

        if current_traffic["noise_level_db"]["night"] > 49:  # WHO-Richtwert
            issues.append(
                {
                    "type": "noise_pollution",
                    "severity": "medium",
                    "description": f"Nachtlärm {current_traffic['noise_level_db']['night']} dB (Grenzwert: 49 dB)",
                    "evidence": "Lärmschutz-Grenzwerte überschritten",
                    "affected_area": "Anwohner entlang der Hauptstraße",
                }
            )

        if current_traffic["accident_rate_per_year"] > 2:
            issues.append(
                {
                    "type": "safety_risk",
                    "severity": "high",
                    "description": f"{current_traffic['accident_rate_per_year']} Unfälle pro Jahr",
                    "evidence": "Unfallstatistik der Polizei",
                    "affected_area": "Kreuzungsbereich und Schulweg",
                }
            )

        if "cycling_infrastructure" in concern["specific_issues"]:
            issues.append(
                {
                    "type": "inadequate_cycling_infrastructure",
                    "severity": "medium",
                    "description": "Fehlende oder unzureichende Radwege",
                    "evidence": "Radfahrer müssen auf Fahrbahn fahren",
                    "affected_area": "Gesamte Straße",
                }
            )

        return issues

    async def _evaluate_traffic_measures(self, location: Dict, issues: List) -> List[Dict]:
        """Bewertet mögliche Verkehrsmaßnahmen"""
        await asyncio.sleep(0.4)

        measures = []

        for issue in issues:
            issue_type = issue["type"]

            if issue_type == "speeding":
                measures.extend(
                    [
                        {
                            "measure": "Tempo - 30-Zone einrichten",
                            "effectiveness": "high",
                            "cost_estimate": "5.000 - 15.000 €",
                            "implementation_time": "3 - 6 Monate",
                            "requirements": ["Verkehrsmessung dokumentieren", "Anwohner - Petition", "Stadtrat - Beschluss"],
                            "expected_benefits": [
                                "50% weniger Geschwindigkeitsverstöße",
                                "30% Lärmreduzierung",
                                "Erhöhte Verkehrssicherheit",
                            ],
                        },
                        {
                            "measure": "Radarkontrollen verstärken",
                            "effectiveness": "medium",
                            "cost_estimate": "Laufende Kosten",
                            "implementation_time": "sofort möglich",
                            "requirements": ["Antrag bei Ordnungsamt"],
                            "expected_benefits": ["Kurzfristige Geschwindigkeitsreduzierung"],
                        },
                    ]
                )

            elif issue_type == "safety_risk":
                measures.extend(
                    [
                        {
                            "measure": "Zebrastreifen errichten",
                            "effectiveness": "high",
                            "cost_estimate": "8.000 - 20.000 €",
                            "implementation_time": "6 - 12 Monate",
                            "requirements": ["Verkehrsgutachten", "Beleuchtung prüfen", "Sichtweiten gewährleisten"],
                            "expected_benefits": ["Sichere Querungsmöglichkeit", "Verkehrsberuhigender Effekt"],
                        },
                        {
                            "measure": "Ampelanlage installieren",
                            "effectiveness": "very_high",
                            "cost_estimate": "80.000 - 150.000 €",
                            "implementation_time": "12 - 18 Monate",
                            "requirements": ["Verkehrsgutachten", "Finanzierung klären", "Verkehrsverbund abstimmen"],
                            "expected_benefits": ["Hohe Verkehrssicherheit", "Geregelter Verkehrsfluss"],
                        },
                    ]
                )

            elif issue_type == "inadequate_cycling_infrastructure":
                measures.append(
                    {
                        "measure": "Geschützten Radweg anlegen",
                        "effectiveness": "high",
                        "cost_estimate": "50.000 - 100.000 € pro km",
                        "implementation_time": "12 - 24 Monate",
                        "requirements": [
                            "Straßenraum - Neuaufteilung",
                            "Parkplatz - Reduzierung möglich",
                            "Radverkehrskonzept",
                        ],
                        "expected_benefits": ["Sichere Radverkehrsführung", "Förderung umweltfreundlicher Mobilität"],
                    }
                )

        return measures

    def _determine_application_process(self, measures: List) -> Dict[str, Any]:
        """Ermittelt Antragsverfahren für Verkehrsmaßnahmen"""

        process = {
            "citizen_petition": {
                "description": "Bürgerantrag für Verkehrsmaßnahmen",
                "requirements": [
                    "Mindestens 50 Unterschriften von Anwohnern",
                    "Konkrete Problembeschreibung",
                    "Lösungsvorschläge",
                ],
                "submission_to": "Tiefbauamt / Verkehrsbehörde",
                "processing_time": "4 - 8 Wochen für erste Prüfung",
                "success_factors": [
                    "Verkehrsproblem objektiv nachweisbar",
                    "Breite Unterstützung der Anwohner",
                    "Wirtschaftliche Machbarkeit",
                ],
            },
            "political_process": {
                "description": "Politische Meinungsbildung",
                "steps": [
                    "Antrag im Stadtrat / Gemeinderat",
                    "Ausschuss - Beratung",
                    "Öffentliche Anhörung",
                    "Beschlussfassung",
                ],
                "timeline": "3 - 12 Monate je nach Komplexität",
                "influencing_factors": ["Verfügbare Haushaltsmittel", "Politische Prioritäten", "Verkehrsentwicklungsplan"],
            },
            "alternative_approaches": [
                {
                    "approach": "Verkehrswacht kontaktieren",
                    "description": "Für Verkehrssicherheits - Maßnahmen",
                    "timeline": "2 - 4 Wochen",
                },
                {
                    "approach": "Polizei für Kontrollen ansprechen",
                    "description": "Für kurzfristige Überwachung",
                    "timeline": "1 - 2 Wochen",
                },
                {
                    "approach": "Bürgerinititative gründen",
                    "description": "Für größere Verkehrsprojekte",
                    "timeline": "Langfristig (6+ Monate)",
                },
            ],
        }

        return process


class PublicTransportWorker(ExternalAPIWorker):
    """Worker für öffentlichen Nahverkehr"""

    def __init__(self):
        from covina_core import WorkerType

        super().__init__(WorkerType.PUBLIC_TRANSPORT, "https://api.verkehr.de/", cache_ttl=600)  # 10 Minuten Cache
        self.transport_apis = {
            "local_transport": "https://api.local - transport.de/",
            "regional_transport": "https://api.regional.de / ",
            "real_time": "https://api.realtime - transport.de/",
        }

    def _extract_location(self, query: str) -> Dict[str, Any]:
        """Extrahiert Standortinformationen aus der Anfrage"""
        location = {
            "name": "München",
            "state": "Bayern",
            "country": "Deutschland",
            "coordinates": {"lat": 48.1351, "lon": 11.5820},
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
        """Analysiert ÖPNV-Situation und -Verbesserungen"""

        location = self._extract_location(metadata.normalized_query)
        transport_need = self._extract_transport_need(metadata.normalized_query)

        try:
            # Aktuelle ÖPNV-Situation analysieren
            current_service = await self._analyze_current_transport_service(location)

            # Verbesserungspotentiale identifizieren
            improvement_potential = await self._identify_improvement_potential(location, transport_need)

            # Alternative Mobilitätsoptionen bewerten
            alternative_options = await self._evaluate_alternative_mobility(location, transport_need)

            # Ausbau-Planungen prüfen
            expansion_plans = await self._check_expansion_plans(location)

            return {
                "current_service": current_service,
                "improvement_potential": improvement_potential,
                "alternative_options": alternative_options,
                "expansion_plans": expansion_plans,
                "summary": f"ÖPNV - Analyse für {location.get('name', 'Gebiet')}: {current_service.get('service_quality', 'unbekannt')} Service-Qualität",
                "confidence_score": 0.8,
                "sources": [{"type": "public_transport_data", "location": location}],
            }

        except Exception as e:
            logging.error(f"❌ PublicTransportWorker Error: {e}")
            return {
                "current_service": {},
                "summary": f"ÖPNV-Analyse fehlgeschlagen: {str(e)}",
                "confidence_score": 0.0,
                "error": str(e),
            }

    def _extract_transport_need(self, query: str) -> Dict[str, Any]:
        """Extrahiert ÖPNV-Bedarf aus Query"""

        need = {"type": "general_improvement", "specific_requests": [], "target_destinations": [], "time_constraints": []}

        # Spezifische Anfragen
        if any(word in query.lower() for word in ["häufiger", "öfter", "takt"]):
            need["specific_requests"].append("increased_frequency")
        if any(word in query.lower() for word in ["abends", "nacht", "spät"]):
            need["specific_requests"].append("extended_hours")
        if any(word in query.lower() for word in ["direktverbindung", "umsteigen"]):
            need["specific_requests"].append("direct_connection")
        if any(word in query.lower() for word in ["barrierefrei", "rollstuhl"]):
            need["specific_requests"].append("accessibility")

        # Ziele
        if any(word in query.lower() for word in ["innenstadt", "zentrum"]):
            need["target_destinations"].append("city_center")
        if any(word in query.lower() for word in ["bahnho", "hauptbahnhof"]):
            need["target_destinations"].append("main_station")
        if any(word in query.lower() for word in ["arbeitsplatz", "arbeit"]):
            need["target_destinations"].append("workplace")

        return need

    async def _analyze_current_transport_service(self, location: Dict) -> Dict[str, Any]:
        """Analysiert aktuelle ÖPNV-Versorgung"""
        await asyncio.sleep(0.4)

        # Mock ÖPNV-Analyse
        service = {
            "service_quality": "adequate",
            "nearby_stops": [
                {
                    "name": "Musterplatz",
                    "distance_meters": 350,
                    "lines": ["Bus 42", "Bus 17"],
                    "frequency_minutes": 20,
                    "operating_hours": "05:30 - 23:00",
                    "accessibility": "partially_accessible",
                },
                {
                    "name": "Hauptstraße",
                    "distance_meters": 650,
                    "lines": ["Tram 3", "Bus 42"],
                    "frequency_minutes": 10,
                    "operating_hours": "05:00 - 24:00",
                    "accessibility": "fully_accessible",
                },
            ],
            "connections_to_center": {
                "travel_time_minutes": 25,
                "transfers_required": 1,
                "frequency_peak_minutes": 10,
                "frequency_offpeak_minutes": 20,
            },
            "service_gaps": [
                "Sonntags reduzierter Takt",
                "Nach 23:00 Uhr keine Verbindung",
                "Umsteigen zum Hauptbahnhof erforderlich",
            ],
            "user_satisfaction": {"punctuality": 3.2, "frequency": 2.8, "accessibility": 3.5, "cleanliness": 3.0},  # 1-5 Skala
        }

        return service

    async def _identify_improvement_potential(self, location: Dict, need: Dict) -> List[Dict]:
        """Identifiziert Verbesserungspotentiale"""
        await asyncio.sleep(0.3)

        improvements = []

        if "increased_frequency" in need["specific_requests"]:
            improvements.append(
                {
                    "improvement": "Takt - Verdichtung",
                    "description": "Häufigere Verbindungen in Stoßzeiten",
                    "impact": "high",
                    "feasibility": "medium",
                    "cost_estimate": "Mittelfristig finanzierbar",
                    "implementation_requirements": [
                        "Mehr Fahrzeuge anschaffen",
                        "Personal aufstocken",
                        "Fahrplan - Optimierung",
                    ],
                }
            )

        if "extended_hours" in need["specific_requests"]:
            improvements.append(
                {
                    "improvement": "Erweiterte Betriebszeiten",
                    "description": "Längere Fahrzeiten abends und am Wochenende",
                    "impact": "medium",
                    "feasibility": "medium",
                    "cost_estimate": "Zusätzliche Betriebskosten",
                    "implementation_requirements": [
                        "Kostendeckung prüfen",
                        "Fahrpersonal für Spätschichten",
                        "Sicherheitskonzept für Nachtverkehr",
                    ],
                }
            )

        if "direct_connection" in need["specific_requests"]:
            improvements.append(
                {
                    "improvement": "Direkte Verbindung",
                    "description": "Neue Linie ohne Umsteigen",
                    "impact": "high",
                    "feasibility": "low",
                    "cost_estimate": "Hohe Investition erforderlich",
                    "implementation_requirements": [
                        "Neue Linienführung planen",
                        "Fahrzeug - Mehrkapazität",
                        "Umfassende Netzplanung",
                    ],
                }
            )

        return improvements

    async def _evaluate_alternative_mobility(self, location: Dict, need: Dict) -> List[Dict]:
        """Bewertet alternative Mobilitätsoptionen"""
        await asyncio.sleep(0.3)

        alternatives = [
            {
                "option": "Bike - Sharing",
                "availability": "verfügbar",
                "coverage_radius_km": 2.5,
                "cost_per_trip": "1 - 3 €",
                "pros": ["Flexible Nutzung", "Umweltfreundlich", "Gesund"],
                "cons": ["Wetterabhängig", "Begrenzte Reichweite"],
                "integration_with_public_transport": "gut",
            },
            {
                "option": "E - Scooter-Sharing",
                "availability": "verfügbar",
                "coverage_radius_km": 3.0,
                "cost_per_trip": "2 - 5 €",
                "pros": ["Schnell für kurze Strecken", "Kein Parkplatzproblem"],
                "cons": ["Teurer als ÖPNV", "Sicherheitsrisiken"],
                "integration_with_public_transport": "mäßig",
            },
            {
                "option": "Ridesharing / Fahrgemeinschaften",
                "availability": "über Apps organisierbar",
                "cost_per_trip": "variabel (4 - 15 €)",
                "pros": ["Direkte Verbindungen", "Kostenteilung möglich"],
                "cons": ["Abhängig von anderen Nutzern", "Unregelmäßig"],
                "integration_with_public_transport": "ergänzend",
            },
            {
                "option": "On - Demand-Shuttle",
                "availability": "geplant für 2026",
                "coverage_radius_km": 5.0,
                "cost_per_trip": "3 - 6 €",
                "pros": ["Flexible Routen", "Tür - zu-Tür - Service"],
                "cons": ["Höhere Kosten", "Wartezeiten"],
                "integration_with_public_transport": "sehr gut",
            },
        ]

        return alternatives

    async def _check_expansion_plans(self, location: Dict) -> List[Dict]:
        """Prüft ÖPNV-Ausbauplanungen"""
        await asyncio.sleep(0.2)

        # Mock Ausbauplanungen
        plans = [
            {
                "project": "Straßenbahn - Verlängerung Linie 3",
                "status": "in_planning",
                "planned_completion": "2027",
                "description": "Verlängerung um 4 km in Richtung Neubaugebiet",
                "impact_on_location": "medium",
                "expected_benefits": [
                    "Direktverbindung zur Innenstadt",
                    "Takt alle 7 - 10 Minuten",
                    "Barrierefreie Haltestellen",
                ],
                "funding_status": "gesichert",
                "current_phase": "Planfeststellungsverfahren",
            },
            {
                "project": "Schnellbus - Linie X42",
                "status": "approved",
                "planned_start": "2025",
                "description": "Express - Verbindung ohne Zwischenstopps",
                "impact_on_location": "high",
                "expected_benefits": ["Fahrzeit - Reduzierung um 15 Minuten", "Alle 15 Minuten in Stoßzeiten"],
                "funding_status": "finanziert",
                "current_phase": "Umsetzung",
            },
        ]

        return plans


class ParkingManagementWorker(BaseWorker):
    """Worker für Parkraummanagement"""

    def __init__(self):
        from covina_core import WorkerType

        super().__init__(WorkerType.PARKING_MANAGEMENT, cache_ttl=1800)  # 30 Minuten Cache

    def _extract_location(self, query: str) -> Dict[str, Any]:
        """Extrahiert Standortinformationen aus der Anfrage"""
        location = {
            "name": "München",
            "state": "Bayern",
            "country": "Deutschland",
            "coordinates": {"lat": 48.1351, "lon": 11.5820},
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
        """Analysiert Parkraum-Situation und Alternativen"""

        location = self._extract_location(metadata.normalized_query)
        parking_need = self._extract_parking_need(metadata.normalized_query)

        try:
            # Aktuelle Parksituation analysieren
            parking_situation = await self._analyze_parking_situation(location)

            # Kosten vergleichen
            cost_comparison = await self._compare_parking_costs(location)

            # Alternative Optionen bewerten
            alternative_options = await self._evaluate_parking_alternatives(location, parking_need)

            # Zukünftige Entwicklungen prüfen
            future_developments = await self._check_parking_developments(location)

            return {
                "parking_situation": parking_situation,
                "cost_comparison": cost_comparison,
                "alternative_options": alternative_options,
                "future_developments": future_developments,
                "summary": f"Parkraumanalyse für {location.get('name', 'Gebiet')}: {parking_situation.get('availability', 'unbekannt')} Verfügbarkeit",
                "confidence_score": 0.85,
                "sources": [{"type": "parking_management_data", "location": location}],
            }

        except Exception as e:
            logging.error(f"❌ ParkingManagementWorker Error: {e}")
            return {
                "parking_situation": {},
                "summary": f"Parkraumanalyse fehlgeschlagen: {str(e)}",
                "confidence_score": 0.0,
                "error": str(e),
            }

    def _extract_parking_need(self, query: str) -> Dict[str, Any]:
        """Extrahiert Parkraum-Bedarf aus Query"""

        need = {"duration": "short_term", "vehicle_type": "car", "price_sensitivity": "medium", "special_requirements": []}

        # Parkdauer
        if any(word in query.lower() for word in ["dauerhaft", "monat", "jahr"]):
            need["duration"] = "long_term"
        elif any(word in query.lower() for word in ["kurz", "stunde", "einkau"]):
            need["duration"] = "short_term"

        # Fahrzeugtyp
        if any(word in query.lower() for word in ["lkw", "transporter"]):
            need["vehicle_type"] = "truck"
        elif any(word in query.lower() for word in ["motorrad", "roller"]):
            need["vehicle_type"] = "motorcycle"

        # Preissensibilität
        if any(word in query.lower() for word in ["teuer", "kostet", "günstig"]):
            need["price_sensitivity"] = "high"

        # Besondere Anforderungen
        if any(word in query.lower() for word in ["behinderung", "rollstuhl"]):
            need["special_requirements"].append("disabled_access")
        if any(word in query.lower() for word in ["elektro", "ladesäule"]):
            need["special_requirements"].append("ev_charging")
        if any(word in query.lower() for word in ["überdacht", "garage"]):
            need["special_requirements"].append("covered")

        return need

    async def _analyze_parking_situation(self, location: Dict) -> Dict[str, Any]:
        """Analysiert aktuelle Parksituation"""
        await asyncio.sleep(0.3)

        # Mock Parkraum-Analyse
        situation = {
            "availability": "limited",
            "parking_zones": [
                {
                    "zone": "Kurzparkzone (max. 2h)",
                    "radius_meters": 200,
                    "cost_per_hour": 2.50,
                    "availability_percent": 25,
                    "operating_hours": "Mo - Sa 8 - 18 Uhr",
                },
                {
                    "zone": "Bewohnerparkzone",
                    "radius_meters": 500,
                    "cost_resident_per_month": 30.0,
                    "cost_visitor_per_hour": 3.0,
                    "availability_percent": 60,
                },
            ],
            "parking_facilities": [
                {
                    "name": "Parkhaus Stadtmitte",
                    "distance_meters": 400,
                    "cost_per_hour": 1.80,
                    "daily_max": 12.0,
                    "capacity": 350,
                    "current_occupancy_percent": 85,
                    "features": ["überdacht", "videoüberwacht", "barrierefrei"],
                },
                {
                    "name": "P + R Bahnho",
                    "distance_meters": 1200,
                    "cost_per_day": 3.0,
                    "capacity": 150,
                    "current_occupancy_percent": 95,
                    "features": ["ÖPNV - Anschluss", "günstig für Pendler"],
                },
            ],
            "enforcement": {
                "fine_amount": 25.0,
                "control_frequency": "täglich",
                "payment_methods": ["Parkschein", "App", "SMS"],
            },
        }

        return situation

    async def _compare_parking_costs(self, location: Dict) -> Dict[str, Any]:
        """Vergleicht Parkkosten verschiedener Optionen"""
        await asyncio.sleep(0.2)

        comparison = {
            "cost_scenarios": {
                "1_hour_city_center": {"street_parking": 2.50, "parking_garage": 1.80, "cheapest_option": "parking_garage"},
                "4_hours_shopping": {
                    "street_parking": 10.0,
                    "parking_garage": 7.20,
                    "daily_ticket_garage": 12.0,
                    "cheapest_option": "parking_garage",
                },
                "full_day_work": {
                    "street_parking": "nicht_erlaubt",
                    "parking_garage": 12.0,
                    "park_and_ride": 3.0,
                    "monthly_pass_garage": 4.30,  # 130€ / Monat / 30 Tage
                    "cheapest_option": "park_and_ride",
                },
            },
            "annual_costs": {
                "daily_commuter": {
                    "parking_garage": 3120.0,  # 260 Tage * 12€
                    "monthly_pass": 1560.0,  # 12 * 130€
                    "park_and_ride": 780.0,  # 260 Tage * 3€
                    "public_transport": 849.0,  # Jahresticket
                },
                "recommendation": "Jahresticket ÖPNV + gelegentlich P+R",
            },
            "cost_trends": {
                "direction": "increasing",
                "rate_per_year": 5,  # Prozent
                "reasons": ["Verkehrswende - Politik", "Flächenknappheit", "Umweltkosten internalisieren"],
            },
        }

        return comparison

    async def _evaluate_parking_alternatives(self, location: Dict, need: Dict) -> List[Dict]:
        """Bewertet Parkraum-Alternativen"""
        await asyncio.sleep(0.3)

        alternatives = []

        # Grundlegende Alternativen
        alternatives.extend(
            [
                {
                    "alternative": "ÖPNV + Gehen",
                    "cost_savings_per_month": 120.0,
                    "pros": ["Keine Parkplatzsuche", "Umweltfreundlich", "Bewegung fördernd", "Kostengünstig"],
                    "cons": ["Wetterabhängig", "Zeitliche Bindung an Fahrplan", "Gepäck - Transport schwieriger"],
                    "feasibility": "high" if need["duration"] == "short_term" else "medium",
                },
                {
                    "alternative": "Fahrrad + sichere Abstellung",
                    "cost_savings_per_month": 100.0,
                    "pros": ["Flexibel und schnell", "Gesund", "Sehr günstig", "Umweltfreundlich"],
                    "cons": ["Wetterabhängig", "Diebstahlrisiko", "Begrenzte Reichweite"],
                    "feasibility": "high" if location.get("cycling_infrastructure", "poor") != "poor" else "medium",
                },
            ]
        )

        # Spezielle Alternativen für verschiedene Bedürfnisse
        if need["duration"] == "long_term":
            alternatives.append(
                {
                    "alternative": "Private Garage mieten",
                    "cost_per_month": 80.0,
                    "pros": ["Garantierter Parkplatz", "Witterungsschutz", "Höhere Sicherheit"],
                    "cons": ["Höhere Kosten", "Oft längere Wege", "Begrenzte Verfügbarkeit"],
                    "feasibility": "medium",
                }
            )

        if "ev_charging" in need["special_requirements"]:
            alternatives.append(
                {
                    "alternative": "Elektroauto - Carsharing",
                    "cost_per_usage": 15.0,
                    "pros": ["Kein eigener Parkplatz nötig", "Inklusive Laden", "Neue Modelle verfügbar"],
                    "cons": [
                        "Verfügbarkeit nicht garantiert",
                        "Voranmeldung erforderlich",
                        "Höhere Kosten bei häufiger Nutzung",
                    ],
                    "feasibility": "medium",
                }
            )

        return alternatives

    async def _check_parking_developments(self, location: Dict) -> List[Dict]:
        """Prüft zukünftige Parkraum-Entwicklungen"""
        await asyncio.sleep(0.2)

        developments = [
            {
                "development": "Ausweitung Bewohnerparkzonen",
                "timeline": "2025 - 2026",
                "impact": "Weniger kostenlose Parkplätze für Besucher",
                "new_cost": "3€ / Stunde für Nicht - Bewohner",
                "affected_area": "Innenstadtbereich erweitert",
            },
            {
                "development": "Neues Parkleitsystem",
                "timeline": "2025",
                "impact": "Bessere Information über freie Plätze",
                "features": ["Echzeit - Anzeige freier Plätze", "App - Integration", "Reservierung möglich"],
            },
            {
                "development": "E - Ladesäulen in Parkhäusern",
                "timeline": "2025 - 2027",
                "impact": "Mehr Optionen für Elektroautos",
                "target": "50% aller Parkplätze mit Lademöglichkeit",
            },
            {
                "development": "Parkplatz - Reduzierung für Radwege",
                "timeline": "2026",
                "impact": "10% weniger Straßenparkplätze",
                "compensation": "Mehr Park + Ride-Plätze am Stadtrand",
            },
        ]

        return developments


# Registrierung der Worker
TRAFFIC_WORKERS = {
    "traffic_management": TrafficManagementWorker,
    "public_transport": PublicTransportWorker,
    "parking_management": ParkingManagementWorker,
}

__all__ = ["TrafficManagementWorker", "PublicTransportWorker", "ParkingManagementWorker", "TRAFFIC_WORKERS"]
