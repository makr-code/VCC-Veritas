from backend.agents.domain.environmental.naturschutz_agent_v2_framework import NaturschutzAgent

agent = NaturschutzAgent()
result = agent.query("FFH Richtlinie")
print(f"Success: {result['success']}")
print(f"Results: {result.get('results', [])}")
print(f"Error: {result.get('error', 'none')}")
print(f"Confidence: {result.get('confidence', 0.0)}")
