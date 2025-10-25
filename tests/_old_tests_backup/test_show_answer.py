"""
Quick test to see actual LLM answer
"""

import requests
import json

BACKEND_URL = "http://localhost:5000"

def test_and_show_answer():
    """Send query and show actual answer"""
    
    print("="*80)
    print("🔍 SHOW ACTUAL LLM ANSWER")
    print("="*80)
    
    question = "Was regelt § 58 LBO BW?"
    
    print(f"\n📝 Frage: {question}")
    print(f"\n⏳ Sende Query an Backend...")
    
    payload = {
        "question": question,
        "mode": "intelligent",
        "session_id": "test-show-answer"
    }
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/ask",
            json=payload,
            timeout=60
        )
        
        if response.status_code == 200:
            data = response.json()
            answer = data.get("answer", "")
            
            print(f"\n✅ Antwort erhalten ({len(answer)} Zeichen)")
            print("\n" + "="*80)
            print("📄 VOLLSTÄNDIGE ANTWORT:")
            print("="*80)
            print(answer)
            print("="*80)
            
            # Check for citations
            import re
            citations = re.findall(r'\[(\d+)\]', answer)
            
            print(f"\n📊 QUICK ANALYSIS:")
            print(f"  Citations [N]: {len(citations)} → {citations if citations else '❌ KEINE!'}")
            print(f"  Legal Refs §: {len(re.findall(r'§\s*\d+', answer))}")
            print(f"  Has 'Direkte Antwort': {'✅' if '**Direkte Antwort**' in answer else '❌'}")
            print(f"  Has 'Details': {'✅' if '**Details**' in answer else '❌'}")
            print(f"  Has 'Quellen': {'✅' if '**Quellen**' in answer else '❌'}")
            print(f"  Has '💡': {'✅' if '💡' in answer else '❌'}")
            
        else:
            print(f"\n❌ Fehler: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"\n❌ Exception: {e}")

if __name__ == "__main__":
    test_and_show_answer()
