# NaturschutzAgent

**Typ:** ENVIRONMENTAL Agent  
**Version:** v1.0  
**Date:** 2025-10-16

---

## Übersicht
Der NaturschutzAgent beantwortet Fragen zu Naturschutz, Artenschutz, FFH-Richtlinie, UVP und Biotopverbund. Er liefert strukturierte Informationen zu gesetzlichen Grundlagen, Schutzgebieten und Verfahren.

---

## Capabilities
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

---

## Wissensbasis (Auszug)
- **BNatSchG:** Schutz von Natur und Landschaft
- **FFH-Richtlinie:** Schutz von Lebensräumen und Arten nach EU-Recht
- **Artenschutzrecht:** Internationale und nationale Regelungen zum Artenschutz
- **UVPG:** Prüfung der Umweltauswirkungen von Projekten
- **BNatSchG:** Ausgleich und Ersatz bei Eingriffen
- **BNatSchG:** Instrument zur Bilanzierung von Ausgleichsmaßnahmen

---

## Methoden
- `query(text: str)`: Liefert relevante Ergebnisse zu Suchbegriffen und Capabilities
- `get_info()`: Gibt Metadaten zum Agent zurück
- `search_naturschutz(text: str)`: Spezielle Suche im Bereich Naturschutz
- `search_uvp(text: str)`: Spezielle Suche im Bereich Umweltverträglichkeitsprüfung

---

## Beispiel-Queries
- "Was regelt das BNatSchG?"
- "Was ist die FFH-Richtlinie?"
- "Wie funktioniert die Umweltverträglichkeitsprüfung?"
- "Was ist ein Ökokonto?"

---

## Registry-Integration
- Agent-ID: `NaturschutzAgent`
- Domain: ENVIRONMENTAL
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
- Erweiterung der Wissensbasis (z.B. aktuelle Schutzgebiete, neue EU-Richtlinien)
- Integration in Multi-Agent-Workflows
- Ausbau von Spezialmethoden (z.B. Biotopverbund-Analyse)

---

**Autor:** VERITAS Development Team
