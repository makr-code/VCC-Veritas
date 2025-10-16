#!/usr/bin/env python3
"""
Direct ChromaDB Connection Test
Testet direkte ChromaDB-Verbindung und zeigt vorhandene Collections/Documents
"""

import requests

def test_chromadb_http():
    """Test ChromaDB via HTTP API"""
    print("=" * 80)
    print("CHROMADB CONNECTION TEST (HTTP API)")
    print("=" * 80)
    print()
    
    # Connection parameters from config.py
    host = "192.168.178.94"
    port = 8000
    base_url = f"http://{host}:{port}"
    
    try:
        print(f"🔌 Verbinde zu ChromaDB: {base_url}")
        print()
        
        # 1. Test connection / heartbeat
        response = requests.get(f"{base_url}/api/v1/heartbeat", timeout=5)
        if response.status_code == 200:
            heartbeat = response.json()
            print(f"✅ Verbindung erfolgreich! Heartbeat: {heartbeat}")
            print()
        
        # 2. Get version
        try:
            response = requests.get(f"{base_url}/api/v1/version", timeout=5)
            if response.status_code == 200:
                version = response.json()
                print(f"📦 ChromaDB Version: {version}")
                print()
        except:
            pass
        
        # 3. List all collections
        print("📚 Collections:")
        response = requests.get(f"{base_url}/api/v1/collections", timeout=5)
        
        if response.status_code == 200:
            collections = response.json()
            
            if collections:
                for coll in collections:
                    coll_name = coll.get('name', 'Unknown')
                    coll_id = coll.get('id', 'Unknown')
                    
                    # Get collection details
                    try:
                        detail_response = requests.get(
                            f"{base_url}/api/v1/collections/{coll_id}",
                            timeout=5
                        )
                        if detail_response.status_code == 200:
                            details = detail_response.json()
                            # Try to count documents
                            count_response = requests.post(
                                f"{base_url}/api/v1/collections/{coll_id}/count",
                                timeout=5
                            )
                            count = count_response.json() if count_response.status_code == 200 else "?"
                            
                            print(f"   - {coll_name} (ID: {coll_id[:8]}...)")
                            print(f"     Dokumente: {count}")
                            
                            # Try to get sample documents
                            try:
                                get_response = requests.post(
                                    f"{base_url}/api/v1/collections/{coll_id}/get",
                                    json={"limit": 3},
                                    timeout=5
                                )
                                if get_response.status_code == 200:
                                    docs = get_response.json()
                                    if docs.get('documents'):
                                        print(f"     Beispiel-Dokumente: {len(docs['documents'])}")
                                        for i, doc in enumerate(docs['documents'][:2], 1):
                                            preview = str(doc)[:100] if doc else ""
                                            print(f"       {i}. {preview}...")
                            except:
                                pass
                    except Exception as detail_e:
                        print(f"   - {coll_name} (Details nicht verfügbar: {detail_e})")
                print()
            else:
                print("   ⚠️  Keine Collections gefunden!")
                print()
        else:
            print(f"   ❌ Fehler beim Abrufen der Collections: HTTP {response.status_code}")
            print()
        
        # 4. Search for BGB/Taschengeld
        if collections:
            print("🔍 Suche nach BGB/Taschengeld-Dokumenten:")
            for coll in collections:
                coll_name = coll.get('name', 'Unknown')
                coll_id = coll.get('id')
                
                try:
                    # Try query
                    query_response = requests.post(
                        f"{base_url}/api/v1/collections/{coll_id}/query",
                        json={
                            "query_texts": ["BGB Taschengeld § 110"],
                            "n_results": 5
                        },
                        timeout=10
                    )
                    
                    if query_response.status_code == 200:
                        results = query_response.json()
                        if results.get('documents') and results['documents'][0]:
                            print(f"   ✅ {coll_name}: {len(results['documents'][0])} Treffer")
                            # Show first result
                            first_doc = results['documents'][0][0] if results['documents'][0] else ""
                            preview = str(first_doc)[:150]
                            print(f"      Beispiel: {preview}...")
                        else:
                            print(f"   ❌ {coll_name}: 0 Treffer")
                except Exception as search_e:
                    print(f"   ⚠️  {coll_name}: Suche fehlgeschlagen ({search_e})")
        
        print()
        print("=" * 80)
        print("TEST ABGESCHLOSSEN")
        print("=" * 80)
        
    except requests.exceptions.ConnectionError:
        print(f"❌ Verbindungsfehler: ChromaDB Server nicht erreichbar auf {base_url}")
        print("   Ist der ChromaDB Server gestartet?")
    except requests.exceptions.Timeout:
        print(f"❌ Timeout: ChromaDB Server antwortet nicht auf {base_url}")
    except Exception as e:
        print(f"❌ FEHLER: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_chromadb_http()
