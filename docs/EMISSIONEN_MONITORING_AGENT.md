# Emissionen-MonitoringAgent

**Capabilities:**
- emissionsmessung
- kontinuierliche überwachung
- emissionsbericht
- grenzwertüberschreitung
- messstellen
- berichterstattung
- emissionsdatenbank
- fernüberwachung

**Wissensbasis:**
- BImSchG (Bundes-Immissionsschutzgesetz)
- TA Luft (Technische Anleitung zur Reinhaltung der Luft)
- Messstellenverordnung
- Emissionsdatenbank
- Fernüberwachung

**Methoden:**
- query(keyword): Sucht nach Capabilities und Wissensbasis-Einträgen
- get_info(): Metadaten und Übersicht
- search_emissionen(query): Suche nach Emissionsdaten
- search_bericht(query): Suche nach Berichten

**Registry-Integration:**
- Agent wird in der AgentRegistry als "EmissionenMonitoringAgent" registriert
- Domain: ENVIRONMENTAL
- requires_db: False
- requires_api: False

**Testabdeckung:**
- Initialisierung
- Capabilities-Query
- Wissensbasis-Query
- Fallback-Query
- get_info
- search_emissionen
- search_bericht

**Beispiel-Querys:**
- "NO2 Grenzwertüberschreitung"
- "Jahresbericht 2024"
- "Messstellen TA Luft"
