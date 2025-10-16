"""Quick test of DirectOllamaLLM JSON parsing"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from native_ollama_integration import DirectOllamaLLM

# Simple prompt
prompt = """Respond with this exact JSON (no other text):
{
  "test": "value",
  "number": 42
}"""

# Create client
client = DirectOllamaLLM(
    model="llama3.1:8b",
    base_url="http://localhost:11434",
    temperature=0.1,
    num_predict=100
)

# Call
result = client.invoke(prompt=prompt)

# Check response
print("=" * 80)
print("RAW RESPONSE:")
print("=" * 80)
if hasattr(result, 'content'):
    print(repr(result.content))
    print("\n" + "=" * 80)
    print("ACTUAL TEXT:")
    print("=" * 80)
    print(result.content)
else:
    print(result)
