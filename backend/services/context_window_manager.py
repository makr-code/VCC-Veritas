#!/usr/bin/env python3
"""
Context Window Manager - Modell-spezifische Token-Limits
=========================================================
Verhindert Token-Overflow und routet zu größeren Modellen bei Bedarf.

Features:
- Modell-spezifische Context-Window-Limits
- 80% Safety-Reserve für System-Prompts
- Automatic Model-Routing bei Overflow
- Token-Counting für Prompts + Responses

Author: VERITAS System
Date: 2025-10-17
"""

import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class ModelSize(str, Enum):
    """Modell-Größenkategorien"""
    TINY = "tiny"      # <1B params
    SMALL = "small"    # 1-3B params
    MEDIUM = "medium"  # 3-8B params
    LARGE = "large"    # 8-70B params
    XLARGE = "xlarge"  # >70B params


@dataclass
class ModelSpec:
    """Modell-Spezifikation mit Context-Window"""
    name: str
    size: ModelSize
    context_window: int  # Max tokens (input + output)
    parameters: str      # z.B. "2.7B"
    recommended_max_output: int  # Empfohlenes max_tokens
    
    @property
    def safe_max_output(self) -> int:
        """80% des Context-Windows für Output (20% Reserve für System-Prompts)"""
        return int(self.context_window * 0.8)


# Ollama-Modell-Registry
OLLAMA_MODELS: Dict[str, ModelSpec] = {
    # Tiny Models (<1B)
    "all-minilm": ModelSpec("all-minilm", ModelSize.TINY, 512, "22M", 400),
    "nomic-embed-text": ModelSpec("nomic-embed-text", ModelSize.TINY, 8192, "137M", 6500),
    
    # Small Models (1-3B)
    "phi3": ModelSpec("phi3", ModelSize.SMALL, 4096, "2.7B", 3200),
    "phi3:mini": ModelSpec("phi3:mini", ModelSize.SMALL, 4096, "2.7B", 3200),
    "gemma3": ModelSpec("gemma3", ModelSize.SMALL, 8192, "2B", 6500),
    "gemma:2b": ModelSpec("gemma:2b", ModelSize.SMALL, 8192, "2B", 6500),
    
    # Medium Models (3-8B)
    "llama3.2": ModelSpec("llama3.2", ModelSize.MEDIUM, 8192, "3B", 6500),
    "llama3.2:3b": ModelSpec("llama3.2:3b", ModelSize.MEDIUM, 8192, "3B", 6500),
    "mistral": ModelSpec("mistral", ModelSize.MEDIUM, 8192, "7B", 6500),
    "mistral:7b": ModelSpec("mistral:7b", ModelSize.MEDIUM, 8192, "7B", 6500),
    
    # Large Models (8-70B)
    "llama3.1:8b": ModelSpec("llama3.1:8b", ModelSize.LARGE, 32768, "8B", 26000),
    "llama3": ModelSpec("llama3", ModelSize.LARGE, 8192, "8B", 6500),
    "llama3:8b": ModelSpec("llama3:8b", ModelSize.LARGE, 8192, "8B", 6500),
    "codellama": ModelSpec("codellama", ModelSize.LARGE, 16384, "13B", 13000),
    "mixtral": ModelSpec("mixtral", ModelSize.LARGE, 32768, "8x7B", 26000),
    "qwen2.5-coder": ModelSpec("qwen2.5-coder", ModelSize.LARGE, 32768, "7B", 26000),
    
    # XLarge Models (>70B)
    "llama3.1:70b": ModelSpec("llama3.1:70b", ModelSize.XLARGE, 131072, "70B", 104000),
}

# Fallback für unbekannte Modelle
DEFAULT_MODEL_SPEC = ModelSpec("unknown", ModelSize.MEDIUM, 8192, "unknown", 6500)


@dataclass
class TokenBudgetContext:
    """Context für Token-Budget-Berechnung"""
    model_name: str
    model_spec: ModelSpec
    system_prompt_tokens: int
    user_prompt_tokens: int
    rag_context_tokens: int
    total_input_tokens: int
    requested_output_tokens: int
    available_output_tokens: int
    needs_model_upgrade: bool
    recommended_model: Optional[str] = None


