# GenehmigungsAgent

**Typ:** LEGAL Agent  
**Version:** v1.0  
**Date:** 2025-10-16

---

## Übersicht
Der GenehmigungsAgent beantwortet Fragen zu Genehmigungsverfahren, Antragsstellung, Beteiligung, Fristen und Umweltinformationsgesetz. Er liefert strukturierte Informationen zu gesetzlichen Grundlagen und Verfahrensschritten.

---

## Capabilities
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

---

## Wissensbasis (Auszug)
- **VwVfG:** Regelungen zu Verwaltungsverfahren und Genehmigungen
- **UIG:** Recht auf Zugang zu Umweltinformationen
- **VwVfG:** Fristen, Beteiligung, Widerspruch, Anhörung, Akteneinsicht

---

## Methoden
- `query(text: str)`: Liefert relevante Ergebnisse zu Suchbegriffen und Capabilities
- `get_info()`: Gibt Metadaten zum Agent zurück
- `search_genehmigung(text: str)`: Spezielle Suche im Bereich Genehmigungsverfahren
- `search_beteiligung(text: str)`: Spezielle Suche im Bereich Beteiligung

---

## Beispiel-Queries
- "Wie läuft ein Genehmigungsverfahren ab?"
- "Welche Fristen gelten im Verwaltungsverfahren?"
- "Wie kann ich Akteneinsicht beantragen?"
- "Was regelt das Umweltinformationsgesetz?"

---

## Registry-Integration
- Agent-ID: `GenehmigungsAgent`
- Domain: LEGAL
- Capabilities: siehe oben
- Vollständig in AgentRegistry integrierbar

---

## Testabdeckung
- Initialisierung
- Query für alle Capabilities
- Fallback-Query
- get_info()

---

## Weiterentwicklung
- Erweiterung der Wissensbasis (z.B. aktuelle Fristen, neue Beteiligungsrechte)
- Integration in Multi-Agent-Workflows
- Ausbau von Spezialmethoden (z.B. Widerspruchsverfahren)

---

**Autor:** VERITAS Development Team
