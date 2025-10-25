#!/usr/bin/env python3
"""
VERITAS Social Services & Citizen Services Workers
Spezialisierte Worker für Soziale Dienste und Bürgerdienste
"""
import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

# Import base classes from framework
try:
    from backend.agents.framework.base_agent import BaseAgent as BaseWorker
except ImportError:
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from backend.agents.framework.base_agent import BaseAgent as BaseWorker

# ExternalAPIWorker is same as BaseWorker for now
ExternalAPIWorker = BaseWorker

class SocialBenefitsWorker(ExternalAPIWorker):
    """Worker für Sozialleistungen und Anspruchsprüfung"""
    
    def __init__(self):
        from covina_core import WorkerType
        super().__init__(WorkerType.SOCIAL_BENEFITS, "https://api.sozialamt.de/", cache_ttl=3600)  # 1 Stunde Cache
        self.social_apis = {
            "federal_social": "https://api.arbeitsagentur.de/",
            "pension_insurance": "https://api.deutsche-rentenversicherung.de/",
            "health_insurance": "https://api.gkv-spitzenverband.de/",
            "family_benefits": "https://api.familienkasse.de/"
        }
    
    async def _process_internal(self, metadata, user_profile: Dict = None) -> Dict[str, Any]:
        """Analysiert Sozialleistungsansprüche"""
        
        benefit_inquiry = self._extract_benefit_inquiry(metadata.normalized_query)
        personal_situation = self._extract_personal_situation(metadata.normalized_query)
        
        try:
            # Anspruchsberechtigte Leistungen identifizieren
            eligible_benefits = await self._identify_eligible_benefits(benefit_inquiry, personal_situation)
            
            # Antragsverfahren analysieren
            application_processes = await self._analyze_application_processes(eligible_benefits)
            
            # Leistungshöhe berechnen
            benefit_calculations = await self._calculate_benefit_amounts(eligible_benefits, personal_situation)
            
            # Kombinationsmöglichkeiten prüfen
            combination_options = await self._check_benefit_combinations(eligible_benefits)
            
            return {
                "eligible_benefits": eligible_benefits,
                "application_processes": application_processes,
                "benefit_calculations": benefit_calculations,
                "combination_options": combination_options,
                "summary": f"Sozialleistungsanalyse: {len(eligible_benefits)} mögliche Leistungen identifiziert",
                "confidence_score": 0.85,
                "sources": [{"type": "social_benefits_database", "benefits_count": len(eligible_benefits)}]
            }
            
        except Exception as e:
            logging.error(f"❌ SocialBenefitsWorker Error: {e}")
            return {
                "eligible_benefits": [],
                "summary": f"Sozialleistungsanalyse fehlgeschlagen: {str(e)}",
                "confidence_score": 0.0,
                "error": str(e)
            }
    
    def _extract_benefit_inquiry(self, query: str) -> Dict[str, Any]:
        """Extrahiert Art der Sozialleistungsanfrage"""
        
        inquiry = {
            "benefit_type": "general",
            "life_situation": "stable",
            "urgency": "normal",
            "specific_concern": None
        }
        
        # Leistungsart identifizieren
        if any(word in query.lower() for word in ["arbeitslosengeld", "alg", "arbeitslos"]):
            inquiry["benefit_type"] = "unemployment_benefits"
        elif any(word in query.lower() for word in ["bürgergeld", "grundsicherung", "hartz"]):
            inquiry["benefit_type"] = "basic_security"
        elif any(word in query.lower() for word in ["kindergeld", "elterngeld", "familie"]):
            inquiry["benefit_type"] = "family_benefits"
        elif any(word in query.lower() for word in ["wohngeld", "miete", "wohnen"]):
            inquiry["benefit_type"] = "housing_allowance"
        elif any(word in query.lower() for word in ["rente", "pension", "alter"]):
            inquiry["benefit_type"] = "pension"
        elif any(word in query.lower() for word in ["behinderung", "pflege", "gesundheit"]):
            inquiry["benefit_type"] = "disability_care"
        
        # Lebenssituation
        if any(word in query.lower() for word in ["verloren", "gekündigt", "entlassen"]):
            inquiry["life_situation"] = "job_loss"
        elif any(word in query.lower() for word in ["schwanger", "baby", "geburt"]):
            inquiry["life_situation"] = "pregnancy_birth"
        elif any(word in query.lower() for word in ["krank", "unfall", "arbeitsunfähig"]):
            inquiry["life_situation"] = "illness_disability"
        elif any(word in query.lower() for word in ["trennung", "scheidung", "alleinerziehend"]):
            inquiry["life_situation"] = "separation"
        
        return inquiry
    
    def _extract_personal_situation(self, query: str) -> Dict[str, Any]:
        """Extrahiert persönliche Situation für Anspruchsprüfung"""
        
        situation = {
            "employment_status": "unknown",
            "family_status": "unknown",
            "children_count": 0,
            "housing_situation": "unknown",
            "income_level": "unknown",
            "age_group": "working_age"
        }
        
        # Beschäftigungsstatus
        if any(word in query.lower() for word in ["arbeitslos", "ohne arbeit"]):
            situation["employment_status"] = "unemployed"
        elif any(word in query.lower() for word in ["teilzeit", "minijob"]):
            situation["employment_status"] = "part_time"
        elif any(word in query.lower() for word in ["selbständig", "freiberufler"]):
            situation["employment_status"] = "self_employed"
        
        # Familienstatus
        if any(word in query.lower() for word in ["verheiratet", "ehe"]):
            situation["family_status"] = "married"
        elif any(word in query.lower() for word in ["alleinerziehend", "allein"]):
            situation["family_status"] = "single_parent"
        elif any(word in query.lower() for word in ["ledig", "single"]):
            situation["family_status"] = "single"
        
        # Kinder
        import re
        children_matches = re.findall(r'(\d+)\s*(?:kind|kinder)', query.lower())
        if children_matches:
            situation["children_count"] = int(children_matches[0])
        elif any(word in query.lower() for word in ["kind", "baby", "schwanger"]):
            situation["children_count"] = 1
        
        return situation
    
    async def _identify_eligible_benefits(self, inquiry: Dict, situation: Dict) -> List[Dict]:
        """Identifiziert anspruchsberechtigte Leistungen"""
        await asyncio.sleep(0.5)
        
        benefits = []
        benefit_type = inquiry.get("benefit_type", "general")
        employment = situation.get("employment_status", "unknown")
        
        # Arbeitslosengeld I
        if benefit_type == "unemployment_benefits" or employment == "unemployed":
            benefits.append({
                "name": "Arbeitslosengeld I",
                "provider": "Bundesagentur für Arbeit",
                "eligibility": {
                    "requirements": [
                        "Arbeitslosigkeit",
                        "Verfügbarkeit für Arbeitsvermittlung",
                        "12 Monate Beitragszahlung in letzten 2 Jahren"
                    ],
                    "duration_months": 12,  # Je nach Alter und Beitragsdauer
                    "percentage_of_last_income": 60,  # 67% mit Kind
                    "max_duration_extension": "bis 24 Monate bei Älteren"
                },
                "application": {
                    "where": "Arbeitsagentur",
                    "deadline": "spätestens 3 Monate nach Arbeitsende",
                    "required_documents": [
                        "Personalausweis",
                        "Arbeitsvertrag und Kündigung",
                        "Arbeitsbescheinigung",
                        "Lohnbescheinigungen"
                    ]
                }
            })
        
        # Bürgergeld (ALG II)
        if benefit_type in ["basic_security", "unemployment_benefits"] or inquiry.get("life_situation") == "job_loss":
            benefits.append({
                "name": "Bürgergeld",
                "provider": "Jobcenter",
                "eligibility": {
                    "requirements": [
                        "Hilfebedürftigkeit",
                        "Erwerbsfähigkeit (15-67 Jahre)",
                        "Gewöhnlicher Aufenthalt in Deutschland"
                    ],
                    "income_limit": "Bedarf nicht durch eigenes Einkommen/Vermögen deckbar",
                    "asset_limits": {
                        "basic_allowance": 15000,  # Euro pro Person
                        "additional_per_year": 750  # Pro Lebensjahr ab 18
                    }
                },
                "monthly_amounts_2025": {
                    "single_adult": 563,
                    "adult_in_partnership": 506,
                    "child_0_5": 357,
                    "child_6_13": 390,
                    "child_14_17": 471
                },
                "additional_benefits": [
                    "Übernahme Unterkunftskosten",
                    "Kranken- und Pflegeversicherung",
                    "Mehrbedarfe (Schwangerschaft, Alleinerziehung)"
                ]
            })
        
        # Kindergeld / Elterngeld
        if benefit_type == "family_benefits" or situation.get("children_count", 0) > 0:
            benefits.extend([
                {
                    "name": "Kindergeld",
                    "provider": "Familienkasse",
                    "eligibility": {
                        "requirements": [
                            "Kind unter 18 Jahren",
                            "Wohnsitz in Deutschland",
                            "Kindergeld-Berechtigung der Eltern"
                        ],
                        "extensions": "bis 25 bei Ausbildung/Studium"
                    },
                    "monthly_amount_2025": 250,  # Einheitlicher Betrag seit 2023
                    "duration": "bis zum 18. Lebensjahr (ggf. länger)"
                },
                {
                    "name": "Elterngeld",
                    "provider": "Elterngeldstelle",
                    "eligibility": {
                        "requirements": [
                            "Geburt eines Kindes ab 01.01.2007",
                            "Hauptbetreuung des Kindes",
                            "Wohnsitz in Deutschland"
                        ]
                    },
                    "calculation": {
                        "percentage_of_income": 67,  # 65% ab 1.240€
                        "minimum_amount": 300,
                        "maximum_amount": 1800
                    },
                    "duration_months": 14,  # Aufteilbar zwischen Eltern
                    "variants": ["Basiselterngeld", "ElterngeldPlus", "Partnerschaftsbonus"]
                }
            ])
        
        # Wohngeld
        if benefit_type == "housing_allowance" or any(word in inquiry.values() for word in ["miete", "wohnen"]):
            benefits.append({
                "name": "Wohngeld",
                "provider": "Wohngeldstelle der Gemeinde",
                "eligibility": {
                    "requirements": [
                        "Keine Sozialleistungen mit Unterkunftskosten",
                        "Eigenes Einkommen unter bestimmten Grenzen",
                        "Hauptwohnsitz in Deutschland"
                    ],
                    "income_limits": "je nach Haushaltsgröße und Mietstufe"
                },
                "calculation_factors": [
                    "Anzahl Haushaltsmitglieder",
                    "Gesamteinkommen des Haushalts",
                    "Höhe der Miete/Belastung",
                    "Mietstufe der Gemeinde"
                ],
                "reform_2025": {
                    "climate_component": "CO2-Komponente für klimafreundliches Wohnen",
                    "heating_allowance": "Heizkosten-Entlastung"
                }
            })
        
        return benefits
    
    async def _analyze_application_processes(self, benefits: List) -> Dict[str, Any]:
        """Analysiert Antragsverfahren"""
        await asyncio.sleep(0.3)
        
        processes = {
            "priority_order": [],
            "timeline": {},
            "common_documents": [],
            "tips": []
        }
        
        # Prioritätsreihenfolge bestimmen
        priority_mapping = {
            "Arbeitslosengeld I": 1,  # Zeitkritisch
            "Bürgergeld": 2,         # Grundsicherung
            "Wohngeld": 3,           # Ergänzend
            "Kindergeld": 4,         # Langfristig
            "Elterngeld": 5          # Zeitlich begrenzt
        }
        
        processes["priority_order"] = sorted(
            benefits, 
            key=lambda x: priority_mapping.get(x["name"], 10)
        )
        
        # Timeline erstellen
        for benefit in benefits:
            name = benefit["name"]
            if name == "Arbeitslosengeld I":
                processes["timeline"][name] = {
                    "apply_when": "Sofort nach Arbeitsplatzverlust",
                    "processing_time": "4-6 Wochen",
                    "first_payment": "meist rückwirkend"
                }
            elif name == "Bürgergeld":
                processes["timeline"][name] = {
                    "apply_when": "Bei Hilfebedürftigkeit",
                    "processing_time": "2-4 Wochen",
                    "first_payment": "ab Antragsmonat"
                }
            elif name == "Elterngeld":
                processes["timeline"][name] = {
                    "apply_when": "Nach Geburt, spätestens 3 Monate",
                    "processing_time": "6-8 Wochen",
                    "retroactive": "bis zu 3 Monate rückwirkend"
                }
        
        # Gemeinsame Dokumente
        processes["common_documents"] = [
            "Personalausweis oder Reisepass",
            "Meldebescheinigung",
            "Einkommensnachweise (Gehaltsabrechnungen)",
            "Kontoauszüge der letzten 3 Monate",
            "Mietvertrag und Mietbescheinigung",
            "Bei Kindern: Geburtsurkunden"
        ]
        
        # Praktische Tipps
        processes["tips"] = [
            "Anträge so früh wie möglich stellen",
            "Kopien aller Dokumente für eigene Unterlagen",
            "Bei Ablehnungen: Widerspruchsfrist (1 Monat) beachten",
            "Beratungsangebote nutzen (Sozialverbände, Gewerkschaften)",
            "Änderungen sofort melden (Einkommen, Wohnsituation)"
        ]
        
        return processes
    
    async def _calculate_benefit_amounts(self, benefits: List, situation: Dict) -> Dict[str, Any]:
        """Berechnet voraussichtliche Leistungshöhen"""
        await asyncio.sleep(0.4)
        
        calculations = {}
        family_status = situation.get("family_status", "single")
        children_count = situation.get("children_count", 0)
        
        for benefit in benefits:
            name = benefit["name"]
            
            if name == "Bürgergeld":
                monthly_amount = benefit["monthly_amounts_2025"]["single_adult"]
                
                if family_status == "married":
                    monthly_amount += benefit["monthly_amounts_2025"]["adult_in_partnership"]
                
                # Kinder hinzufügen
                for i in range(children_count):
                    if i < 1:  # Erstes Kind unter 6
                        monthly_amount += benefit["monthly_amounts_2025"]["child_0_5"]
                    else:  # Weitere Kinder
                        monthly_amount += benefit["monthly_amounts_2025"]["child_6_13"]
                
                calculations[name] = {
                    "monthly_basic_amount": monthly_amount,
                    "additional_costs": {
                        "housing": "actual costs up to reasonable limit",
                        "heating": "actual costs",
                        "health_insurance": "fully covered"
                    },
                    "potential_supplements": [
                        "Mehrbedarf Schwangerschaft: +17%",
                        "Mehrbedarf Alleinerziehung: +12-60%",
                        "Einmalige Bedarfe: Erstausstattung, Klassenfahrten"
                    ]
                }
            
            elif name == "Kindergeld":
                total_kindergeld = benefit["monthly_amount_2025"] * children_count
                calculations[name] = {
                    "monthly_amount": total_kindergeld,
                    "annual_amount": total_kindergeld * 12,
                    "duration": "until 18 (potentially until 25)"
                }
            
            elif name == "Wohngeld":
                # Vereinfachte Berechnung
                household_size = 1 + (1 if family_status == "married" else 0) + children_count
                estimated_amount = min(300, household_size * 80)  # Grobe Schätzung
                
                calculations[name] = {
                    "estimated_monthly": estimated_amount,
                    "depends_on": [
                        "Genaue Miethöhe",
                        "Haushaltseinkommen",
                        "Mietstufe der Gemeinde"
                    ],
                    "note": "Genaue Berechnung nur mit allen Daten möglich"
                }
        
        return calculations
    
    async def _check_benefit_combinations(self, benefits: List) -> Dict[str, Any]:
        """Prüft Kombinationsmöglichkeiten von Leistungen"""
        await asyncio.sleep(0.2)
        
        combinations = {
            "allowed_combinations": [],
            "exclusions": [],
            "optimization_tips": []
        }
        
        benefit_names = [b["name"] for b in benefits]
        
        # Erlaubte Kombinationen
        if "Kindergeld" in benefit_names:
            combinations["allowed_combinations"].append({
                "benefits": ["Kindergeld", "Bürgergeld"],
                "note": "Kindergeld wird nicht als Einkommen angerechnet"
            })
            combinations["allowed_combinations"].append({
                "benefits": ["Kindergeld", "Wohngeld"],
                "note": "Kindergeld zählt als Einkommen bei Wohngeld"
            })
        
        if "Elterngeld" in benefit_names:
            combinations["allowed_combinations"].append({
                "benefits": ["Elterngeld", "Kindergeld"],
                "note": "Vollständig kombinierbar"
            })
        
        # Ausschlüsse
        if "Arbeitslosengeld I" in benefit_names and "Bürgergeld" in benefit_names:
            combinations["exclusions"].append({
                "benefits": ["Arbeitslosengeld I", "Bürgergeld"],
                "reason": "ALG I hat Vorrang vor Bürgergeld",
                "exception": "Aufstockung bei niedrigem ALG I möglich"
            })
        
        if "Wohngeld" in benefit_names and "Bürgergeld" in benefit_names:
            combinations["exclusions"].append({
                "benefits": ["Wohngeld", "Bürgergeld"],
                "reason": "Bürgergeld enthält bereits Unterkunftskosten",
                "note": "Wohngeld nur bei Ausschluss von Bürgergeld"
            })
        
        # Optimierung
        combinations["optimization_tips"] = [
            "Bei niedrigem ALG I: Aufstockung durch Bürgergeld prüfen",
            "Wohngeld vs. Bürgergeld rechnen: Was ist günstiger?",
            "Elterngeld-Varianten vergleichen (Basis vs. Plus)",
            "Zeitliche Abfolge planen (z.B. ALG I → Bürgergeld)",
            "Freibeträge optimal nutzen (Erwerbstätigkeit, Elterngeld)"
        ]
        
        return combinations