class ContextWindowManager:
    """
    Managed Context-Window-Limits für verschiedene LLM-Modelle
    
    Features:
    - Modell-spezifische Limits
    - Token-Counting
    - Automatic Model-Routing
    - Safety-Reserve Management
    """
    
    def __init__(self, safety_factor: float = 0.8):
        """
        Args:
            safety_factor: Sicherheitsfaktor für max_output (default: 0.8 = 80%)
        """
        self.safety_factor = safety_factor
        self.models = OLLAMA_MODELS
    
    def get_model_spec(self, model_name: str) -> ModelSpec:
        """
        Holt Modell-Spezifikation
        
        Args:
            model_name: Name des Modells (z.B. "phi3", "llama3.1:8b")
            
        Returns:
            ModelSpec mit Context-Window-Informationen
        """
        # Exakter Match
        if model_name in self.models:
            return self.models[model_name]
        
        # Partial Match (z.B. "llama3" matched "llama3:8b")
        for key, spec in self.models.items():
            if model_name in key or key in model_name:
                return spec
        
        # Fallback
        return DEFAULT_MODEL_SPEC
    
    def estimate_token_count(self, text: str) -> int:
        """
        Schätzt Token-Count (approximiert: 1 token ≈ 4 chars)
        
        Args:
            text: Text zum Zählen
            
        Returns:
            Geschätzte Anzahl Tokens
        """
        if not text:
            return 0
        
        # Einfache Approximation: 1 token ≈ 4 characters
        # Für präzisere Zählung: tiktoken verwenden
        return len(text) // 4
    
    def calculate_available_output_tokens(
        self,
        model_name: str,
        system_prompt: str = "",
        user_prompt: str = "",
        rag_context: str = "",
        requested_output_tokens: int = 1000
    ) -> TokenBudgetContext:
        """
        Berechnet verfügbare Output-Tokens unter Berücksichtigung des Context-Windows
        
        Args:
            model_name: Modell-Name
            system_prompt: System-Prompt
            user_prompt: User-Prompt
            rag_context: RAG-Context
            requested_output_tokens: Gewünschte Output-Tokens
            
        Returns:
            TokenBudgetContext mit allen Informationen
        """
        model_spec = self.get_model_spec(model_name)
        
        # Token-Counts schätzen
        system_tokens = self.estimate_token_count(system_prompt)
        user_tokens = self.estimate_token_count(user_prompt)
        rag_tokens = self.estimate_token_count(rag_context)
        
        total_input_tokens = system_tokens + user_tokens + rag_tokens
        
        # Verfügbare Output-Tokens berechnen
        max_safe_output = int(model_spec.context_window * self.safety_factor)
        available_output = max_safe_output - total_input_tokens
        
        # Prüfen ob Model-Upgrade nötig
        needs_upgrade = requested_output_tokens > available_output
        recommended_model = None
        
        if needs_upgrade:
            recommended_model = self._find_suitable_model(
                total_input_tokens,
                requested_output_tokens
            )
        
        return TokenBudgetContext(
            model_name=model_name,
            model_spec=model_spec,
            system_prompt_tokens=system_tokens,
            user_prompt_tokens=user_tokens,
            rag_context_tokens=rag_tokens,
            total_input_tokens=total_input_tokens,
            requested_output_tokens=requested_output_tokens,
            available_output_tokens=max(0, available_output),
            needs_model_upgrade=needs_upgrade,
            recommended_model=recommended_model
        )
    
    def _find_suitable_model(
        self,
        input_tokens: int,
        output_tokens: int
    ) -> Optional[str]:
        """
        Findet passendes größeres Modell
        
        Args:
            input_tokens: Benötigte Input-Tokens
            output_tokens: Benötigte Output-Tokens
            
        Returns:
            Empfohlenes Modell oder None
        """
        total_needed = input_tokens + output_tokens
        
        # Sortiere Modelle nach Context-Window
        sorted_models = sorted(
            self.models.items(),
            key=lambda x: x[1].context_window
        )
        
        # Finde kleinstes Modell das ausreicht
        for name, spec in sorted_models:
            if spec.context_window * self.safety_factor >= total_needed:
                return name
        
        return None
    
    def adjust_token_budget(
        self,
        model_name: str,
        requested_tokens: int,
        system_prompt: str = "",
        user_prompt: str = "",
        rag_context: str = ""
    ) -> Tuple[int, TokenBudgetContext]:
        """
        Passt Token-Budget an Context-Window-Limits an
        
        Args:
            model_name: Modell-Name
            requested_tokens: Gewünschte Output-Tokens
            system_prompt: System-Prompt
            user_prompt: User-Prompt
            rag_context: RAG-Context
            
        Returns:
            Tuple[adjusted_tokens, context]
        """
        context = self.calculate_available_output_tokens(
            model_name=model_name,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            rag_context=rag_context,
            requested_output_tokens=requested_tokens
        )
        
        # Budget auf verfügbare Tokens begrenzen
        adjusted_tokens = min(requested_tokens, context.available_output_tokens)
        
        return adjusted_tokens, context
    
    def get_model_recommendations(
        self,
        complexity_score: float,
        token_budget: int
    ) -> List[str]:
        """
        Empfiehlt Modelle basierend auf Komplexität und Token-Budget
        
        Args:
            complexity_score: Query-Komplexität (1-10)
            token_budget: Benötigtes Token-Budget
            
        Returns:
            Liste empfohlener Modelle (sortiert nach Eignung)
        """
