#!/usr/bin/env python3
"""
Test Script for Vector Chart Agent

Tests:
1. Backend Agent (standalone)
2. Backend API Endpoints
3. Frontend UI (manual)
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


async def test_agent_standalone():
    """Test 1: VectorChartAgent standalone"""
    print("=" * 70)
    print("TEST 1: VectorChartAgent (Standalone)")
    print("=" * 70)
    
    from backend.agents.vector_chart_agent import VectorChartAgent
    
    agent = VectorChartAgent()
    
    # Test 1.1: Bar Chart mit Template
    print("\n📊 Test 1.1: Bar Chart (Template: bimschg_overview)")
    result = await agent.generate_chart(
        "Erstelle ein Bar Chart",
        template='bimschg_overview'
    )
    
    if result['success']:
        print(f"  ✅ Erfolg!")
        print(f"     Typ: {result['chart_type']}")
        print(f"     Titel: {result['title']}")
        print(f"     PNG: {result['exports']['png']}")
        print(f"     SVG: {result['exports']['svg']}")
        print(f"     PDF: {result['exports']['pdf']}")
        if result['exports'].get('pptx'):
            print(f"     PPTX: {result['exports']['pptx']}")
    else:
        print(f"  ❌ Fehler: {result.get('error')}")
    
    # Test 1.2: Pie Chart
    print("\n🥧 Test 1.2: Pie Chart (Template: wka_leistung)")
    result = await agent.generate_chart(
        "Zeige Pie Chart",
        template='wka_leistung'
    )
    
    if result['success']:
        print(f"  ✅ Erfolg!")
        print(f"     Typ: {result['chart_type']}")
        print(f"     Titel: {result['title']}")
        print(f"     Datenpunkte: {len(result['data']['values'])}")
    else:
        print(f"  ❌ Fehler: {result.get('error')}")
    
    # Test 1.3: Line Chart
    print("\n📈 Test 1.3: Line Chart (Template: zeitreihe_genehmigungen)")
    result = await agent.generate_chart(
        "Liniendiagramm",
        template='zeitreihe_genehmigungen'
    )
    
    if result['success']:
        print(f"  ✅ Erfolg!")
        print(f"     Typ: {result['chart_type']}")
        print(f"     Titel: {result['title']}")
    else:
        print(f"  ❌ Fehler: {result.get('error')}")
    
    # Test 1.4: Fallback (ohne LLM)
    print("\n🔄 Test 1.4: Fallback-Intent (ohne LLM)")
    result = await agent.generate_chart(
        "Erstelle ein beliebiges Bar Chart"
    )
    
    if result['success']:
        print(f"  ✅ Erfolg! (Fallback funktioniert)")
        print(f"     Typ: {result['chart_type']}")
    else:
        print(f"  ❌ Fehler: {result.get('error')}")
    
    # Test 1.5: Templates auflisten
    print("\n📋 Test 1.5: Templates auflisten")
    templates = agent.list_templates()
    print(f"  ✅ {len(templates)} Templates verfügbar:")
    for t in templates:
        print(f"     - {t['name']:30} | {t['type']:8} | {t['title']}")
    
    print("\n✅ VectorChartAgent-Tests abgeschlossen\n")


async def test_api_endpoints():
    """Test 2: Backend API Endpoints"""
    print("=" * 70)
    print("TEST 2: Backend API Endpoints")
    print("=" * 70)
    
    import requests
    
    base_url = "http://localhost:5000"
    
    # Test 2.1: Health Check
    print("\n🏥 Test 2.1: Health Check")
    try:
        response = requests.get(f"{base_url}/api/charts/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"  ✅ Backend erreichbar")
            print(f"     Status: {data.get('status')}")
            print(f"     Agent initialisiert: {data.get('agent_initialized')}")
            print(f"     Templates: {data.get('templates_available')}")
        else:
            print(f"  ❌ HTTP {response.status_code}")
    except requests.exceptions.ConnectionError:
        print(f"  ❌ Backend nicht erreichbar (http://localhost:5000)")
        print(f"     Bitte starten Sie das Backend mit: python start_backend.py")
        return
    except Exception as e:
        print(f"  ❌ Fehler: {e}")
        return
    
    # Test 2.2: Templates abrufen
    print("\n📋 Test 2.2: Templates abrufen")
    try:
        response = requests.get(f"{base_url}/api/charts/templates", timeout=5)
        if response.status_code == 200:
            templates = response.json()
            print(f"  ✅ {len(templates)} Templates abgerufen")
            for t in templates[:3]:
                print(f"     - {t['name']}: {t['title']} ({t['type']})")
        else:
            print(f"  ❌ HTTP {response.status_code}")
    except Exception as e:
        print(f"  ❌ Fehler: {e}")
    
    # Test 2.3: Chart generieren
    print("\n🎨 Test 2.3: Chart generieren (API)")
    try:
        payload = {
            "prompt": "Erstelle ein Bar Chart",
            "template": "bimschg_overview"
        }
        response = requests.post(
            f"{base_url}/api/charts/generate",
            json=payload,
            timeout=30
        )
        if response.status_code == 200:
            data = response.json()
            print(f"  ✅ Chart generiert")
            print(f"     Typ: {data.get('chart_type')}")
            print(f"     Titel: {data.get('title')}")
            print(f"     PNG vorhanden: {'image_base64' in data}")
            print(f"     Exports: {', '.join(data.get('exports', {}).keys())}")
        else:
            print(f"  ❌ HTTP {response.status_code}")
            print(f"     Detail: {response.json().get('detail')}")
    except Exception as e:
        print(f"  ❌ Fehler: {e}")
    
    print("\n✅ API-Tests abgeschlossen\n")


def test_frontend_manual():
    """Test 3: Frontend UI (manueller Test)"""
    print("=" * 70)
    print("TEST 3: Frontend UI (Manueller Test)")
    print("=" * 70)
    print()
    print("ℹ️  Dieser Test öffnet das Chart Builder-Fenster.")
    print("    Bitte testen Sie manuell:")
    print()
    print("    1. Template auswählen (z.B. 'BImSchG-Übersicht')")
    print("    2. Oder eigenen Prompt eingeben")
    print("    3. 'Chart Generieren' klicken")
    print("    4. Chart-Anzeige überprüfen")
    print("    5. Export-Funktionen testen (PNG, SVG, PDF, PPTX)")
    print()
    
    input("Drücken Sie Enter um das Chart Builder-Fenster zu öffnen...")
    
    try:
        import tkinter as tk
        from frontend.ui.chart_builder import ChartBuilderWindow
        
        root = tk.Tk()
        root.withdraw()
        
        # Mock API-Client
        class MockAPIClient:
            base_url = "http://localhost:5000"
        
        api_client = MockAPIClient()
        
        print("\n🪟 Chart Builder-Fenster geöffnet...")
        print("   Bitte führen Sie die manuellen Tests durch.")
        print("   Schließen Sie das Fenster um fortzufahren.\n")
        
        window = ChartBuilderWindow(root, api_client)
        
        root.mainloop()
        
        print("\n✅ Frontend-Test abgeschlossen\n")
    
    except Exception as e:
        print(f"\n❌ Fehler beim Öffnen des Frontend: {e}\n")


async def run_all_tests():
    """Alle Tests ausführen"""
    print("\n" + "=" * 70)
    print("VERITAS VECTOR CHART AGENT - VOLLSTÄNDIGER TEST")
    print("=" * 70)
    print()
    
    # Test 1: Agent standalone
    await test_agent_standalone()
    
    # Test 2: API Endpoints
    await test_api_endpoints()
    
    # Test 3: Frontend (manuell)
    print("Möchten Sie auch das Frontend testen? (y/n): ", end="")
    answer = input().strip().lower()
    if answer == 'y':
        test_frontend_manual()
    
    print("\n" + "=" * 70)
    print("TESTS ABGESCHLOSSEN")
    print("=" * 70)
    print()
    print("📊 Chart-Dateien wurden erstellt in:")
    print(f"   /tmp/veritas_charts/")
    print()
    print("📝 Nächste Schritte:")
    print("   1. Backend starten: python start_backend.py")
    print("   2. Frontend starten: python start_frontend.py")
    print("   3. Chart Builder öffnen: Tools > Chart Builder (Ctrl+Shift+C)")
    print()


if __name__ == '__main__':
    asyncio.run(run_all_tests())