class CitizenServicesWorker(BaseWorker):
    """Worker für allgemeine Bürgerdienste und Verwaltungsverfahren"""
    
    def __init__(self):
        from covina_core import WorkerType
        super().__init__(WorkerType.CITIZEN_SERVICES, cache_ttl=3600)  # 1 Stunde Cache
    
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
        """Bearbeitet Bürgerdienst-Anfragen"""
        
        service_request = self._extract_service_request(metadata.normalized_query)
        location = self._extract_location(metadata.normalized_query)
        
        try:
            # Zuständige Behörde identifizieren
            responsible_authority = await self._identify_responsible_authority(service_request, location)
            
            # Verfahrensschritte analysieren
            process_steps = await self._analyze_process_steps(service_request)
            
            # Benötigte Unterlagen ermitteln
            required_documents = await self._determine_required_documents(service_request)
            
            # Kosten und Gebühren berechnen
            costs_and_fees = await self._calculate_costs_and_fees(service_request, location)
            
            return {
                "responsible_authority": responsible_authority,
                "process_steps": process_steps,
                "required_documents": required_documents,
                "costs_and_fees": costs_and_fees,
                "summary": f"Bürgerdienst-Analyse: {service_request['service_type']} bei {responsible_authority.get('name', 'Behörde')}",
                "confidence_score": 0.9,
                "sources": [{"type": "administrative_database", "authority": responsible_authority.get("name")}]
            }
            
        except Exception as e:
            logging.error(f"❌ CitizenServicesWorker Error: {e}")
            return {
                "responsible_authority": {},
                "summary": f"Bürgerdienst-Analyse fehlgeschlagen: {str(e)}",
                "confidence_score": 0.0,
                "error": str(e)
            }
    
    def _extract_service_request(self, query: str) -> Dict[str, Any]:
        """Extrahiert Art des Bürgerdienst-Anliegens"""
        
        request = {
            "service_type": "general_inquiry",
            "document_type": None,
            "life_event": None,
            "urgency": "normal",
            "online_possible": False
        }
        
        # Service-Typ identifizieren
        if any(word in query.lower() for word in ["personalausweis", "ausweis", "id"]):
            request["service_type"] = "id_card"
            request["document_type"] = "personalausweis"
            request["online_possible"] = True
        elif any(word in query.lower() for word in ["reisepass", "pass"]):
            request["service_type"] = "passport"
            request["document_type"] = "reisepass"
        elif any(word in query.lower() for word in ["führerschein", "fahrerlaubnis"]):
            request["service_type"] = "drivers_license"
            request["document_type"] = "führerschein"
        elif any(word in query.lower() for word in ["anmeldung", "ummeldung", "abmeldung"]):
            request["service_type"] = "residence_registration"
            request["online_possible"] = True
        elif any(word in query.lower() for word in ["geburtsurkunde", "geburt"]):
            request["service_type"] = "birth_certificate"
            request["document_type"] = "geburtsurkunde"
        elif any(word in query.lower() for word in ["heirat", "eheschließung", "hochzeit"]):
            request["service_type"] = "marriage"
            request["life_event"] = "marriage"
        elif any(word in query.lower() for word in ["kfz", "auto", "zulassung", "fahrzeug"]):
            request["service_type"] = "vehicle_registration"
        elif any(word in query.lower() for word in ["gewerbe", "gewerbeanmeldung", "selbständig"]):
            request["service_type"] = "business_registration"
        
        # Dringlichkeit
        if any(word in query.lower() for word in ["dringend", "schnell", "express", "eilig"]):
            request["urgency"] = "urgent"
        elif any(word in query.lower() for word in ["verloren", "gestohlen", "verlust"]):
            request["urgency"] = "urgent"
            request["life_event"] = "document_loss"
        
        return request
    
    async def _identify_responsible_authority(self, request: Dict, location: Dict) -> Dict[str, Any]:
        """Identifiziert zuständige Behörde"""
        await asyncio.sleep(0.3)
        
        service_type = request.get("service_type", "general_inquiry")
        city = location.get("name", "München")
        
        authority_mapping = {
            "id_card": {
                "name": f"Bürgerbüro {city}",
                "type": "municipal",
                "department": "Bürgerservice",
                "address": f"Hauptstraße 1, {city}",
                "opening_hours": {
                    "monday_friday": "08:00-16:00",
                    "saturday": "09:00-12:00 (nur Notfälle)"
                },
                "online_services": True,
                "appointment_required": True
            },
            "passport": {
                "name": f"Bürgerbüro {city}",
                "type": "municipal",
                "department": "Passstelle",
                "address": f"Hauptstraße 1, {city}",
                "opening_hours": {
                    "monday_friday": "08:00-16:00",
                    "thursday": "08:00-18:00"
                },
                "appointment_required": True,
                "express_service": True
            },
            "drivers_license": {
                "name": f"Führerscheinstelle {city}",
                "type": "municipal_or_district",
                "department": "Straßenverkehrsamt",
                "address": f"Verkehrsstraße 10, {city}",
                "opening_hours": {
                    "monday_wednesday_friday": "08:00-12:00",
                    "tuesday_thursday": "08:00-16:00"
                },
                "appointment_required": True
            },
            "residence_registration": {
                "name": f"Einwohnermeldeamt {city}",
                "type": "municipal",
                "department": "Meldestelle",
                "address": f"Rathaus {city}",
                "online_services": True,
                "deadline_days": 14,  # Anmeldefrist
                "appointment_required": False
            },
            "vehicle_registration": {
                "name": f"Kfz-Zulassungsstelle {city}",
                "type": "district",
                "department": "Straßenverkehrsamt",
                "address": f"Zulassungsstraße 5, {city}",
                "opening_hours": {
                    "monday_friday": "07:30-15:00",
                    "thursday": "07:30-17:00"
                },
                "online_services": "partial",
                "appointment_recommended": True
            },
            "business_registration": {
                "name": f"Gewerbeamt {city}",
                "type": "municipal",
                "department": "Wirtschaftsförderung",
                "address": f"Wirtschaftsstraße 1, {city}",
                "online_services": True,
                "processing_time_days": 14
            }
        }
        
        authority = authority_mapping.get(service_type, {
            "name": f"Bürgerbüro {city}",
            "type": "municipal",
            "note": "Allgemeine Auskunft - genaue Zuständigkeit wird dort geklärt"
        })
        
        # Kontaktinformationen hinzufügen
        authority.update({
            "phone": f"+49-89-{city.lower()[:3]}-0",
            "email": f"buergerservice@{city.lower()}.de",
            "website": f"https://www.{city.lower()}.de",
            "accessibility": "Barrierefrei zugänglich"
        })
        
        return authority
    
    async def _analyze_process_steps(self, request: Dict) -> List[Dict]:
        """Analysiert Verfahrensschritte"""
        await asyncio.sleep(0.4)
        
        service_type = request.get("service_type", "general_inquiry")
        
        process_mappings = {
            "id_card": [
                {
                    "step": 1,
                    "title": "Termin vereinbaren",
                    "description": "Online oder telefonisch Termin buchen",
                    "duration": "5 Minuten",
                    "can_be_done_online": True
                },
                {
                    "step": 2,
                    "title": "Unterlagen vorbereiten",
                    "description": "Alle erforderlichen Dokumente zusammenstellen",
                    "duration": "30 Minuten",
                    "important_notes": ["Aktuelles Passfoto mitbringen", "Alter Ausweis zur Ungültigmachung"]
                },
                {
                    "step": 3,
                    "title": "Behördentermin wahrnehmen",
                    "description": "Persönlich vor Ort erscheinen für Antragstellung",
                    "duration": "20-30 Minuten",
                    "what_happens": ["Identitätsprüfung", "Fingerabdrücke nehmen", "Unterschrift leisten"]
                },
                {
                    "step": 4,
                    "title": "Abholung oder Zustellung",
                    "description": "Ausweis nach 3-4 Wochen abholen",
                    "duration": "10 Minuten",
                    "alternatives": ["Abholung vor Ort", "Zustellung per Post (gegen Aufpreis)"]
                }
            ],
            "residence_registration": [
                {
                    "step": 1,
                    "title": "Innerhalb von 14 Tagen anmelden",
                    "description": "Gesetzliche Frist nach Einzug beachten",
                    "legal_requirement": True,
                    "penalty_if_late": "Bußgeld bis 1.000€"
                },
                {
                    "step": 2,
                    "title": "Online-Anmeldung oder persönlich",
                    "description": "Wahl zwischen digitalem Service oder Behördengang",
                    "recommendation": "Online ist meist schneller"
                },
                {
                    "step": 3,
                    "title": "Meldebescheinigung erhalten",
                    "description": "Bestätigung der Anmeldung für andere Zwecke",
                    "uses": ["Bankkonto eröffnen", "Anmeldung bei Versicherungen", "Arbeitsplatz"]
                }
            ],
            "business_registration": [
                {
                    "step": 1,
                    "title": "Gewerbeanmeldung ausfüllen",
                    "description": "Formular online oder vor Ort ausfüllen",
                    "duration": "30 Minuten",
                    "form": "Gewerbe-Anmeldung nach § 14 GewO"
                },
                {
                    "step": 2,
                    "title": "Automatische Weiterleitung",
                    "description": "Daten werden an andere Behörden übermittelt",
                    "affected_authorities": ["Finanzamt", "IHK/HWK", "Berufsgenossenschaft", "Statistisches Amt"]
                },
                {
                    "step": 3,
                    "title": "Weitere Anmeldungen bearbeiten",
                    "description": "Reaktion auf Zuschriften der Behörden",
                    "typical_followups": ["Steuernummer beantragen", "IHK-Beitrag", "Unfallversicherung"]
                }
            ]
        }
        
        return process_mappings.get(service_type, [
            {
                "step": 1,
                "title": "Zuständigkeit klären",
                "description": "Bei der Gemeindeverwaltung nachfragen"
            }
        ])
    
    async def _determine_required_documents(self, request: Dict) -> Dict[str, Any]:
        """Ermittelt benötigte Unterlagen"""
        await asyncio.sleep(0.3)
        
        service_type = request.get("service_type", "general_inquiry")
        
        document_requirements = {
            "id_card": {
                "mandatory": [
                    "Aktueller Personalausweis (zur Ungültigmachung)",
                    "Biometrisches Passfoto (35x45mm, nicht älter als 6 Monate)",
                    "Bei Minderjährigen: Zustimmung beider Elternteile"
                ],
                "optional": [
                    "Meldebescheinigung (falls Adresse nicht aktuell)"
                ],
                "cost_of_photo": "8-15€ beim Fotografen",
                "photo_requirements": [
                    "Biometrisch nach ICAO-Standards",
                    "Neutral frontaler Blick",
                    "Geschlossener Mund",
                    "Heller, gleichmäßiger Hintergrund"
                ]
            },
            "passport": {
                "mandatory": [
                    "Personalausweis",
                    "Biometrisches Passfoto (35x45mm)",
                    "Bei Minderjährigen: Geburtsurkunde und Zustimmung beider Eltern"
                ],
                "express_service": {
                    "available": True,
                    "additional_cost": 32,
                    "processing_time": "2-4 Werktage statt 3-4 Wochen"
                }
            },
            "residence_registration": {
                "mandatory": [
                    "Personalausweis oder Reisepass",
                    "Wohnungsgeberbestätigung (vom Vermieter)",
                    "Bei Familie: Dokumente aller Familienmitglieder"
                ],
                "digital_alternative": [
                    "Online-Anmeldung mit elektronischem Personalausweis",
                    "Wohnungsgeberbestätigung als PDF-Upload"
                ]
            },
            "vehicle_registration": {
                "mandatory": [
                    "Fahrzeugbrief (Zulassungsbescheinigung Teil II)",
                    "Fahrzeugschein (Zulassungsbescheinigung Teil I)",
                    "gültige HU/AU-Bescheinigung",
                    "EVB-Nummer der Kfz-Versicherung",
                    "Personalausweis",
                    "SEPA-Lastschriftmandat für Kfz-Steuer"
                ],
                "for_new_cars": [
                    "EG-Übereinstimmungsbescheinigung (CoC)",
                    "Rechnung des Händlers"
                ],
                "for_used_cars": [
                    "Fahrzeugbrief mit Verkäufer-Unterschrift",
                    "Kaufvertrag"
                ]
            },
            "business_registration": {
                "mandatory": [
                    "Personalausweis",
                    "Bei bestimmten Gewerben: Qualifikationsnachweise",
                    "Bei Unternehmen: Gesellschaftsvertrag/Handelsregisterauszug"
                ],
                "qualification_required_for": [
                    "Handwerk (Meisterbrief oder Ausnahmebewilligung)",
                    "Gastronomie (Gaststättenerlaubnis)",
                    "Personenbeförderung (Führerschein entsprechender Klasse)"
                ]
            }
        }
        
        requirements = document_requirements.get(service_type, {
            "mandatory": ["Personalausweis"],
            "note": "Genaue Anforderungen bei zuständiger Behörde erfragen"
        })
        
        return requirements
    
    async def _calculate_costs_and_fees(self, request: Dict, location: Dict) -> Dict[str, Any]:
        """Berechnet Kosten und Gebühren"""
        await asyncio.sleep(0.2)
        
        service_type = request.get("service_type", "general_inquiry")
        urgency = request.get("urgency", "normal")
        
        fee_structure = {
            "id_card": {
                "standard_fee": 37.0,  # Euro, gültig ab 2025
                "under_24": 22.50,     # Ermäßigt für unter 24-Jährige
                "express_surcharge": 32.0,
                "postal_delivery": 5.90,
                "validity_years": 10,
                "cost_per_year": 3.70
            },
            "passport": {
                "standard_fee": 70.0,
                "under_24": 37.50,
                "express_surcharge": 32.0,
                "pages_32": 70.0,     # Standard
                "pages_48": 82.0,     # Mehr Seiten
                "validity_years": 10,
                "cost_per_year": 7.0
            },
            "residence_registration": {
                "standard_fee": 0.0,  # Meist kostenlos
                "certificate_copy": 8.0,
                "multiple_certificates": 8.0,  # pro weiteres Exemplar
                "online_convenience": "kostenlos"
            },
            "vehicle_registration": {
                "new_registration": 26.30,
                "re_registration": 26.30,
                "license_plate": {
                    "standard": 10.20,
                    "seasonal": 15.00,
                    "custom_plate": 12.80,
                    "electric_e_plate": 10.20
                },
                "additional_costs": {
                    "tüv_inspection": 120.0,  # ca., je nach Prüfstelle
                    "insurance_registration": 0.0,
                    "kfz_tax": "depends on vehicle"
                }
            },
            "business_registration": {
                "standard_fee": 20.0,
                "copy_certificate": 10.0,
                "modification": 15.0,
                "deregistration": 20.0,
                "additional_notifications": {
                    "ihk_notification": 0.0,  # automatisch
                    "tax_office_notification": 0.0  # automatisch
                }
            }
        }
        
        base_costs = fee_structure.get(service_type, {"standard_fee": 0.0})
        
        # Gesamtkosten berechnen
        total_cost = base_costs.get("standard_fee", 0.0)
        
        if urgency == "urgent" and "express_surcharge" in base_costs:
            total_cost += base_costs["express_surcharge"]
        
        cost_breakdown = {
            "base_fee": base_costs.get("standard_fee", 0.0),
            "total_cost": total_cost,
            "payment_methods": ["Bargeld", "EC-Karte", "teilweise Kreditkarte"],
            "cost_breakdown": base_costs,
            "money_saving_tips": []
        }
        
        # Sparmöglichkeiten
        if service_type == "id_card" and "under_24" in base_costs:
            cost_breakdown["money_saving_tips"].append(
                f"Unter 24 Jahren nur {base_costs['under_24']}€ statt {base_costs['standard_fee']}€"
            )
        
        if service_type in ["id_card", "passport"]:
            cost_breakdown["money_saving_tips"].extend([
                "Passfoto selbst machen (mit App) statt beim Fotografen",
                f"Gültigkeitsdauer {base_costs.get('validity_years', 10)} Jahre beachten"
            ])
        
        return cost_breakdown