<<<<<<< Updated upstream
        recommendations = []
        
=======
        recommendations: List[str] = []

>>>>>>> Stashed changes
        # Einfache Queries (1-3) → Small Models
        if complexity_score <= 3:
            recommendations.extend(["phi3", "gemma3"])
        
        # Mittlere Queries (4-6) → Medium Models
        elif complexity_score <= 6:
            recommendations.extend(["mistral", "llama3.2"])
        
        # Komplexe Queries (7-8) → Large Models
        elif complexity_score <= 8:
            recommendations.extend(["llama3.1:8b", "mixtral"])
        
        # Sehr komplexe Queries (9-10) → XLarge Models
        else:
            recommendations.extend(["llama3.1:70b", "mixtral"])
        
        # Filtere nach Context-Window
        suitable: List[str] = []
        for model_name in recommendations:
            spec = self.get_model_spec(model_name)
            if spec.safe_max_output >= token_budget:
                suitable.append(model_name)
        
        return suitable if suitable else ["llama3.1:8b"]  # Fallback


# Test-Funktion
if __name__ == "__main__":
    manager = ContextWindowManager(safety_factor=0.8)
    
    print("=" * 80)
    print("CONTEXT WINDOW MANAGER - Test")
    print("=" * 80)
    
    # Test 1: Modell-Specs
    print("\n📊 MODELL-SPEZIFIKATIONEN")
    print("─" * 80)
    for model_name in ["phi3", "llama3.1:8b", "llama3.1:70b"]:
        spec = manager.get_model_spec(model_name)
        print(f"\n{model_name}:")
        print(f"  • Context Window: {spec.context_window:,} tokens")
        print(f"  • Safe Max Output: {spec.safe_max_output:,} tokens (80%)")
        print(f"  • Recommended: {spec.recommended_max_output:,} tokens")
        print(f"  • Size: {spec.size.value} ({spec.parameters})")
    
    # Test 2: Token-Budget-Anpassung
    print("\n\n💰 TOKEN-BUDGET-ANPASSUNG")
    print("─" * 80)
<<<<<<< Updated upstream
    
    test_cases = [
=======

    from typing import Any as _Any

    test_cases: List[Dict[str, _Any]] = [
>>>>>>> Stashed changes
        {
            "model": "phi3",
            "requested": 2000,
            "system": "Du bist ein hilfreicher Assistent." * 10,
            "user": "Erkläre mir Verwaltungsrecht." * 20,
            "rag": "Verwaltungsrecht umfasst..." * 50
        },
        {
            "model": "llama3.1:8b",
            "requested": 4000,
            "system": "Du bist ein Rechtsexperte." * 10,
            "user": "Analysiere verwaltungsrechtliche Voraussetzungen." * 30,
            "rag": "Rechtliche Grundlagen..." * 100
        }
    ]
    
    for i, test in enumerate(test_cases, 1):
        print(f"\nTest {i}: {test['model']}")
        
        adjusted, context = manager.adjust_token_budget(
            model_name=test['model'],
            requested_tokens=test['requested'],
            system_prompt=test['system'],
            user_prompt=test['user'],
            rag_context=test['rag']
        )
        
        print(f"  • Input Tokens: {context.total_input_tokens:,}")
        print(f"    - System: {context.system_prompt_tokens:,}")
        print(f"    - User: {context.user_prompt_tokens:,}")
        print(f"    - RAG: {context.rag_context_tokens:,}")
        print(f"  • Requested Output: {test['requested']:,} tokens")
        print(f"  • Available Output: {context.available_output_tokens:,} tokens")
        print(f"  • Adjusted Output: {adjusted:,} tokens")
        
        if context.needs_model_upgrade:
            print(f"  ⚠️ Model-Upgrade empfohlen: {context.recommended_model}")
        else:
            print(f"  ✅ Model ausreichend")
    
    # Test 3: Modell-Empfehlungen
    print("\n\n🎯 MODELL-EMPFEHLUNGEN")
    print("─" * 80)
    
    complexity_tests = [
        (2.0, 500, "Einfache Frage"),
        (5.0, 1500, "Mittlere Komplexität"),
        (8.5, 4000, "Verwaltungsrecht"),
        (10.0, 4000, "Multi-Aspekt-Analyse")
    ]
    
    for complexity, budget, description in complexity_tests:
        recommendations = manager.get_model_recommendations(complexity, budget)
        print(f"\n{description} (Complexity: {complexity}/10, Budget: {budget:,}):")
        print(f"  → Empfohlen: {', '.join(recommendations)}")
    
    print("\n" + "=" * 80 + "\n")
