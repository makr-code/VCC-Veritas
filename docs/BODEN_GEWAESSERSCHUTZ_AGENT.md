# BodenGewaesserschutzAgent

**Typ:** ENVIRONMENTAL Agent  
**Version:** v1.0  
**Date:** 2025-10-16

---

## Übersicht
Der BodenGewaesserschutzAgent ist spezialisiert auf alle Fragen rund um Bodenschutz, Altlasten, Grundwasser und Wasserrecht. Er bietet schnelle, strukturierte Antworten zu gesetzlichen Grundlagen, Grenzwerten und Verfahren.

---

## Capabilities
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

---

## Wissensbasis (Auszug)
- **BBodSchG:** Schutz des Bodens vor schädlichen Veränderungen
- **Altlastenverordnung:** Definition und Sanierung von Altlasten
- **WHG:** Schutz und Nutzung des Grundwassers
- **WRRL:** Ziel: Guter Zustand aller Gewässer bis 2027
- **Nitrat-Richtlinie:** Grenzwerte für Nitrat im Grundwasser
- **KrWG:** Kreislaufwirtschaftsgesetz für Abfallmanagement
- **Abwasserverordnung:** Grenzwerte und Anforderungen für Abwasser
- **BNatSchG:** Schutz von Gebieten mit besonderer Bedeutung

---

## Methoden
- `query(text: str)`: Liefert relevante Ergebnisse zu Suchbegriffen und Capabilities
- `get_info()`: Gibt Metadaten zum Agent zurück
- `search_bodenschutz(text: str)`: Spezielle Suche im Bereich Bodenschutz
- `search_wasserrecht(text: str)`: Spezielle Suche im Bereich Wasserrecht

---

## Beispiel-Queries
- "Was regelt das BBodSchG?"
- "Welche Grenzwerte gelten für Nitrat im Grundwasser?"
- "Was ist die Wasserrahmenrichtlinie?"
- "Wie werden Altlasten saniert?"

---

## Registry-Integration
- Agent-ID: `BodenGewaesserschutzAgent`
- Domain: ENVIRONMENTAL
- Capabilities: siehe oben
- Vollständig in AgentRegistry integriert

---

## Testabdeckung
- Initialisierung
- Query für alle Capabilities
- Fallback-Query
- get_info()
- **100% Test Success Rate**

---

## Weiterentwicklung
- Erweiterung der Wissensbasis (z.B. aktuelle Grenzwerte, neue Verordnungen)
- Integration in Multi-Agent-Workflows
- Ausbau von Spezialmethoden (z.B. Altlasten-Sanierungsverfahren)

---

**Autor:** VERITAS Development Team
