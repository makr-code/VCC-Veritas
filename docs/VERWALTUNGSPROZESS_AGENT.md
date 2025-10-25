# VerwaltungsprozessAgent

**Capabilities:**
- verwaltungsprozess
- klageverfahren
- einstweiliger rechtsschutz
- gerichtsbarkeit
- verwaltungsgericht
- fristen
- rechtsmittel
- urteilsdatenbank

**Wissensbasis:**
- VwGO (Verwaltungsgerichtsordnung)
- Klagefrist (§ 74 VwGO)
- Widerspruchsfrist (§ 70 VwGO)
- Einstweiliger Rechtsschutz (§§ 80, 80a, 123 VwGO)
- Berufung (§ 124 VwGO)
- Revision (§ 132 VwGO)
- Urteilsdatenbank (BVerwG, OVG)
- Verwaltungsgerichtsbarkeit (Dreistufiger Aufbau)

**Methoden:**
- query(keyword): Sucht nach Capabilities und Wissensbasis-Einträgen
- get_info(): Metadaten und Übersicht
- search_prozess(query): Suche nach Verfahrensinformationen
- search_urteile(query): Suche in Urteilsdatenbank

**Registry-Integration:**
- Agent wird in der AgentRegistry als "VerwaltungsprozessAgent" registriert
- Domain: ADMINISTRATIVE
- requires_db: False
- requires_api: False

**Testabdeckung:**
- Initialisierung
- Capabilities-Query
- Wissensbasis-Query
- Fallback-Query
- get_info
- search_prozess
- search_urteile

**Beispiel-Querys:**
- "Klagefrist Widerspruchsbescheid"
- "BVerwG Immissionsschutz"
- "Einstweiliger Rechtsschutz § 80 VwGO"
- "Berufung Verwaltungsgericht"
