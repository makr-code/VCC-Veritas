#!/usr/bin/env python3
"""
VERITAS - Vollständiger Streaming-Backend + Agent-Integration Test
===================================================================

Umfassender End-to-End Test für:
1. Streaming Backend (SSE)
2. Intelligent Pipeline Integration
3. Alle 14 Agents (6 Basis + 8 Production)
4. Agent Registry Funktionalität
5. Multi-Agent Koordination
6. Progress Streaming
7. Real-time Event Handling

Author: VERITAS Development Team
Date: 2025-10-16
"""

import asyncio
import aiohttp
import json
import sys
import time
from datetime import datetime
from typing import Dict, List, Any, Optional

# Test-Konfiguration
BACKEND_URL = "http://localhost:5000"
TIMEOUT = 60  # Sekunden für komplexe Queries

class StreamingAgentTester:
    """Umfassender Test-Manager für Streaming + Agents"""
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.test_results: Dict[str, Any] = {}
        self.start_time = time.time()
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def print_header(self, title: str):
        """Formatierte Ausgabe für Testsektionen"""
        print("\n" + "=" * 80)
        print(f"🧪 {title}")
        print("=" * 80)
    
    def print_result(self, test_name: str, passed: bool, details: str = ""):
        """Formatierte Testergebnis-Ausgabe"""
        icon = "✅" if passed else "❌"
        print(f"{icon} {test_name}")
        if details:
            for line in details.split('\n'):
                print(f"   {line}")
    
    async def test_backend_health(self) -> bool:
        """Test 1: Backend Health Check"""
        self.print_header("TEST 1: Backend Health Check")
        
        try:
            async with self.session.get(f"{BACKEND_URL}/health", timeout=10) as response:
                if response.status != 200:
                    self.print_result("Backend Health", False, f"HTTP {response.status}")
                    return False
                
                health = await response.json()
                
                # Detaillierte Checks
                checks = {
                    "Backend Status": health.get('status') == 'healthy',
                    "Streaming verfügbar": health.get('streaming_available', False),
                    "Intelligent Pipeline": health.get('intelligent_pipeline_available', False),
                    "UDS3 verfügbar": health.get('uds3_available', False),
                    "Ollama verfügbar": health.get('ollama_available', False)
                }
                
                all_passed = all(checks.values())
                
                details = "\n".join([f"{k}: {'✅' if v else '❌'}" for k, v in checks.items()])
                self.print_result("Backend Health Check", all_passed, details)
                
                self.test_results['health'] = {
                    'passed': all_passed,
                    'details': health
                }
                
                return all_passed
                
        except Exception as e:
            self.print_result("Backend Health", False, f"Fehler: {e}")
            return False
    
    async def test_agent_registry(self) -> bool:
        """Test 2: Agent Registry mit allen 14 Agents"""
        self.print_header("TEST 2: Agent Registry - Alle 14 Agents")
        
        try:
            async with self.session.get(f"{BACKEND_URL}/capabilities", timeout=10) as response:
                if response.status != 200:
                    self.print_result("Agent Registry", False, f"HTTP {response.status}")
                    return False
                
                capabilities = await response.json()
                # Neue Struktur: features.intelligent_pipeline.agents.agents (Dict)
                pipeline_info = capabilities.get('features', {}).get('intelligent_pipeline', {})
                agents_dict = pipeline_info.get('agents', {}).get('agents', {})
                agents = list(agents_dict.keys()) if isinstance(agents_dict, dict) else []
                
                # Erwartete Agents (6 Basis + 8 Production)
                expected_agents = [
                    # Basis-Agents
                    "EnvironmentalAgent",
                    "ChemicalDataAgent",
                    "TechnicalStandardsAgent",
                    "WikipediaAgent",
                    "AtmosphericFlowAgent",
                    "DatabaseAgent",
                    # Production-Agents
                    "VerwaltungsrechtAgent",
                    "RechtsrecherchAgent",
                    "ImmissionsschutzAgent",
                    "BodenGewaesserschutzAgent",
                    "NaturschutzAgent",
                    "GenehmigungsAgent",
                    "EmissionenMonitoringAgent",
                    "VerwaltungsprozessAgent"
                ]
                
                found_agents = []
                missing_agents = []
                
                for expected in expected_agents:
                    if expected in agents:
                        found_agents.append(expected)
                    else:
                        missing_agents.append(expected)
                
                passed = len(missing_agents) == 0 and len(found_agents) == 14
                
                details_lines = [
                    f"Gefunden: {len(found_agents)}/14 Agents",
                    f"Registry-Count: {len(agents)} Agents"
                ]
                
                if missing_agents:
                    details_lines.append(f"Fehlend: {', '.join(missing_agents)}")
                
                # Agent-Kategorien
                env_agents = [a for a in found_agents if 'Environmental' in a or 'Atmospheric' in a or 'Immissionsschutz' in a or 'Boden' in a or 'Naturschutz' in a or 'Emissionen' in a]
                admin_agents = [a for a in found_agents if 'Verwaltung' in a or 'Rechts' in a or 'Genehmigung' in a]
                data_agents = [a for a in found_agents if 'Data' in a or 'Database' in a or 'Wikipedia' in a or 'Technical' in a]
                
                details_lines.extend([
                    f"",
                    f"Kategorien:",
                    f"  Umwelt/Immission: {len(env_agents)} Agents",
                    f"  Verwaltung/Recht: {len(admin_agents)} Agents",
                    f"  Daten/Recherche: {len(data_agents)} Agents"
                ])
                
                self.print_result("Agent Registry Check", passed, "\n".join(details_lines))
                
                self.test_results['agent_registry'] = {
                    'passed': passed,
                    'found': found_agents,
                    'missing': missing_agents,
                    'total': len(agents)
                }
                
                return passed
                
        except Exception as e:
            self.print_result("Agent Registry", False, f"Fehler: {e}")
            return False
    
    async def test_streaming_query_simple(self) -> bool:
        """Test 3: Einfache Streaming Query"""
        self.print_header("TEST 3: Einfache Streaming Query")
        
        query = "Was ist die TA Luft?"
        
        try:
            payload = {
                "query": query,
                "session_id": f"test_simple_{int(time.time())}",
                "enable_streaming": True,
                "enable_intermediate_results": True,
                "enable_llm_thinking": False
            }
            
            print(f"📝 Query: '{query}'")
            print(f"⏳ Starte Streaming...")
            
            # Step 1: Start streaming query (returns session_id and stream_url)
            async with self.session.post(
                f"{BACKEND_URL}/v2/query/stream",
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                
                if response.status != 200:
                    text = await response.text()
                    self.print_result("Simple Streaming", False, f"HTTP {response.status}: {text}")
                    return False
                
                stream_info = await response.json()
                stream_url = stream_info.get('stream_url', '')
                session_id = stream_info.get('session_id', '')
                
                if not stream_url:
                    self.print_result("Simple Streaming", False, "No stream_url in response")
                    return False
            
            # Step 2: Connect to SSE stream
            events = []
            agent_results = {}
            final_response = None
            
            async with self.session.get(
                f"{BACKEND_URL}{stream_url}",
                headers={'Accept': 'text/event-stream'},
                timeout=aiohttp.ClientTimeout(total=TIMEOUT)
            ) as stream_response:
                
                if stream_response.status != 200:
                    text = await stream_response.text()
                    self.print_result("Simple Streaming", False, f"Stream HTTP {stream_response.status}: {text}")
                    return False
                
                async for line in stream_response.content:
                    if line:
                        try:
                            event_str = line.decode('utf-8').strip()
                            
                            if event_str.startswith('data: '):
                                data = json.loads(event_str[6:])
                                event_type = data.get('type')  # Changed from 'event' to 'type'
                                events.append(event_type)
                                
                                if event_type == 'agent_complete':  # Changed from 'AGENT_COMPLETE'
                                    agent_name = data.get('agent_type')  # Changed from 'agent'
                                    # Extract result from details if present
                                    result = data.get('details', {})
                                    agent_results[agent_name] = result
                                    print(f"  ✓ Agent: {agent_name}")
                                
                                elif event_type == 'stage_complete' and data.get('stage') == 'completed':  # Changed from 'STREAM_COMPLETE'
                                    final_response = data.get('details', {})
                                    print(f"  ✓ Stream Complete")
                                
                        except json.JSONDecodeError:
                            pass
                        except Exception as e:
                            print(f"  ⚠️ Parse Error: {e}")
                
                passed = len(agent_results) > 0 and final_response is not None
                
                details_lines = [
                    f"Events empfangen: {len(events)}",
                    f"Agents ausgeführt: {len(agent_results)}",
                    f"Final Response: {'✅' if final_response else '❌'}"
                ]
                
                if agent_results:
                    details_lines.append(f"Agents: {', '.join(agent_results.keys())}")
                
                self.print_result("Simple Streaming Query", passed, "\n".join(details_lines))
                
                self.test_results['simple_streaming'] = {
                    'passed': passed,
                    'events': len(events),
                    'agents': list(agent_results.keys()),
                    'has_response': final_response is not None
                }
                
                return passed
                
        except Exception as e:
            self.print_result("Simple Streaming", False, f"Fehler: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    async def test_streaming_multi_agent_query(self) -> bool:
        """Test 4: Komplexe Multi-Agent Query"""
        self.print_header("TEST 4: Komplexe Multi-Agent Query mit Pipeline")
        
        query = "Welche Genehmigungen und Umweltauflagen brauche ich für ein Industriegebäude in Stuttgart mit Emissionen?"
        
        try:
            payload = {
                "query": query,
                "session_id": f"test_multi_{int(time.time())}",
                "enable_streaming": True,
                "enable_intermediate_results": True,
                "enable_llm_thinking": False
            }
            
            print(f"📝 Query: '{query}'")
            print(f"⏳ Starte Multi-Agent Koordination...")
            
            # Step 1: Start streaming query
            async with self.session.post(
                f"{BACKEND_URL}/v2/query/stream",
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                
                if response.status != 200:
                    text = await response.text()
                    self.print_result("Multi-Agent Query", False, f"HTTP {response.status}: {text}")
                    return False
                
                stream_info = await response.json()
                stream_url = stream_info.get('stream_url', '')
                
                if not stream_url:
                    self.print_result("Multi-Agent Query", False, "No stream_url in response")
                    return False
            
            # Step 2: Connect to SSE stream
            agent_results = {}
            stage_updates = []
            pipeline_used = False
            final_response = None
            
            async with self.session.get(
                f"{BACKEND_URL}{stream_url}",
                headers={'Accept': 'text/event-stream'},
                timeout=aiohttp.ClientTimeout(total=TIMEOUT)
            ) as stream_response:
                
                if stream_response.status != 200:
                    text = await stream_response.text()
                    self.print_result("Multi-Agent Query", False, f"Stream HTTP {stream_response.status}: {text}")
                    return False
                
                async for line in stream_response.content:
                    if line:
                        try:
                            event_str = line.decode('utf-8').strip()
                            
                            if event_str.startswith('data: '):
                                data = json.loads(event_str[6:])
                                event_type = data.get('type')  # Changed from 'event'
                                
                                if event_type == 'agent_complete':  # Changed from 'AGENT_COMPLETE'
                                    agent_name = data.get('agent_type')  # Changed from 'agent'
                                    result = data.get('details', {})
                                    is_sim = result.get('is_simulation', False)
                                    confidence = result.get('confidence_score', 0.0)
                                    
                                    status = "🔴 MOCK" if is_sim else "✅ PIPELINE"
                                    if not is_sim:
                                        pipeline_used = True
                                    
                                    print(f"  {agent_name:30s}: {status} (Conf: {confidence:.2f})")
                                    agent_results[agent_name] = {
                                        'is_simulation': is_sim,
                                        'confidence': confidence,
                                        'result': result
                                    }
                                
                                elif event_type == 'stage_start' or event_type == 'stage_progress':  # Changed from 'STAGE_UPDATE'
                                    stage = data.get('stage')
                                    stage_updates.append(stage)
                                    print(f"  Stage: {stage}")
                                
                                elif event_type == 'stage_complete' and data.get('stage') == 'completed':  # Changed from 'STREAM_COMPLETE'
                                    final_response = data.get('details', {})
                                    print(f"  ✓ Stream Complete")
                                
                        except json.JSONDecodeError:
                            pass
                        except Exception as e:
                            print(f"  ⚠️ Parse Error: {e}")
                
                # Analyse
                relevant_agents = [
                    'VerwaltungsrechtAgent',
                    'GenehmigungsAgent',
                    'ImmissionsschutzAgent',
                    'BodenGewaesserschutzAgent',
                    'EmissionenMonitoringAgent'
                ]
                
                found_relevant = [a for a in relevant_agents if a in agent_results]
                
                passed = (
                    len(agent_results) >= 3 and  # Mindestens 3 Agents
                    pipeline_used and  # Pipeline wurde genutzt
                    len(found_relevant) >= 2 and  # Mindestens 2 relevante Agents
                    final_response is not None
                )
                
                details_lines = [
                    f"Total Agents: {len(agent_results)}",
                    f"Pipeline genutzt: {'✅' if pipeline_used else '❌'}",
                    f"Relevante Agents: {len(found_relevant)}/{len(relevant_agents)}",
                    f"Stages durchlaufen: {len(set(stage_updates))}",
                    f"",
                    f"Gefundene relevante Agents:"
                ]
                
                for agent in found_relevant:
                    info = agent_results[agent]
                    details_lines.append(f"  ✓ {agent} (Conf: {info['confidence']:.2f})")
                
                self.print_result("Multi-Agent Query", passed, "\n".join(details_lines))
                
                self.test_results['multi_agent'] = {
                    'passed': passed,
                    'total_agents': len(agent_results),
                    'relevant_agents': found_relevant,
                    'pipeline_used': pipeline_used,
                    'stages': list(set(stage_updates))
                }
                
                return passed
                
        except Exception as e:
            self.print_result("Multi-Agent Query", False, f"Fehler: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    async def test_agent_domain_coverage(self) -> bool:
        """Test 5: Agent Domain Coverage"""
        self.print_header("TEST 5: Agent Domain Coverage (Umwelt + Verwaltung)")
        
        test_queries = [
            {
                "query": "Welche Grenzwerte gelten für NO2 Emissionen?",
                "expected_agents": ['ImmissionsschutzAgent', 'EmissionenMonitoringAgent'],
                "domain": "Umwelt"
            },
            {
                "query": "Was sind Altlasten im Bodenschutzrecht?",
                "expected_agents": ['BodenGewaesserschutzAgent'],
                "domain": "Umwelt"
            },
            {
                "query": "Wie läuft ein Genehmigungsverfahren ab?",
                "expected_agents": ['GenehmigungsAgent', 'VerwaltungsrechtAgent'],
                "domain": "Verwaltung"
            },
            {
                "query": "Welche Fristen gelten im Verwaltungsprozess?",
                "expected_agents": ['VerwaltungsprozessAgent'],
                "domain": "Verwaltung"
            }
        ]
        
        results = []
        
        for idx, test_case in enumerate(test_queries, 1):
            query = test_case['query']
            expected = test_case['expected_agents']
            domain = test_case['domain']
            
            print(f"\n{idx}. [{domain}] {query}")
            
            try:
                payload = {
                    "query": query,
                    "session_id": f"test_domain_{idx}_{int(time.time())}",
                    "enable_streaming": True,
                    "enable_intermediate_results": False,
                    "enable_llm_thinking": False
                }
                
                # Step 1: Start streaming
                async with self.session.post(
                    f"{BACKEND_URL}/v2/query/stream",
                    json=payload,
                    headers={'Content-Type': 'application/json'},
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    
                    if response.status != 200:
                        print(f"   ❌ HTTP {response.status}")
                        results.append(False)
                        continue
                    
                    stream_info = await response.json()
                    stream_url = stream_info.get('stream_url', '')
                
                # Step 2: Connect to SSE stream
                agent_results = {}
                
                async with self.session.get(
                    f"{BACKEND_URL}{stream_url}",
                    headers={'Accept': 'text/event-stream'},
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as stream_response:
                    
                    if stream_response.status != 200:
                        print(f"   ❌ Stream HTTP {stream_response.status}")
                        results.append(False)
                        continue
                    
                    async for line in stream_response.content:
                        if line:
                            try:
                                event_str = line.decode('utf-8').strip()
                                
                                if event_str.startswith('data: '):
                                    data = json.loads(event_str[6:])
                                    
                                    if data.get('type') == 'agent_complete':  # Fixed
                                        agent_name = data.get('agent_type')  # Fixed
                                        agent_results[agent_name] = True
                            
                            except:
                                pass
                    
                    found_expected = [a for a in expected if a in agent_results]
                    passed = len(found_expected) > 0
                    
                    if passed:
                        print(f"   ✅ Agents: {', '.join(found_expected)}")
                    else:
                        print(f"   ❌ Erwartete Agents nicht gefunden")
                        print(f"      Erwartet: {expected}")
                        print(f"      Gefunden: {list(agent_results.keys())}")
                    
                    results.append(passed)
                
            except Exception as e:
                print(f"   ❌ Fehler: {e}")
                results.append(False)
        
        passed = sum(results) >= 3  # Mindestens 3 von 4 müssen bestehen
        
        self.print_result(
            f"Domain Coverage ({sum(results)}/4 Tests bestanden)",
            passed,
            f"Umwelt-Queries: {results[0] and results[1]}\nVerwaltungs-Queries: {results[2] and results[3]}"
        )
        
        self.test_results['domain_coverage'] = {
            'passed': passed,
            'results': results,
            'score': f"{sum(results)}/4"
        }
        
        return passed
    
    async def test_pipeline_performance(self) -> bool:
        """Test 6: Pipeline Performance"""
        self.print_header("TEST 6: Pipeline Performance & Response Time")
        
        query = "Was ist die 17. BImSchV?"
        
        try:
            start_time = time.time()
            
            payload = {
                "query": query,
                "session_id": f"test_perf_{int(time.time())}",
                "enable_streaming": True,
                "enable_intermediate_results": False,
                "enable_llm_thinking": False
            }
            
            print(f"📝 Query: '{query}'")
            
            # Step 1: Start streaming
            async with self.session.post(
                f"{BACKEND_URL}/v2/query/stream",
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                
                if response.status != 200:
                    self.print_result("Performance Test", False, f"HTTP {response.status}")
                    return False
                
                stream_info = await response.json()
                stream_url = stream_info.get('stream_url', '')
            
            # Step 2: Connect to SSE and measure
            agent_count = 0
            first_agent_time = None
            last_agent_time = None
            
            async with self.session.get(
                f"{BACKEND_URL}{stream_url}",
                headers={'Accept': 'text/event-stream'},
                timeout=aiohttp.ClientTimeout(total=30)
            ) as stream_response:
                
                if stream_response.status != 200:
                    self.print_result("Performance Test", False, f"Stream HTTP {stream_response.status}")
                    return False
                
                async for line in stream_response.content:
                    if line:
                        try:
                            event_str = line.decode('utf-8').strip()
                            
                            if event_str.startswith('data: '):
                                data = json.loads(event_str[6:])
                                
                                if data.get('type') == 'agent_complete':  # Fixed
                                    agent_count += 1
                                    current_time = time.time()
                                    
                                    if first_agent_time is None:
                                        first_agent_time = current_time
                                    
                                    last_agent_time = current_time
                        
                        except:
                            pass
                
                end_time = time.time()
                
                total_time = end_time - start_time
                first_response_time = (first_agent_time - start_time) if first_agent_time else 0
                
                # Performance Kriterien
                passed = (
                    total_time < 30 and  # Unter 30 Sekunden total
                    first_response_time < 10 and  # Erster Agent unter 10 Sekunden
                    agent_count >= 1  # Mindestens 1 Agent
                )
                
                details_lines = [
                    f"Gesamtzeit: {total_time:.2f}s",
                    f"Zeit bis erster Agent: {first_response_time:.2f}s",
                    f"Agents ausgeführt: {agent_count}",
                    f"",
                    f"Performance-Ziele:",
                    f"  Total < 30s: {'✅' if total_time < 30 else '❌'}",
                    f"  First Response < 10s: {'✅' if first_response_time < 10 else '❌'}",
                    f"  Agents >= 1: {'✅' if agent_count >= 1 else '❌'}"
                ]
                
                self.print_result("Performance Test", passed, "\n".join(details_lines))
                
                self.test_results['performance'] = {
                    'passed': passed,
                    'total_time': total_time,
                    'first_response_time': first_response_time,
                    'agent_count': agent_count
                }
                
                return passed
                
        except Exception as e:
            self.print_result("Performance Test", False, f"Fehler: {e}")
            return False
    
    async def run_all_tests(self) -> bool:
        """Führt alle Tests aus und erstellt Zusammenfassung"""
        print("\n" + "=" * 80)
        print("🚀 VERITAS STREAMING + AGENT INTEGRATION - VOLLSTÄNDIGER TEST")
        print("=" * 80)
        print(f"Backend: {BACKEND_URL}")
        print(f"Datum: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        
        tests = [
            ("Backend Health", self.test_backend_health),
            ("Agent Registry (14 Agents)", self.test_agent_registry),
            ("Simple Streaming", self.test_streaming_query_simple),
            ("Multi-Agent Coordination", self.test_streaming_multi_agent_query),
            ("Domain Coverage", self.test_agent_domain_coverage),
            ("Performance", self.test_pipeline_performance)
        ]
        
        results = []
        
        for test_name, test_func in tests:
            try:
                result = await test_func()
                results.append((test_name, result))
            except Exception as e:
                print(f"\n❌ EXCEPTION in {test_name}: {e}")
                import traceback
                traceback.print_exc()
                results.append((test_name, False))
        
        # Zusammenfassung
        self.print_header("TEST ZUSAMMENFASSUNG")
        
        for test_name, passed in results:
            icon = "✅" if passed else "❌"
            print(f"{icon} {test_name}")
        
        passed_count = sum(1 for _, passed in results if passed)
        total_count = len(results)
        percentage = (passed_count / total_count * 100) if total_count > 0 else 0
        
        print("\n" + "=" * 80)
        print(f"📊 ERGEBNIS: {passed_count}/{total_count} Tests bestanden ({percentage:.1f}%)")
        
        total_time = time.time() - self.start_time
        print(f"⏱️  Gesamtzeit: {total_time:.2f}s")
        print("=" * 80)
        
        if passed_count == total_count:
            print("\n🎉 ALLE TESTS BESTANDEN! 🎉")
            print("\n✅ VERITAS Streaming + Agent Backend ist PRODUCTION READY!")
            return True
        elif passed_count >= total_count * 0.8:
            print(f"\n⚠️  {total_count - passed_count} Test(s) fehlgeschlagen - System teilweise funktionsfähig")
            return False
        else:
            print(f"\n❌ {total_count - passed_count} Test(s) fehlgeschlagen - Kritische Probleme!")
            return False


async def main():
    """Hauptfunktion"""
    print("\n⚠️  WICHTIG: Backend muss laufen!")
    print("Starte Backend mit: python start_backend.py\n")
    
    async with StreamingAgentTester() as tester:
        success = await tester.run_all_tests()
        return success


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Test abgebrochen durch Benutzer")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Kritischer Fehler: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