class HealthInsuranceWorker(ExternalAPIWorker):
    """Worker für Krankenversicherungs- und Gesundheitssystem-Anfragen"""
    
    def __init__(self):
        from covina_core import WorkerType
        super().__init__(WorkerType.HEALTH_INSURANCE, "https://api.sozialamt.de/", cache_ttl=3600)  # 1 Stunde Cache
        self.health_apis = {
            "gkv_central": "https://api.gkv-spitzenverband.de/",
            "insurance_finder": "https://api.krankenkassen.de/",
            "service_portal": "https://api.gesundheit.gv.at/"
        }
    
    async def _process_internal(self, metadata, user_profile: Dict = None) -> Dict[str, Any]:
        """Bearbeitet Krankenversicherungsanfragen"""
        
        health_inquiry = self._extract_health_inquiry(metadata.normalized_query)
        personal_situation = self._extract_personal_situation(metadata.normalized_query)
        
        try:
            # Passende Krankenversicherung finden
            suitable_insurances = await self._find_suitable_insurances(health_inquiry, personal_situation)
            
            # Leistungsvergleich durchführen
            benefit_comparison = await self._compare_benefits(suitable_insurances, health_inquiry)
            
            # Wechselmöglichkeiten prüfen
            switching_options = await self._analyze_switching_options(personal_situation)
            
            # Kostenanalyse erstellen
            cost_analysis = await self._perform_cost_analysis(suitable_insurances, personal_situation)
            
            return {
                "suitable_insurances": suitable_insurances,
                "benefit_comparison": benefit_comparison,
                "switching_options": switching_options,
                "cost_analysis": cost_analysis,
                "summary": f"Krankenversicherungsanalyse: {len(suitable_insurances)} passende Optionen gefunden",
                "confidence_score": 0.8,
                "sources": [{"type": "health_insurance_database", "options": len(suitable_insurances)}]
            }
            
        except Exception as e:
            logging.error(f"❌ HealthInsuranceWorker Error: {e}")
            return {
                "suitable_insurances": [],
                "summary": f"Krankenversicherungsanalyse fehlgeschlagen: {str(e)}",
                "confidence_score": 0.0,
                "error": str(e)
            }
    
    def _extract_health_inquiry(self, query: str) -> Dict[str, Any]:
        """Extrahiert Gesundheitsversicherungs-Anfrage"""
        
        inquiry = {
            "inquiry_type": "general",
            "specific_need": None,
            "budget_concern": False,
            "service_priority": "standard"
        }
        
        # Anfrage-Typ
        if any(word in query.lower() for word in ["wechseln", "wechsel", "kündigen"]):
            inquiry["inquiry_type"] = "switching"
        elif any(word in query.lower() for word in ["vergleich", "vergleichen", "unterschied"]):
            inquiry["inquiry_type"] = "comparison"
        elif any(word in query.lower() for word in ["anmelden", "versichern", "neu"]):
            inquiry["inquiry_type"] = "enrollment"
        elif any(word in query.lower() for word in ["leistung", "kosten", "rechnung"]):
            inquiry["inquiry_type"] = "benefits_costs"
        
        # Spezifische Bedürfnisse
        if any(word in query.lower() for word in ["zahn", "dental", "zahnersatz"]):
            inquiry["specific_need"] = "dental"
        elif any(word in query.lower() for word in ["brille", "sehhilfe", "optik"]):
            inquiry["specific_need"] = "vision"
        elif any(word in query.lower() for word in ["alternative", "homöopathie", "naturheilkunde"]):
            inquiry["specific_need"] = "alternative_medicine"
        elif any(word in query.lower() for word in ["ausland", "reise", "travel"]):
            inquiry["specific_need"] = "travel_coverage"
        
        # Budget-Bewusstsein
        if any(word in query.lower() for word in ["günstig", "billig", "preiswert", "sparen"]):
            inquiry["budget_concern"] = True
        elif any(word in query.lower() for word in ["premium", "beste", "vollschutz"]):
            inquiry["service_priority"] = "premium"
        
        return inquiry
    
    async def _find_suitable_insurances(self, inquiry: Dict, situation: Dict) -> List[Dict]:
        """Findet passende Krankenversicherungen"""
        await asyncio.sleep(0.5)
        
        insurances = []
        employment = situation.get("employment_status", "employed")
        
        # Gesetzliche Krankenversicherungen
        if employment != "self_employed" or inquiry.get("budget_concern"):
            gkv_options = [
                {
                    "name": "AOK Bayern",
                    "type": "GKV",
                    "additional_rate": 1.7,  # Zusatzbeitrag 2025
                    "total_rate": 16.2,      # 14.6% + 1.7% - 0.1% Ermäßigung
                    "members": 4500000,
                    "customer_satisfaction": 4.2,  # 1-5 Skala
                    "special_services": [
                        "Kostenlose Gesundheitskurse",
                        "Erweiterte Vorsorge",
                        "Bonusprogramm mit Prämien",
                        "24/7 Gesundheitshotline"
                    ],
                    "regional_focus": "Bayern",
                    "digital_services": {
                        "app_rating": 4.3,
                        "online_services": "umfangreich",
                        "video_consultations": True
                    }
                },
                {
                    "name": "Techniker Krankenkasse",
                    "type": "GKV",
                    "additional_rate": 1.2,
                    "total_rate": 15.8,
                    "members": 11000000,
                    "customer_satisfaction": 4.5,
                    "special_services": [
                        "TK-App mit vielen Features",
                        "Erweiterte Reiseimpfungen",
                        "Kostenübernahme Osteopathie",
                        "Präventionskurse online"
                    ],
                    "nationwide": True,
                    "awards": ["Bester Service 2024", "Digitaler Innovator"]
                },
                {
                    "name": "Barmer",
                    "type": "GKV",
                    "additional_rate": 1.9,
                    "total_rate": 16.5,
                    "members": 8800000,
                    "customer_satisfaction": 4.1,
                    "special_services": [
                        "Teledoktor 7 Tage/Woche",
                        "Kostenübernahme Naturheilverfahren",
                        "Erweiterte Zahnvorsorge",
                        "Hebammen-Beratung per Video"
                    ],
                    "family_focus": True
                }
            ]
            insurances.extend(gkv_options)
        
        # Private Krankenversicherung (bei Berechtigung)
        if employment == "self_employed" or situation.get("income", 0) > 69300:  # Versicherungspflichtgrenze 2025
            pkv_options = [
                {
                    "name": "Allianz Private Krankenversicherung",
                    "type": "PKV",
                    "entry_age_factor": True,
                    "estimated_monthly_cost": {
                        "age_30": 450,
                        "age_40": 520,
                        "age_50": 680
                    },
                    "benefits": [
                        "Chefarztbehandlung",
                        "Einzelzimmer",
                        "Auslandsschutz weltweit",
                        "Höhere Zahnersatz-Erstattung"
                    ],
                    "pros": [
                        "Keine Wartezeiten bei Fachärzten",
                        "Bessere Leistungen",
                        "Beitragsrückerstattung möglich"
                    ],
                    "cons": [
                        "Beiträge steigen im Alter",
                        "Gesundheitsprüfung erforderlich",
                        "Familienversicherung nicht möglich"
                    ]
                }
            ]
            
            if inquiry.get("service_priority") == "premium":
                insurances.extend(pkv_options)
        
        return insurances
    
    async def _compare_benefits(self, insurances: List, inquiry: Dict) -> Dict[str, Any]:
        """Vergleicht Leistungen der Krankenversicherungen"""
        await asyncio.sleep(0.4)
        
        comparison = {
            "basic_benefits": {},
            "additional_benefits": {},
            "cost_comparison": {},
            "recommendation_matrix": {}
        }
        
        # Grundleistungen (bei GKV standardisiert)
        comparison["basic_benefits"] = {
            "doctor_visits": "100% bei Kassenärzten",
            "hospital_treatment": "100% in allgemeiner Station",
            "medications": "Zuzahlung 5-10€ pro Medikament",
            "dental_basic": "Regelversorgung 60% (mit Bonus bis 75%)",
            "maternity": "Vollständige Übernahme",
            "rehabilitation": "Nach ärztlicher Verordnung"
        }
        
        # Zusatzleistungen vergleichen
        specific_need = inquiry.get("specific_need")
        
        if specific_need == "dental":
            comparison["additional_benefits"]["dental"] = {}
            for insurance in insurances:
                if insurance["type"] == "GKV":
                    dental_coverage = "Standard-Regelversorgung"
                    if "Zahnvorsorge" in str(insurance.get("special_services", [])):
                        dental_coverage = "Erweiterte Vorsorge inklusive"
                else:  # PKV
                    dental_coverage = "Bis zu 100% je nach Tarif"
                
                comparison["additional_benefits"]["dental"][insurance["name"]] = dental_coverage
        
        if specific_need == "alternative_medicine":
            comparison["additional_benefits"]["alternative"] = {}
            for insurance in insurances:
                alt_med_coverage = "Nicht standardmäßig abgedeckt"
                if "Naturheilverfahren" in str(insurance.get("special_services", [])):
                    alt_med_coverage = "Teilweise Kostenübernahme"
                elif "Osteopathie" in str(insurance.get("special_services", [])):
                    alt_med_coverage = "Osteopathie bis 40€/Sitzung"
                
                comparison["additional_benefits"]["alternative"][insurance["name"]] = alt_med_coverage
        
        # Kostenvergleich
        for insurance in insurances:
            if insurance["type"] == "GKV":
                cost_info = {
                    "monthly_rate": f"{insurance['total_rate']}% vom Bruttoeinkommen",
                    "max_monthly": 797.72,  # Beitragsbemessungsgrenze 2025
                    "employer_share": "50% (bei Angestellten)"
                }
            else:  # PKV
                cost_info = {
                    "monthly_rate": f"ca. {insurance['estimated_monthly_cost']['age_30']}€ (Alter 30)",
                    "age_dependent": True,
                    "employer_share": "max. 403.99€ Zuschuss"
                }
            
            comparison["cost_comparison"][insurance["name"]] = cost_info
        
        return comparison
    
    async def _analyze_switching_options(self, situation: Dict) -> Dict[str, Any]:
        """Analysiert Wechselmöglichkeiten"""
        await asyncio.sleep(0.3)
        
        options = {
            "possible_switches": [],
            "restrictions": [],
            "optimal_timing": {},
            "process_steps": []
        }
        
        employment = situation.get("employment_status", "employed")
        
        # GKV zu GKV Wechsel
        if employment == "employed":
            options["possible_switches"].append({
                "from": "GKV",
                "to": "GKV",
                "requirements": [
                    "Mindestens 12 Monate bei aktueller Kasse",
                    "Kündigungsfrist 2 Monate zum Monatsende",
                    "Neue Kasse muss Aufnahme bestätigen"
                ],
                "exceptions": [
                    "Sonderkündigungsrecht bei Beitragserhöhung",
                    "Sofortwechsel bei Umzug (regional begrenzte Kasse)"
                ]
            })
        
        # PKV zu GKV Wechsel
        if employment != "self_employed":
            options["possible_switches"].append({
                "from": "PKV",
                "to": "GKV",
                "requirements": [
                    "Einkommen unter Versicherungspflichtgrenze",
                    "Angestelltenverhältnis oder arbeitslos",
                    "Unter 55 Jahre alt"
                ],
                "challenges": [
                    "Verlust der PKV-Anwartschaft",
                    "Keine Beitragsrückerstattung",
                    "Wartezeiten bei Fachärzten"
                ]
            })
        
        # Beschränkungen
        options["restrictions"] = [
            "PKV-Wechsel zurück in GKV schwierig ab 55 Jahren",
            "Gesundheitsprüfung bei PKV-Wechsel",
            "Wartezeiten bei Neueintritt in PKV",
            "Familienversicherung nur in GKV"
        ]
        
        # Optimaler Zeitpunkt
        options["optimal_timing"] = {
            "gkv_switch": "Zum Jahresende (wegen Kündigungsfristen)",
            "pkv_entry": "Jung und gesund (niedrigere Beiträge)",
            "job_change": "Übergangszeit für Systemwechsel nutzen"
        }
        
        return options
    
    async def _perform_cost_analysis(self, insurances: List, situation: Dict) -> Dict[str, Any]:
        """Führt detaillierte Kostenanalyse durch"""
        await asyncio.sleep(0.3)
        
        analysis = {
            "monthly_costs": {},
            "annual_comparison": {},
            "lifetime_projection": {},
            "cost_factors": {}
        }
        
        # Beispiel-Einkommen für Berechnung
        example_income = 4000  # Euro brutto
        
        for insurance in insurances:
            if insurance["type"] == "GKV":
                monthly_cost = min(
                    example_income * insurance["total_rate"] / 100,
                    797.72  # Höchstbeitrag 2025
                )
                employee_share = monthly_cost / 2  # Arbeitgeberanteil
                
                analysis["monthly_costs"][insurance["name"]] = {
                    "employee_share": round(employee_share, 2),
                    "total_cost": round(monthly_cost, 2),
                    "basis": f"{insurance['total_rate']}% von {example_income}€"
                }
            
            else:  # PKV
                monthly_cost = insurance["estimated_monthly_cost"]["age_30"]
                employer_subsidy = min(403.99, monthly_cost / 2)
                
                analysis["monthly_costs"][insurance["name"]] = {
                    "employee_share": round(monthly_cost - employer_subsidy, 2),
                    "total_cost": monthly_cost,
                    "employer_subsidy": round(employer_subsidy, 2)
                }
        
        # Kostenfaktoren
        analysis["cost_factors"] = {
            "gkv_factors": [
                "Bruttoeinkommen (bis zur Beitragsbemessungsgrenze)",
                "Zusatzbeitrag der Krankenkasse",
                "Familienversicherung kostenlos möglich"
            ],
            "pkv_factors": [
                "Eintrittsalter",
                "Gesundheitszustand bei Vertragsabschluss",
                "Gewählter Leistungsumfang",
                "Selbstbeteiligung",
                "Beitragsentwicklung im Alter"
            ],
            "hidden_costs": [
                "Praxisgebühren entfallen seit 2013",
                "Zuzahlungen bei Medikamenten",
                "Zusatzversicherungen für erweiterte Leistungen"
            ]
        }
        
        return analysis

# Registrierung der Worker
SOCIAL_WORKERS = {
    "social_benefits": SocialBenefitsWorker,
    "citizen_services": CitizenServicesWorker,
    "health_insurance": HealthInsuranceWorker
}

__all__ = ["SocialBenefitsWorker", "CitizenServicesWorker", "HealthInsuranceWorker", "SOCIAL_WORKERS"]
