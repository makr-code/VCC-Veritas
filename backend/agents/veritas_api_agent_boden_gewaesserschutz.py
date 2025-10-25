"""
Boden- und GewässerschutzAgent für VERITAS
==========================================

Capabilities:
- bodenschutz
- altlasten
- grundwasser
- wasserrahmenrichtlinie
- bodenverunreinigung
- schutzgebiete
- hydrogeologie
- abfallrecht
- wasserrecht
- abwasser
- nitratbelastung

Wissensbasis:
- Bodenschutzgesetz (BBodSchG)
- Wasserhaushaltsgesetz (WHG)
- Altlastenverordnung
- Wasserrahmenrichtlinie (WRRL)
- Nitrat-Richtlinie

Author: VERITAS Development Team
Date: 2025-10-16
"""

from typing import List, Dict, Any

class BodenGewaesserschutzAgent:
    """Agent für Boden- und Gewässerschutz"""
    name = "BodenGewaesserschutzAgent"
    domain = "ENVIRONMENTAL"
    version = "v1.0"
    capabilities = [
        "bodenschutz", "altlasten", "grundwasser", "wasserrahmenrichtlinie",
        "bodenverunreinigung", "schutzgebiete", "hydrogeologie", "abfallrecht",
        "wasserrecht", "abwasser", "nitratbelastung"
    ]
    knowledge_base = {
        "bodenschutz": [
            {"gesetz": "BBodSchG", "inhalt": "Schutz des Bodens vor schädlichen Veränderungen."},
            {"gesetz": "Altlastenverordnung", "inhalt": "Regelungen zu Altlasten und Sanierung."}
        ],
        "altlasten": [
            {"gesetz": "Altlastenverordnung", "inhalt": "Definition und Sanierung von Altlasten."},
            {"gesetz": "BBodSchG", "inhalt": "Pflichten zur Erkundung und Sanierung von Altlasten."}
        ],
        "grundwasser": [
            {"gesetz": "WHG", "inhalt": "Schutz und Nutzung des Grundwassers."},
            {"gesetz": "WRRL", "inhalt": "Europäische Wasserrahmenrichtlinie."}
        ],
        "wasserrahmenrichtlinie": [
            {"gesetz": "WRRL", "inhalt": "Ziel: Guter Zustand aller Gewässer bis 2027."},
            {"gesetz": "WHG", "inhalt": "Umsetzung der WRRL im deutschen Wasserrecht."}
        ],
        "nitratbelastung": [
            {"gesetz": "Nitrat-Richtlinie", "inhalt": "Grenzwerte für Nitrat im Grundwasser."}
        ],
        "abfallrecht": [
            {"gesetz": "KrWG", "inhalt": "Kreislaufwirtschaftsgesetz für Abfallmanagement."}
        ],
        "wasserrecht": [
            {"gesetz": "WHG", "inhalt": "Wasserhaushaltsgesetz für Oberflächengewässer und Grundwasser."}
        ],
        "abwasser": [
            {"gesetz": "Abwasserverordnung", "inhalt": "Grenzwerte und Anforderungen für Abwasser."}
        ],
        "schutzgebiete": [
            {"gesetz": "BNatSchG", "inhalt": "Schutz von Gebieten mit besonderer Bedeutung."}
        ],
        "hydrogeologie": [
            {"gesetz": "WHG", "inhalt": "Hydrogeologische Grundlagen im Wasserrecht."}
        ],
        "bodenverunreinigung": [
            {"gesetz": "BBodSchG", "inhalt": "Sanierung und Vorsorge bei Bodenverunreinigung."}
        ]
    }

    def query(self, text: str) -> Dict[str, Any]:
        """Verarbeitet eine Anfrage und liefert relevante Ergebnisse"""
        results = []
        confidence = 0.0
        for cap in self.capabilities:
            if cap in text.lower():
                kb = self.knowledge_base.get(cap, [])
                results.extend(kb)
                confidence = 0.8
        # Fallback: Schlüsselwortsuche
        if not results:
            for cap, kb in self.knowledge_base.items():
                for entry in kb:
                    if any(word in text.lower() for word in [entry["gesetz"].lower(), entry["inhalt"].lower()]):
                        results.append(entry)
                        confidence = 0.6
        return {
            "success": bool(results),
            "results": results,
            "confidence": confidence,
            "agent": self.name
        }

    def get_info(self) -> Dict[str, Any]:
        """Gibt Metadaten zum Agent zurück"""
        return {
            "name": self.name,
            "domain": self.domain,
            "version": self.version,
            "capabilities": self.capabilities,
            "knowledge_base_size": sum(len(v) for v in self.knowledge_base.values())
        }

    def search_bodenschutz(self, text: str) -> List[Dict[str, Any]]:
        """Spezielle Suche im Bereich Bodenschutz"""
        return [entry for entry in self.knowledge_base.get("bodenschutz", []) if text.lower() in entry["inhalt"].lower()]

    def search_wasserrecht(self, text: str) -> List[Dict[str, Any]]:
        """Spezielle Suche im Bereich Wasserrecht"""
        return [entry for entry in self.knowledge_base.get("wasserrecht", []) if text.lower() in entry["inhalt"].lower()]
