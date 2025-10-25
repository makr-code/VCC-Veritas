"""
NaturschutzAgent für VERITAS
===========================

Capabilities:
- naturschutz
- flora-fauna-habitat
- artenschutz
- landschaftsschutz
- naturschutzgebiete
- FFH-Richtlinie
- Biotopverbund
- Umweltverträglichkeitsprüfung
- Eingriffsregelung
- Ökokonto

Wissensbasis:
- BNatSchG (Bundesnaturschutzgesetz)
- FFH-Richtlinie
- UVPG (Umweltverträglichkeitsprüfungsgesetz)
- Artenschutzrecht

Author: VERITAS Development Team
Date: 2025-10-16
"""

from typing import List, Dict, Any

class NaturschutzAgent:
    """Agent für Naturschutz und Artenschutz"""
    name = "NaturschutzAgent"
    domain = "ENVIRONMENTAL"
    version = "v1.0"
    capabilities = [
        "naturschutz", "flora-fauna-habitat", "artenschutz", "landschaftsschutz",
        "naturschutzgebiete", "ffh-richtlinie", "biotopverbund", "umweltverträglichkeitsprüfung",
        "eingriffsregelung", "ökokonto"
    ]
    knowledge_base = {
        "naturschutz": [
            {"gesetz": "BNatSchG", "inhalt": "Schutz von Natur und Landschaft."}
        ],
        "flora-fauna-habitat": [
            {"gesetz": "FFH-Richtlinie", "inhalt": "Schutz von Lebensräumen und Arten nach EU-Recht."}
        ],
        "artenschutz": [
            {"gesetz": "BNatSchG", "inhalt": "Besonderer Schutz gefährdeter Arten."},
            {"gesetz": "Artenschutzrecht", "inhalt": "Internationale und nationale Regelungen zum Artenschutz."}
        ],
        "landschaftsschutz": [
            {"gesetz": "BNatSchG", "inhalt": "Erhalt und Entwicklung der Landschaft."}
        ],
        "naturschutzgebiete": [
            {"gesetz": "BNatSchG", "inhalt": "Ausweisung und Schutz von Naturschutzgebieten."}
        ],
        "ffh-richtlinie": [
            {"gesetz": "FFH-Richtlinie", "inhalt": "Erhalt von Lebensräumen und Arten von gemeinschaftlichem Interesse."}
        ],
        "biotopverbund": [
            {"gesetz": "BNatSchG", "inhalt": "Vernetzung von Biotopen zur Förderung der Artenvielfalt."}
        ],
        "umweltverträglichkeitsprüfung": [
            {"gesetz": "UVPG", "inhalt": "Prüfung der Umweltauswirkungen von Projekten."}
        ],
        "eingriffsregelung": [
            {"gesetz": "BNatSchG", "inhalt": "Ausgleich und Ersatz bei Eingriffen in Natur und Landschaft."}
        ],
        "ökokonto": [
            {"gesetz": "BNatSchG", "inhalt": "Instrument zur Bilanzierung von Ausgleichs- und Ersatzmaßnahmen."}
        ]
    }

    def query(self, text: str) -> Dict[str, Any]:
        results = []
        confidence = 0.0
        for cap in self.capabilities:
            if cap in text.lower():
                kb = self.knowledge_base.get(cap, [])
                results.extend(kb)
                confidence = 0.8
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
        return {
            "name": self.name,
            "domain": self.domain,
            "version": self.version,
            "capabilities": self.capabilities,
            "knowledge_base_size": sum(len(v) for v in self.knowledge_base.values())
        }

    def search_naturschutz(self, text: str) -> List[Dict[str, Any]]:
        return [entry for entry in self.knowledge_base.get("naturschutz", []) if text.lower() in entry["inhalt"].lower()]

    def search_uvp(self, text: str) -> List[Dict[str, Any]]:
        return [entry for entry in self.knowledge_base.get("umweltverträglichkeitsprüfung", []) if text.lower() in entry["inhalt"].lower()]
