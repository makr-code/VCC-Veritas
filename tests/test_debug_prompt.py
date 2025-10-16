"""
Debug: Show exact prompt sent to LLM
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.agents.veritas_enhanced_prompts import EnhancedPromptTemplates, PromptMode

def show_prompt():
    """Show exact prompt that LLM receives"""
    
    print("="*80)
    print("🔍 EXACT PROMPT SENT TO LLM")
    print("="*80)
    
    # Simulate what SupervisorAgent does
    original_query = "Was regelt § 58 LBO BW?"
    
    rag_context = "[1] RAG: § 58 LBO BW regelt Bauanträge und Genehmigungen"
    
    agent_results_text = """**BuildingAgent** (Confidence: 0.85):
§ 58 LBO BW behandelt die formalen Anforderungen für Bauanträge."""
    
    source_list = """[1] Agent: BuildingAgent (Conf: 0.85)"""
    
    # Get system prompt
    system_prompt = EnhancedPromptTemplates.get_system_prompt(
        mode=PromptMode.USER_FACING,
        domain="general"
    )
    
    # Get user prompt
    user_prompt = EnhancedPromptTemplates.get_user_prompt(
        mode=PromptMode.USER_FACING,
        domain="general",
        query=original_query,
        rag_context=rag_context,
        agent_results=agent_results_text,
        source_list=source_list
    )
    
    print("\n" + "="*80)
    print("📝 SYSTEM PROMPT (First 500 chars):")
    print("="*80)
    print(system_prompt[:500])
    print("...\n")
    
    print("="*80)
    print("📝 USER PROMPT (Full):")
    print("="*80)
    print(user_prompt)
    print("\n")
    
    print("="*80)
    print("📊 ANALYSIS:")
    print("="*80)
    print(f"System Prompt Length: {len(system_prompt)} chars")
    print(f"User Prompt Length: {len(user_prompt)} chars")
    print(f"Total Prompt Length: {len(system_prompt) + len(user_prompt)} chars")
    
    # Check for key phrases
    full_prompt = system_prompt + "\n\n" + user_prompt
    
    print(f"\n✅ Contains 'IEEE-ZITATIONEN': {('IEEE-ZITATIONEN' in full_prompt)}")
    print(f"✅ Contains '[N] zitiert werden': {('[N] zitiert werden' in full_prompt)}")
    print(f"✅ Contains 'BEISPIEL 1': {('BEISPIEL 1' in full_prompt)}")
    print(f"✅ Contains 'BEISPIEL 2': {('BEISPIEL 2' in full_prompt)}")
    print(f"✅ Contains 'BEISPIEL 3': {('BEISPIEL 3' in full_prompt)}")
    print(f"✅ Contains 'source_list': {('Verfügbare Quellen' in full_prompt or 'source_list' in full_prompt)}")
    
    # Count few-shot examples
    import re
    examples = re.findall(r'BEISPIEL \d+', full_prompt)
    print(f"\n📚 Few-Shot Examples Found: {len(examples)} → {examples}")

if __name__ == "__main__":
    show_prompt()
