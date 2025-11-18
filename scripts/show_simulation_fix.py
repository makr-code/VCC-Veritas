# Fix: Agent Results mit Simulation-Warnung markieren
# Fügt Transparenz hinzu bis UDS3 Integration abgeschlossen ist

import os
import sys

# Pfad anpassen
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

print("🔧 SIMULATION WARNING PATCH")
print("=" * 80)
print("Ziel: Markiere simulierte Agent Results mit Warnung")
print("=" * 80)

# Zeige aktuellen Code
print("\n📄 Aktueller Code in _generate_agent_result():")
print("-" * 80)

code_snippet = """
def _generate_agent_result(agent_type: str, query: str, complexity: str) -> Dict[str, Any]:
    # ... UDS3 Try-Block ...

    # Fallback: Simulierte Ergebnisse
    base_confidence = 0.8 if complexity == 'basic' else 0.75

    agent_specialties = {
        'geo_context': {
            'summary': 'Geografischer Kontext...',
            'sources': ['OpenStreetMap', 'Gemeinde-DB']  # ← HARDCODED
        },
        # ... weitere Agenten ...
    }

    return {
        'agent_type': agent_type,
        'confidence_score': base_confidence + (0.1 * hash(...)),  # ← RANDOM
        'summary': specialty['summary'],  # ← HARDCODED
        'sources': specialty['sources'],  # ← HARDCODED
        'status': 'completed'
    }
"""
print(code_snippet)

print("\n📝 Empfohlene Änderung:")
print("-" * 80)

fix_snippet = """
def _generate_agent_result(agent_type: str, query: str, complexity: str) -> Dict[str, Any]:
    # ... UDS3 Try-Block ...

    # Fallback: Simulierte Ergebnisse
    logger.warning(f"⚠️  SIMULATION: Agent {agent_type} nutzt hardcoded Daten (UDS3 nicht verfügbar)")

    base_confidence = 0.8 if complexity == 'basic' else 0.75

    agent_specialties = { ... }

    return {
        'agent_type': agent_type,
        'confidence_score': base_confidence + (0.1 * hash(...)),
        'summary': specialty['summary'],
        'sources': specialty['sources'],
        'status': 'completed',
        'is_simulation': True,  # 🆕 NEU: Markiere als Simulation
        'simulation_reason': 'UDS3 not available',  # 🆕 NEU: Grund
        'data_quality': 'simulated'  # 🆕 NEU: Qualitäts-Flag
    }
"""
print(fix_snippet)

print("\n" + "=" * 80)
print("✅ Empfohlene Aktionen:")
print("=" * 80)
print(
    """
1. In backend/api/veritas_api_backend.py:

   Zeile ~1200 - In _generate_agent_result() hinzufügen:

   a) Vor dem return im Fallback-Block:
      logger.warning(f"⚠️  SIMULATION: {agent_type} nutzt hardcoded Daten")

   b) Im return dict hinzufügen:
      'is_simulation': True,
      'simulation_reason': 'UDS3 database not available',
      'data_quality': 'simulated'

2. In backend/api/veritas_api_backend.py:

   Zeile ~1266 - In _synthesize_final_response() hinzufügen:

   # Prüfe ob Ergebnisse simuliert sind
   simulated_agents = [
       agent for agent, result in agent_results.items()
       if result.get('is_simulation', False)
   ]

   if simulated_agents:
       main_response += f'''
⚠️  **HINWEIS**: Diese Antwort basiert teilweise auf simulierten Daten.
   Folgende Agenten nutzen Beispieldaten: {', '.join(simulated_agents)}
   Grund: UDS3-Datenbank nicht verfügbar.
'''

3. Im Frontend (frontend/veritas_app.py):

   Zeile ~590 - In _handle_backend_response() hinzufügen:

   # Prüfe auf Simulation
   if response_data.get('metadata', {}).get('has_simulation'):
       formatted_content = "⚠️  DEMO-MODUS\\n\\n" + formatted_content

4. Teste die Warnung:

   python start_frontend.py
   → Stelle eine Frage
   → Prüfe ob Warnung erscheint
"""
)

print("\n" + "=" * 80)
print("📚 Weitere Informationen:")
print("=" * 80)
print(
    """
- Vollständiger Report: docs/SIMULATION_MOCK_ANALYSIS_REPORT.md
- UDS3 Integration Plan: docs/UDS3_REAL_AGENT_INTEGRATION_PLAN.md
- Chat History Doku: docs/CHAT_HISTORY_INTEGRATION.md
"""
)

print("\n✅ Script abgeschlossen\n")
