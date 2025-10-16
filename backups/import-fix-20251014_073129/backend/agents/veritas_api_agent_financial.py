#!/usr/bin/env python3
"""
VERITAS Financial & Tax Workers
Spezialisierte Worker für Finanz- und Steueranfragen
"""
import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from covina_base import BaseWorker, ExternalAPIWorker

class TaxAssessmentWorker(ExternalAPIWorker):
    """Worker für Steuerveranlagung und Steuerbescheide"""
    
    def __init__(self):
        from covina_core import WorkerType
        super().__init__(WorkerType.TAX_ASSESSMENT, "https://api.finanzverwaltung.de/", cache_ttl=7200)  # 2 Stunden Cache
        self.tax_apis = {
            "federal_tax": "https://api.bundesfinanzministerium.de/",
            "state_tax": "https://api.landesfinanzverwaltung.de/",
            "municipal_tax": "https://api.municipality.de/steuern/"
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
        """Analysiert Steuerbescheide und Veranlagungen"""
        
        tax_inquiry = self._extract_tax_inquiry(metadata.normalized_query)
        location = self._extract_location(metadata.normalized_query)
        
        try:
            # Relevante Steuerarten identifizieren
            relevant_taxes = await self._identify_relevant_taxes(tax_inquiry, location)
            
            # Aktuelle Steuersätze ermitteln
            current_rates = await self._get_current_tax_rates(relevant_taxes, location)
            
            # Berechnungsgrundlagen analysieren
            calculation_basis = await self._analyze_calculation_basis(tax_inquiry, relevant_taxes)
            
            # Rechtsmittel-Optionen bewerten
            legal_options = self._evaluate_legal_remedies(tax_inquiry)
            
            return {
                "relevant_taxes": relevant_taxes,
                "current_rates": current_rates,
                "calculation_basis": calculation_basis,
                "legal_options": legal_options,
                "summary": f"Steueranalyse: {len(relevant_taxes)} relevante Steuerarten identifiziert",
                "confidence_score": 0.85,
                "sources": [{"type": "tax_law_database", "location": location}]
            }
            
        except Exception as e:
            logging.error(f"❌ TaxAssessmentWorker Error: {e}")
            return {
                "relevant_taxes": [],
                "summary": f"Steueranalyse fehlgeschlagen: {str(e)}",
                "confidence_score": 0.0,
                "error": str(e)
            }
    
    def _extract_tax_inquiry(self, query: str) -> Dict[str, Any]:
        """Extrahiert Steueranfrage-Details aus Query"""
        
        inquiry = {
            "tax_type": "unknown",
            "concern_type": "general",
            "amount_mentioned": None,
            "time_period": "current",
            "property_related": False
        }
        
        # Steuerart identifizieren
        if any(word in query.lower() for word in ["grundsteuer", "grund"]):
            inquiry["tax_type"] = "property_tax"
            inquiry["property_related"] = True
        elif any(word in query.lower() for word in ["gewerbesteuer", "gewerbe"]):
            inquiry["tax_type"] = "business_tax"
        elif any(word in query.lower() for word in ["einkommensteuer", "einkommen"]):
            inquiry["tax_type"] = "income_tax"
        elif any(word in query.lower() for word in ["umsatzsteuer", "mehrwertsteuer"]):
            inquiry["tax_type"] = "vat"
        elif any(word in query.lower() for word in ["erbschaftsteuer", "erbschaft"]):
            inquiry["tax_type"] = "inheritance_tax"
        
        # Anliegen-Typ
        if any(word in query.lower() for word in ["erhöhung", "gestiegen", "warum"]):
            inquiry["concern_type"] = "increase_explanation"
        elif any(word in query.lower() for word in ["widerspruch", "einspruch", "falsch"]):
            inquiry["concern_type"] = "objection"
        elif any(word in query.lower() for word in ["berechnung", "wie", "berechnungsgrundlage"]):
            inquiry["concern_type"] = "calculation_method"
        elif any(word in query.lower() for word in ["vergleich", "niedrig", "günstig"]):
            inquiry["concern_type"] = "comparison"
        
        # Beträge extrahieren
        import re
        amounts = re.findall(r'(\d+(?:\.\d+)?)\s*(?:€|euro|prozent|%)', query.lower())
        if amounts:
            inquiry["amount_mentioned"] = float(amounts[0])
        
        return inquiry
    
    async def _identify_relevant_taxes(self, inquiry: Dict, location: Dict) -> List[Dict]:
        """Identifiziert relevante Steuerarten"""
        await asyncio.sleep(0.3)
        
        taxes = []
        tax_type = inquiry.get("tax_type", "unknown")
        
        if tax_type == "property_tax":
            taxes.append({
                "type": "Grundsteuer A",
                "description": "Land- und forstwirtschaftliche Betriebe",
                "applicable": False,
                "reason": "Nur für landwirtschaftliche Nutzung"
            })
            taxes.append({
                "type": "Grundsteuer B",
                "description": "Grundstücke und Gebäude",
                "applicable": True,
                "calculation_factors": ["Grundstückswert", "Steuermesszahl", "Hebesatz"]
            })
        
        elif tax_type == "business_tax":
            taxes.append({
                "type": "Gewerbesteuer",
                "description": "Steuer auf Gewerbeertrag",
                "applicable": True,
                "calculation_factors": ["Gewerbeertrag", "Steuermesszahl", "Hebesatz"]
            })
        
        elif tax_type == "income_tax":
            taxes.extend([
                {
                    "type": "Einkommensteuer",
                    "description": "Bundessteuer auf Einkommen",
                    "applicable": True,
                    "progressive_rates": True
                },
                {
                    "type": "Solidaritätszuschlag",
                    "description": "Ergänzungssteuer zur Einkommensteuer",
                    "applicable": True,
                    "rate_percent": 5.5
                }
            ])
        
        return taxes
    
    async def _get_current_tax_rates(self, taxes: List, location: Dict) -> Dict[str, Any]:
        """Ermittelt aktuelle Steuersätze"""
        await asyncio.sleep(0.4)
        
        rates = {}
        municipality = location.get("name", "München")  # Fallback
        
        for tax in taxes:
            tax_type = tax["type"]
            
            if tax_type == "Grundsteuer B":
                rates[tax_type] = {
                    "grundsteuer_messzahl": 0.31,  # Promille des Einheitswerts
                    "hebesatz_municipality": 535,   # Beispiel München
                    "effective_rate_promille": 1.66,  # 0.31 * 535 / 100
                    "municipality": municipality,
                    "comparison_average": {
                        "bavaria": 520,
                        "germany": 459
                    }
                }
            
            elif tax_type == "Gewerbesteuer":
                rates[tax_type] = {
                    "grundbetrag_percent": 3.5,
                    "hebesatz_municipality": 490,  # Beispiel München
                    "effective_rate_percent": 17.15,  # 3.5 * 490 / 100
                    "municipality": municipality,
                    "comparison_average": {
                        "bavaria": 345,
                        "germany": 356
                    }
                }
            
            elif tax_type == "Einkommensteuer":
                rates[tax_type] = {
                    "type": "progressive",
                    "brackets": [
                        {"from": 0, "to": 10908, "rate": 0},
                        {"from": 10909, "to": 62810, "rate_formula": "progressive 14-42%"},
                        {"from": 62811, "to": 277826, "rate": 42},
                        {"from": 277827, "to": None, "rate": 45}
                    ],
                    "year": 2024
                }
        
        return rates
    
    async def _analyze_calculation_basis(self, inquiry: Dict, taxes: List) -> Dict[str, Any]:
        """Analysiert Berechnungsgrundlagen"""
        await asyncio.sleep(0.3)
        
        analysis = {}
        
        if inquiry.get("tax_type") == "property_tax":
            analysis["property_tax"] = {
                "current_system": "Einheitswert-basiert (bis 2024)",
                "new_system": "Bundesmodell ab 2025",
                "calculation_steps": [
                    "1. Grundstückswert ermitteln",
                    "2. Steuermesszahl anwenden (0,31‰)",
                    "3. Kommunalen Hebesatz anwenden",
                    "4. = Jährliche Grundsteuer"
                ],
                "reform_impact": {
                    "description": "Grundsteuerreform 2025",
                    "key_changes": [
                        "Neue Bewertungsverfahren",
                        "Aktuelle Bodenrichtwerte",
                        "Mögliche Verschiebungen der Steuerlast"
                    ],
                    "protection_clause": "Öffnungsklausel für Bundesländer"
                }
            }
        
        elif inquiry.get("tax_type") == "business_tax":
            analysis["business_tax"] = {
                "calculation_base": "Gewerbeertrag nach Einkommen- oder Körperschaftsteuer",
                "adjustments": [
                    "Hinzurechnungen (z.B. Mieten, Zinsen)",
                    "Kürzungen (z.B. Grundbesitz)",
                    "Freibetrag (24.500€ für Einzelunternehmen)"
                ],
                "municipal_variation": {
                    "description": "Hebesätze variieren stark zwischen Gemeinden",
                    "range": "200-900%",
                    "economic_factors": [
                        "Standortattraktivität",
                        "Infrastruktur-Bedarf",
                        "Kommunale Finanzsituation"
                    ]
                }
            }
        
        return analysis
    
    def _evaluate_legal_remedies(self, inquiry: Dict) -> List[Dict]:
        """Bewertet Rechtsmittel-Optionen"""
        
        remedies = []
        concern_type = inquiry.get("concern_type", "general")
        
        if concern_type == "objection":
            remedies.append({
                "remedy": "Einspruch gegen Steuerbescheid",
                "deadline": "1 Monat nach Bekanntgabe",
                "cost": "kostenfrei",
                "success_probability": "medium",
                "requirements": [
                    "Schriftlicher Einspruch",
                    "Begründung der Beanstandung",
                    "Belege für abweichende Bewertung"
                ],
                "process": [
                    "Einspruch bei zuständigem Finanzamt",
                    "Prüfung durch Verwaltung",
                    "Einspruchsentscheidung oder Abhilfe"
                ],
                "next_step_if_unsuccessful": "Klage vor Finanzgericht"
            })
        
        if concern_type == "increase_explanation":
            remedies.append({
                "remedy": "Informationsbegehren / Akteneinsicht",
                "deadline": "keine",
                "cost": "geringe Verwaltungsgebühren",
                "success_probability": "high",
                "requirements": [
                    "Berechtigtes Interesse darlegen",
                    "Antrag bei zuständiger Behörde"
                ],
                "expected_outcome": [
                    "Einsicht in Bewertungsunterlagen",
                    "Verständnis der Berechnungsgrundlage",
                    "Basis für möglichen Einspruch"
                ]
            })
        
        # Allgemeine Optionen
        remedies.append({
            "remedy": "Steuerberatung in Anspruch nehmen",
            "cost": "150-300€ pro Stunde",
            "benefits": [
                "Professionelle Bewertung der Situation",
                "Optimierung der Steuerstrategie",
                "Unterstützung bei Rechtsmitteln"
            ],
            "when_recommended": [
                "Komplexe Sachverhalte",
                "Hohe Steuerbeträge",
                "Wiederholte Probleme"
            ]
        })
        
        return remedies

class FundingOpportunitiesWorker(ExternalAPIWorker):
    """Worker für Förderungen und Finanzierungshilfen"""
    
    def __init__(self):
        from covina_core import WorkerType
        super().__init__(WorkerType.FUNDING_OPPORTUNITIES, "https://api.finanzverwaltung.de/", cache_ttl=3600)  # 1 Stunde Cache
        self.funding_apis = {
            "federal_funding": "https://api.foerderdatenbank.de/",
            "state_funding": "https://api.landesfoerderung.de/",
            "eu_funding": "https://api.ec.europa.eu/funding/",
            "kfw": "https://api.kfw.de/"
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
        """Identifiziert passende Förderungen"""
        
        funding_request = self._extract_funding_request(metadata.normalized_query)
        location = self._extract_location(metadata.normalized_query)
        
        try:
            # Passende Förderprogramme finden
            matching_programs = await self._find_matching_programs(funding_request, location)
            
            # Kombinationsmöglichkeiten prüfen
            combination_options = await self._analyze_combination_options(matching_programs)
            
            # Antragsverfahren bewerten
            application_processes = await self._evaluate_application_processes(matching_programs)
            
            # Erfolgschancen einschätzen
            success_assessment = self._assess_success_probability(funding_request, matching_programs)
            
            return {
                "matching_programs": matching_programs,
                "combination_options": combination_options,
                "application_processes": application_processes,
                "success_assessment": success_assessment,
                "summary": f"Förderungsanalyse: {len(matching_programs)} passende Programme gefunden",
                "confidence_score": 0.85,
                "sources": [{"type": "funding_database", "programs": len(matching_programs)}]
            }
            
        except Exception as e:
            logging.error(f"❌ FundingOpportunitiesWorker Error: {e}")
            return {
                "matching_programs": [],
                "summary": f"Förderungsanalyse fehlgeschlagen: {str(e)}",
                "confidence_score": 0.0,
                "error": str(e)
            }
    
    def _extract_funding_request(self, query: str) -> Dict[str, Any]:
        """Extrahiert Förderanfrage-Details aus Query"""
        
        request = {
            "purpose": "general",
            "building_type": None,
            "energy_related": False,
            "amount_range": None,
            "urgency": "normal",
            "applicant_type": "private"
        }
        
        # Zweck identifizieren
        if any(word in query.lower() for word in ["sanierung", "renovierung", "modernisierung"]):
            request["purpose"] = "renovation"
        elif any(word in query.lower() for word in ["neubau", "bauen", "errichten"]):
            request["purpose"] = "new_construction"
        elif any(word in query.lower() for word in ["energie", "heizung", "dämmung", "solar"]):
            request["purpose"] = "energy_efficiency"
            request["energy_related"] = True
        elif any(word in query.lower() for word in ["denkmal", "heritage", "historisch"]):
            request["purpose"] = "heritage_protection"
        elif any(word in query.lower() for word in ["barriere", "altersgerecht", "accessible"]):
            request["purpose"] = "accessibility"
        
        # Gebäudetyp
        if any(word in query.lower() for word in ["altbau", "alt"]):
            request["building_type"] = "historic_building"
        elif any(word in query.lower() for word in ["einfamilienhaus", "eigenheim"]):
            request["building_type"] = "single_family_home"
        elif any(word in query.lower() for word in ["mehrfamilienhaus", "vermietung"]):
            request["building_type"] = "multi_family_home"
        
        # Antragsteller
        if any(word in query.lower() for word in ["unternehmen", "firma", "gewerbe"]):
            request["applicant_type"] = "business"
        elif any(word in query.lower() for word in ["vermieter", "vermietung"]):
            request["applicant_type"] = "landlord"
        
        return request
    
    async def _find_matching_programs(self, request: Dict, location: Dict) -> List[Dict]:
        """Findet passende Förderprogramme"""
        await asyncio.sleep(0.5)
        
        programs = []
        purpose = request.get("purpose", "general")
        
        # KfW-Programme
        if purpose == "energy_efficiency":
            programs.extend([
                {
                    "name": "KfW 261 - Wohngebäude Kredit",
                    "provider": "KfW",
                    "type": "low_interest_loan",
                    "max_amount": 150000,
                    "interest_rate": 0.01,  # 0,01% bis 2,61%
                    "grant_component": 37500,  # max. Tilgungszuschuss
                    "requirements": [
                        "Effizienzhaus 85 Standard oder besser",
                        "Antrag vor Baubeginnen",
                        "Energieberater-Begleitung"
                    ],
                    "eligible_measures": [
                        "Dämmung von Wänden, Dach, Keller",
                        "Austausch Fenster und Türen",
                        "Erneuerung Heizungsanlage",
                        "Lüftungsanlage"
                    ],
                    "deadline": "Laufendes Programm",
                    "processing_time_weeks": 3
                },
                {
                    "name": "BAFA Einzelmaßnahmen",
                    "provider": "BAFA",
                    "type": "direct_grant",
                    "grant_rate": 15,  # Prozent der Kosten
                    "max_amount": 60000,
                    "requirements": [
                        "Mindestinvestition 2.000€",
                        "Fachbetrieb durchführung",
                        "Antrag vor Baubeginnen"
                    ],
                    "eligible_measures": [
                        "Wärmepumpen",
                        "Solarthermie",
                        "Biomasse-Heizungen",
                        "Dämmung Gebäudehülle"
                    ],
                    "processing_time_weeks": 8
                }
            ])
        
        if purpose == "heritage_protection":
            programs.append({
                "name": "Denkmalschutz-AfA",
                "provider": "Finanzamt",
                "type": "tax_deduction",
                "deduction_rate": 90,  # Prozent über 12 Jahre
                "requirements": [
                    "Denkmalgeschütztes Gebäude",
                    "Abstimmung mit Denkmalschutzbehörde",
                    "Eigennutzung oder Vermietung"
                ],
                "additional_info": "Alternative zur normalen AfA",
                "processing_time_weeks": 4
            })
        
        # Regionale Programme
        if location.get("state", "") == "Bayern":
            programs.append({
                "name": "10.000-Häuser-Programm Bayern",
                "provider": "Bayern",
                "type": "direct_grant",
                "grant_amount": 2000,  # Basis-Förderung
                "additional_grants": {
                    "heating_bonus": 1000,
                    "efficiency_bonus": 1000
                },
                "requirements": [
                    "Wohnsitz in Bayern",
                    "Heizungstausch auf erneuerbare Energien",
                    "Mindestinvestition 10.000€"
                ],
                "deadline": "31.12.2025",
                "budget_limited": True
            })
        
        # Kommunale Programme
        programs.append({
            "name": "Städtisches Fassadenprogramm",
            "provider": location.get("name", "Stadtverwaltung"),
            "type": "direct_grant",
            "grant_rate": 25,  # Prozent der Kosten
            "max_amount": 5000,
            "requirements": [
                "Gebäude in Altstadtbereich",
                "Verbesserung des Straßenbildes",
                "Vorlage Farbkonzept"
            ],
            "eligible_measures": [
                "Fassadenrenovierung",
                "Denkmalgerechte Fenster",
                "Historische Haustüren"
            ]
        })
        
        return programs
    
    async def _analyze_combination_options(self, programs: List) -> Dict[str, Any]:
        """Analysiert Kombinationsmöglichkeiten von Förderungen"""
        await asyncio.sleep(0.3)
        
        combinations = {
            "possible_combinations": [],
            "restrictions": [],
            "optimization_strategies": []
        }
        
        # Finde kompatible Kombinationen
        kfw_programs = [p for p in programs if p["provider"] == "KfW"]
        bafa_programs = [p for p in programs if p["provider"] == "BAFA"]
        regional_programs = [p for p in programs if p["provider"] not in ["KfW", "BAFA", "Finanzamt"]]
        
        if kfw_programs and bafa_programs:
            combinations["possible_combinations"].append({
                "combination": "KfW + BAFA",
                "description": "KfW-Kredit mit BAFA-Zuschuss kombinierbar",
                "total_funding_example": {
                    "investment": 50000,
                    "kfw_loan": 50000,
                    "kfw_grant": 12500,  # 25% bei EH 55
                    "bafa_grant": 7500,   # 15% für Einzelmaßnahmen
                    "net_cost": 30000
                },
                "restrictions": [
                    "Verschiedene Maßnahmen müssen abgegrenzt werden",
                    "Doppelförderung einzelner Komponenten ausgeschlossen"
                ]
            })
        
        if any(p["type"] == "tax_deduction" for p in programs):
            combinations["possible_combinations"].append({
                "combination": "Förderung + Steuervorteile",
                "description": "Zuschüsse mit steuerlichen Abschreibungen kombinieren",
                "note": "AfA-Sätze können sich durch Förderungen reduzieren"
            })
        
        # Beschränkungen
        combinations["restrictions"] = [
            "De-minimis-Regel bei Unternehmensförderung (200.000€ in 3 Jahren)",
            "Kumulierungsverbot bei EU-Beihilfen",
            "Budgetgrenzen bei regionalen Programmen"
        ]
        
        # Optimierungsstrategien
        combinations["optimization_strategies"] = [
            "Antragszeitpunkt koordinieren für beste Konditionen",
            "Maßnahmen phasenweise umsetzen für mehrfache Förderung",
            "Energieberatung für optimale Förderkombination nutzen"
        ]
        
        return combinations
    
    async def _evaluate_application_processes(self, programs: List) -> Dict[str, Any]:
        """Bewertet Antragsverfahren"""
        await asyncio.sleep(0.2)
        
        evaluation = {
            "complexity_ranking": [],
            "timing_requirements": {},
            "documentation_requirements": {},
            "professional_help_recommended": []
        }
        
        for program in programs:
            complexity = "low"
            if "Energieberater" in str(program.get("requirements", [])):
                complexity = "medium"
            if program.get("provider") == "EU":
                complexity = "high"
            
            evaluation["complexity_ranking"].append({
                "program": program["name"],
                "complexity": complexity,
                "estimated_effort_hours": {
                    "low": 5,
                    "medium": 15,
                    "high": 40
                }.get(complexity, 10)
            })
        
        # Timing-Anforderungen
        evaluation["timing_requirements"] = {
            "before_construction_start": [p["name"] for p in programs if "vor Baubeginnen" in str(p.get("requirements", []))],
            "deadlines": [(p["name"], p.get("deadline", "Laufend")) for p in programs if p.get("deadline")],
            "processing_times": [(p["name"], p.get("processing_time_weeks", 0)) for p in programs]
        }
        
        # Dokumentations-Anforderungen
        common_documents = [
            "Kostenvoranschläge von Fachbetrieben",
            "Energieberaterbericht (bei KfW)",
            "Grundbuchauszug",
            "Baugenehmigung oder Bauanzeige",
            "Nachweis Eigentumsrecht"
        ]
        
        evaluation["documentation_requirements"] = {
            "common_documents": common_documents,
            "program_specific": {
                "BAFA": ["Herstellerbescheinigungen", "Fachunternehmererklärung"],
                "Denkmalschutz": ["Stellungnahme Denkmalschutzbehörde"],
                "Regional": ["Bestätigung kommunale Förderrichtlinien"]
            }
        }
        
        return evaluation
    
    def _assess_success_probability(self, request: Dict, programs: List) -> Dict[str, Any]:
        """Schätzt Erfolgschancen ein"""
        
        assessment = {
            "overall_probability": "medium",
            "program_assessments": [],
            "success_factors": [],
            "risk_factors": []
        }
        
        for program in programs:
            probability = "medium"
            
            # Positive Faktoren
            if program.get("type") == "low_interest_loan":
                probability = "high"  # KfW-Kredite meist bewilligt
            if program.get("budget_limited"):
                probability = "medium"  # Abhängig von Antragszeitpunkt
            
            assessment["program_assessments"].append({
                "program": program["name"],
                "probability": probability,
                "key_factors": program.get("requirements", [])[:3]  # Top 3 Anforderungen
            })
        
        # Allgemeine Erfolgsfaktoren
        assessment["success_factors"] = [
            "Vollständige und korrekte Antragstellung",
            "Rechtzeitige Antragstellung vor Maßnahmenbeginn",
            "Qualifizierte Fachbetriebe beauftragen",
            "Energieberater bei komplexen Projekten einbeziehen",
            "Alternative Programme als Backup vorbereiten"
        ]
        
        assessment["risk_factors"] = [
            "Budgetausschöpfung bei begrenzten Programmen",
            "Änderung der Förderrichtlinien",
            "Unvollständige oder zu späte Antragstellung",
            "Nichteinhaltung technischer Mindestanforderungen"
        ]
        
        return assessment

class BusinessTaxOptimizationWorker(BaseWorker):
    """Worker für Gewerbesteuer-Optimierung und Standortvergleiche"""
    
    def __init__(self):
        from covina_core import WorkerType
        super().__init__(WorkerType.BUSINESS_TAX, cache_ttl=7200)  # 2 Stunden Cache
    
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
        """Optimiert Gewerbesteuer und vergleicht Standorte"""
        
        business_inquiry = self._extract_business_inquiry(metadata.normalized_query)
        location = self._extract_location(metadata.normalized_query)
        
        try:
            # Gewerbesteuer-Hebesätze vergleichen
            tax_comparison = await self._compare_business_tax_rates(location, business_inquiry)
            
            # Standortfaktoren bewerten
            location_factors = await self._evaluate_location_factors(location, business_inquiry)
            
            # Optimierungsstrategien entwickeln
            optimization_strategies = await self._develop_optimization_strategies(business_inquiry, tax_comparison)
            
            # Gesamt-Kosten-Nutzen-Analyse
            cost_benefit_analysis = self._perform_cost_benefit_analysis(tax_comparison, location_factors)
            
            return {
                "tax_comparison": tax_comparison,
                "location_factors": location_factors,
                "optimization_strategies": optimization_strategies,
                "cost_benefit_analysis": cost_benefit_analysis,
                "summary": f"Gewerbesteueranalyse: {len(tax_comparison.get('municipalities', []))} Standorte verglichen",
                "confidence_score": 0.9,
                "sources": [{"type": "business_tax_database", "locations": len(tax_comparison.get('municipalities', []))}]
            }
            
        except Exception as e:
            logging.error(f"❌ BusinessTaxOptimizationWorker Error: {e}")
            return {
                "tax_comparison": {},
                "summary": f"Gewerbesteueranalyse fehlgeschlagen: {str(e)}",
                "confidence_score": 0.0,
                "error": str(e)
            }
    
    def _extract_business_inquiry(self, query: str) -> Dict[str, Any]:
        """Extrahiert Unternehmens-Anfrage-Details"""
        
        inquiry = {
            "business_type": "general",
            "annual_profit": None,
            "employee_count": None,
            "location_flexibility": True,
            "priority_factors": []
        }
        
        # Unternehmenstyp
        if any(word in query.lower() for word in ["handwerk", "handwerker"]):
            inquiry["business_type"] = "craft"
        elif any(word in query.lower() for word in ["it", "software", "tech"]):
            inquiry["business_type"] = "technology"
        elif any(word in query.lower() for word in ["einzelhandel", "laden", "geschäft"]):
            inquiry["business_type"] = "retail"
        elif any(word in query.lower() for word in ["produktion", "fertigung"]):
            inquiry["business_type"] = "manufacturing"
        
        # Prioritäten
        if any(word in query.lower() for word in ["günstig", "niedrig", "steuer"]):
            inquiry["priority_factors"].append("low_taxes")
        if any(word in query.lower() for word in ["infrastruktur", "verkehr", "anbindung"]):
            inquiry["priority_factors"].append("infrastructure")
        if any(word in query.lower() for word in ["fachkräfte", "personal", "arbeitskräfte"]):
            inquiry["priority_factors"].append("workforce")
        
        return inquiry
    
    async def _compare_business_tax_rates(self, location: Dict, inquiry: Dict) -> Dict[str, Any]:
        """Vergleicht Gewerbesteuer-Hebesätze"""
        await asyncio.sleep(0.4)
        
        # Mock-Daten für Gewerbesteuer-Vergleich
        municipalities = [
            {
                "name": "München",
                "hebesatz": 490,
                "effective_rate_percent": 17.15,
                "state": "Bayern",
                "population": 1500000,
                "economic_strength": "sehr hoch",
                "annual_cost_example": {
                    "profit_50k": 8575,
                    "profit_100k": 17150,
                    "profit_500k": 85750
                }
            },
            {
                "name": "Augsburg",
                "hebesatz": 420,
                "effective_rate_percent": 14.7,
                "state": "Bayern",
                "population": 300000,
                "economic_strength": "hoch",
                "annual_cost_example": {
                    "profit_50k": 7350,
                    "profit_100k": 14700,
                    "profit_500k": 73500
                }
            },
            {
                "name": "Garching",
                "hebesatz": 240,
                "effective_rate_percent": 8.4,
                "state": "Bayern",
                "population": 18000,
                "economic_strength": "sehr hoch",
                "annual_cost_example": {
                    "profit_50k": 4200,
                    "profit_100k": 8400,
                    "profit_500k": 42000
                },
                "special_note": "Technologie-Standort, niedrige Hebesätze"
            }
        ]
        
        comparison = {
            "municipalities": municipalities,
            "ranking_by_tax_burden": sorted(municipalities, key=lambda x: x["hebesatz"]),
            "state_average": 345,
            "federal_average": 356,
            "potential_savings": {
                "best_vs_worst": {
                    "hebesatz_difference": 250,  # 490 - 240
                    "annual_savings_50k_profit": 4375,  # (17.15% - 8.4%) * 50k
                    "annual_savings_100k_profit": 8750
                }
            }
        }
        
        return comparison
    
    async def _evaluate_location_factors(self, location: Dict, inquiry: Dict) -> Dict[str, Any]:
        """Bewertet Standortfaktoren über Steuern hinaus"""
        await asyncio.sleep(0.3)
        
        factors = {
            "infrastructure": {
                "score": 8.5,  # 1-10
                "details": {
                    "public_transport": "excellent",
                    "road_access": "very_good",
                    "internet_broadband": "excellent",
                    "airports": "Munich Airport 45km"
                }
            },
            "workforce": {
                "score": 9.0,
                "details": {
                    "university_access": "TU München, LMU München",
                    "skilled_workers": "high availability",
                    "unemployment_rate": 2.1,
                    "avg_salary_level": "above national average"
                }
            },
            "business_environment": {
                "score": 8.0,
                "details": {
                    "startup_ecosystem": "very active",
                    "business_support": "extensive programs",
                    "regulatory_efficiency": "good",
                    "cluster_effects": inquiry.get("business_type") == "technology"
                }
            },
            "cost_of_living": {
                "score": 4.0,  # Niedriger = teurer
                "details": {
                    "office_rent_per_sqm": 25.0,
                    "residential_rent_index": 180,  # 100 = Bundesdurchschnitt
                    "employee_cost_factor": 1.15
                }
            },
            "quality_of_life": {
                "score": 9.5,
                "details": {
                    "cultural_offerings": "excellent",
                    "recreation": "Alps nearby",
                    "education": "top schools and universities",
                    "healthcare": "excellent"
                }
            }
        }
        
        # Gewichtung basierend auf Unternehmensprioritäten
        priorities = inquiry.get("priority_factors", [])
        weighted_score = 0
        
        if "low_taxes" in priorities:
            weighted_score += factors["business_environment"]["score"] * 0.4
        if "infrastructure" in priorities:
            weighted_score += factors["infrastructure"]["score"] * 0.4
        if "workforce" in priorities:
            weighted_score += factors["workforce"]["score"] * 0.4
        
        factors["overall_weighted_score"] = weighted_score / len(priorities) if priorities else 7.5
        
        return factors
    
    async def _develop_optimization_strategies(self, inquiry: Dict, tax_comparison: Dict) -> List[Dict]:
        """Entwickelt Optimierungsstrategien"""
        await asyncio.sleep(0.2)
        
        strategies = []
        
        # Standortwechsel-Strategie
        best_tax_location = min(tax_comparison["municipalities"], key=lambda x: x["hebesatz"])
        current_location = max(tax_comparison["municipalities"], key=lambda x: x["hebesatz"])  # Annahme: aktuell München
        
        strategies.append({
            "strategy": "Standortverlagerung",
            "description": f"Umzug von {current_location['name']} nach {best_tax_location['name']}",
            "tax_savings_annual": tax_comparison["potential_savings"]["best_vs_worst"]["annual_savings_100k_profit"],
            "implementation_effort": "high",
            "pros": [
                f"Jährliche Steuerersparnis: {tax_comparison['potential_savings']['best_vs_worst']['annual_savings_100k_profit']}€",
                "Niedrigere Betriebskosten möglich",
                "Weniger Verkehr und Stress"
            ],
            "cons": [
                "Umzugskosten",
                "Verlust etablierter Geschäftsbeziehungen",
                "Möglicherweise weniger Infrastruktur",
                "Mitarbeiter-Akzeptanz fraglich"
            ],
            "break_even_years": 2  # Abhängig von Umzugskosten
        })
        
        # Rechtsform-Optimierung
        strategies.append({
            "strategy": "Rechtsform-Optimierung",
            "description": "Prüfung optimaler Rechtsform für Steuerminimierung",
            "options": [
                {
                    "form": "GmbH",
                    "tax_burden": "Gewerbesteuer + Körperschaftsteuer",
                    "optimal_for": "Höhere Gewinne (>60.000€)"
                },
                {
                    "form": "Freiberufler",
                    "tax_burden": "Nur Einkommensteuer",
                    "optimal_for": "Beratung, IT-Services ohne Gewerbesteuer"
                }
            ],
            "implementation_effort": "medium",
            "professional_advice_required": True
        })
        
        # Verlagerung von Betriebsstätten
        strategies.append({
            "strategy": "Betriebsstätten-Aufteilung",
            "description": "Aufteilung auf mehrere Standorte mit niedrigeren Hebesätzen",
            "examples": [
                "Verwaltung in steueroptimierter Gemeinde",
                "Produktion am Hauptstandort",
                "Lager in günstigem Umland"
            ],
            "complexity": "high",
            "legal_considerations": [
                "Betriebsstättenabgrenzung beachten",
                "Verrechnungspreise dokumentieren",
                "Substanzerfordernis erfüllen"
            ]
        })
        
        return strategies
    
    def _perform_cost_benefit_analysis(self, tax_comparison: Dict, location_factors: Dict) -> Dict[str, Any]:
        """Führt Kosten-Nutzen-Analyse durch"""
        
        analysis = {
            "total_cost_calculation": {},
            "recommendation": {},
            "sensitivity_analysis": {}
        }
        
        # Beispiel-Berechnung für verschiedene Szenarien
        business_scenarios = [
            {"name": "Startup (50k Gewinn)", "annual_profit": 50000},
            {"name": "Mittelstand (200k Gewinn)", "annual_profit": 200000},
            {"name": "Großunternehmen (1M Gewinn)", "annual_profit": 1000000}
        ]
        
        for scenario in business_scenarios:
            profit = scenario["annual_profit"]
            
            scenario_costs = {}
            for municipality in tax_comparison["municipalities"]:
                # Gewerbesteuer berechnen
                taxable_profit = max(0, profit - 24500)  # Freibetrag
                annual_tax = taxable_profit * municipality["effective_rate_percent"] / 100
                
                # Weitere Standortkosten einschätzen
                location_cost_factor = {
                    "München": 1.2,
                    "Augsburg": 1.0,
                    "Garching": 1.1
                }.get(municipality["name"], 1.0)
                
                total_annual_cost = annual_tax + (profit * 0.1 * location_cost_factor)  # 10% Betriebskosten
                
                scenario_costs[municipality["name"]] = {
                    "gewerbesteuer": annual_tax,
                    "estimated_operating_costs": profit * 0.1 * location_cost_factor,
                    "total_cost": total_annual_cost
                }
            
            analysis["total_cost_calculation"][scenario["name"]] = scenario_costs
        
        # Empfehlung basierend auf verschiedenen Faktoren
        analysis["recommendation"] = {
            "for_startups": "Garching - niedrige Steuern, Tech-Cluster",
            "for_established_business": "München - beste Infrastruktur trotz höherer Steuern",
            "for_cost_sensitive": "Augsburg - guter Kompromiss aus Kosten und Infrastruktur",
            "general_advice": "Steuerersparnis gegen Standortvorteile abwägen"
        }
        
        return analysis

# Registrierung der Worker
FINANCIAL_WORKERS = {
    "tax_assessment": TaxAssessmentWorker,
    "funding_opportunities": FundingOpportunitiesWorker,
    "business_tax_optimization": BusinessTaxOptimizationWorker
}

__all__ = ["TaxAssessmentWorker", "FundingOpportunitiesWorker", "BusinessTaxOptimizationWorker", "FINANCIAL_WORKERS"]
