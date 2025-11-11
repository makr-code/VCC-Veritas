"""
GenehmigungsAgent für VERITAS
============================

Capabilities:
- genehmigungsverfahren
- antragsstellung
- verwaltungsverfahren
- fristen
- beteiligung
- öffentlichkeitsbeteiligung
- widerspruch
- anhörung
- umweltinformationsgesetz
- akteneinsicht

Wissensbasis:
- VwVfG (Verwaltungsverfahrensgesetz)
- UIG (Umweltinformationsgesetz)
- Fristenregelungen
- Beteiligungsrechte

Author: VERITAS Development Team
Date: 2025-10-16
"""

from typing import Any, Dict, List


class GenehmigungsAgent:
    """Agent für Genehmigungsverfahren und Beteiligung"""

    name = "GenehmigungsAgent"
    domain = "LEGAL"
    version = "v1.0"
    capabilities = [
        "genehmigungsverfahren",
        "antragsstellung",
        "verwaltungsverfahren",
        "fristen",
        "beteiligung",
        "öffentlichkeitsbeteiligung",
        "widerspruch",
        "anhörung",
        "umweltinformationsgesetz",
        "akteneinsicht",
    ]
    knowledge_base = {
        "genehmigungsverfahren": [{"gesetz": "VwVfG", "inhalt": "Regelungen zu Verwaltungsverfahren und Genehmigungen."}],
        "antragsstellung": [{"gesetz": "VwVfG", "inhalt": "Form und Ablauf der Antragstellung."}],
        "verwaltungsverfahren": [{"gesetz": "VwVfG", "inhalt": "Ablauf und Grundsätze des Verwaltungsverfahrens."}],
        "fristen": [{"gesetz": "VwVfG", "inhalt": "Fristen im Verwaltungsverfahren."}],
        "beteiligung": [{"gesetz": "VwVfG", "inhalt": "Beteiligungsrechte im Verfahren."}],
        "öffentlichkeitsbeteiligung": [{"gesetz": "VwVfG", "inhalt": "Öffentliche Beteiligung bei Genehmigungen."}],
        "widerspruch": [{"gesetz": "VwVfG", "inhalt": "Widerspruchsverfahren gegen Verwaltungsakte."}],
        "anhörung": [{"gesetz": "VwVfG", "inhalt": "Recht auf Anhörung im Verfahren."}],
        "umweltinformationsgesetz": [{"gesetz": "UIG", "inhalt": "Recht auf Zugang zu Umweltinformationen."}],
        "akteneinsicht": [{"gesetz": "VwVfG", "inhalt": "Recht auf Akteneinsicht im Verfahren."}],
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
        return {"success": bool(results), "results": results, "confidence": confidence, "agent": self.name}

    def get_info(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "domain": self.domain,
            "version": self.version,
            "capabilities": self.capabilities,
            "knowledge_base_size": sum(len(v) for v in self.knowledge_base.values()),
        }

    def search_genehmigung(self, text: str) -> List[Dict[str, Any]]:
        return [
            entry for entry in self.knowledge_base.get("genehmigungsverfahren", []) if text.lower() in entry["inhalt"].lower()
        ]

    def search_beteiligung(self, text: str) -> List[Dict[str, Any]]:
        return [entry for entry in self.knowledge_base.get("beteiligung", []) if text.lower() in entry["inhalt"].lower()]
