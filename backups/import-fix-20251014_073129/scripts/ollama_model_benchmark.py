#!/usr/bin/env python3
"""
OLLAMA MODEL BENCHMARK & AUTO-SELECTION
========================================

Testet alle verfügbaren Ollama-Modelle auf:
1. Verfügbarkeit
2. Antwortzeit (Latenz)
3. Qualität der Query Expansion
4. Empfehlung basierend auf Speed/Quality-Tradeoff

Author: VERITAS System
Date: 7. Oktober 2025
"""

import asyncio
import time
import json
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict
import httpx


@dataclass
class ModelBenchmarkResult:
    """Benchmark-Ergebnis für ein Ollama-Modell."""
    
    model_name: str
    available: bool
    
    # Performance
    avg_latency_ms: float = 0.0
    min_latency_ms: float = 0.0
    max_latency_ms: float = 0.0
    p95_latency_ms: float = 0.0
    
    # Size & Details
    size_gb: float = 0.0
    parameter_size: str = ""
    quantization: str = ""
    
    # Quality (subjektiv)
    quality_score: float = 0.0  # 0-10
    
    # Recommendation
    recommended_for: str = ""  # "production", "development", "testing"
    score: float = 0.0  # Gesamt-Score (Speed + Quality)
    
    # Errors
    error: Optional[str] = None


class OllamaModelBenchmark:
    """Benchmark-Tool für Ollama-Modelle."""
    
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
        self.test_prompts = [
            "Formuliere um: BGB Taschengeldparagraph",
            "Umschreibe: Verwaltungsakt Definition",
            "Synonym für: nachhaltig bauen"
        ]
    
    async def get_available_models(self) -> List[Dict]:
        """Holt Liste aller verfügbaren Modelle."""
        
        print("🔍 Fetching available Ollama models...")
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                response.raise_for_status()
                
                data = response.json()
                models = data.get("models", [])
                
                print(f"✅ Found {len(models)} models")
                return models
                
        except Exception as e:
            print(f"❌ Error fetching models: {e}")
            return []
    
    async def benchmark_model(
        self, 
        model_name: str,
        model_details: Dict,
        num_runs: int = 3
    ) -> ModelBenchmarkResult:
        """Benchmarkt ein einzelnes Modell."""
        
        print(f"\n{'='*60}")
        print(f"🧪 Benchmarking: {model_name}")
        print(f"{'='*60}")
        
        result = ModelBenchmarkResult(
            model_name=model_name,
            available=True
        )
        
        # Extract model details
        details = model_details.get("details", {})
        result.size_gb = model_details.get("size", 0) / (1024**3)
        result.parameter_size = details.get("parameter_size", "Unknown")
        result.quantization = details.get("quantization_level", "Unknown")
        
        print(f"📊 Size: {result.size_gb:.2f} GB")
        print(f"📊 Parameters: {result.parameter_size}")
        print(f"📊 Quantization: {result.quantization}")
        
        # Run benchmark
        latencies = []
        
        for i, prompt in enumerate(self.test_prompts, 1):
            print(f"\n🔄 Test {i}/{len(self.test_prompts)}: '{prompt[:40]}...'")
            
            for run in range(num_runs):
                try:
                    start_time = time.time()
                    
                    response_text = await self._call_ollama(model_name, prompt)
                    
                    latency_ms = (time.time() - start_time) * 1000
                    latencies.append(latency_ms)
                    
                    print(f"   Run {run+1}: {latency_ms:.0f}ms → '{response_text[:50]}...'")
                    
                except Exception as e:
                    print(f"   Run {run+1}: ❌ ERROR: {e}")
                    result.error = str(e)
                    result.available = False
                    return result
        
        # Calculate statistics
        if latencies:
            result.avg_latency_ms = sum(latencies) / len(latencies)
            result.min_latency_ms = min(latencies)
            result.max_latency_ms = max(latencies)
            result.p95_latency_ms = sorted(latencies)[int(len(latencies) * 0.95)]
            
            print(f"\n📈 Performance Statistics:")
            print(f"   Avg: {result.avg_latency_ms:.0f}ms")
            print(f"   Min: {result.min_latency_ms:.0f}ms")
            print(f"   Max: {result.max_latency_ms:.0f}ms")
            print(f"   P95: {result.p95_latency_ms:.0f}ms")
            
            # Calculate quality score (based on model size & type)
            result.quality_score = self._estimate_quality(model_name, result.parameter_size)
            
            # Calculate overall score (Speed + Quality tradeoff)
            # Lower latency = better score
            # Higher quality = better score
            speed_score = max(0, 10 - (result.avg_latency_ms / 1000))  # 10 points at 0ms, 0 at 10s
            result.score = (speed_score * 0.6) + (result.quality_score * 0.4)
            
            # Recommendation
            if result.avg_latency_ms < 500:
                result.recommended_for = "production"
            elif result.avg_latency_ms < 2000:
                result.recommended_for = "development"
            else:
                result.recommended_for = "testing"
            
            print(f"\n⭐ Quality Score: {result.quality_score:.1f}/10")
            print(f"⚡ Speed Score: {speed_score:.1f}/10")
            print(f"🎯 Overall Score: {result.score:.1f}/10")
            print(f"💡 Recommended for: {result.recommended_for.upper()}")
        
        return result
    
    async def _call_ollama(self, model: str, prompt: str) -> str:
        """Ruft Ollama API auf."""
        
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.7,
                "num_predict": 50
            }
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            
            result = response.json()
            return result.get("response", "").strip()
    
    def _estimate_quality(self, model_name: str, param_size: str) -> float:
        """Schätzt Qualität basierend auf Modell-Name und Größe."""
        
        # Extract parameter count
        param_lower = param_size.lower()
        
        # Quality estimates (subjektiv, basierend auf typischen LLM-Größen)
        if "mixtral" in model_name.lower():
            return 9.0  # Mixtral ist sehr gut
        elif "70b" in param_lower or "45b" in param_lower:
            return 9.5
        elif "20b" in param_lower or "13b" in param_lower:
            return 8.5
        elif "8b" in param_lower or "7b" in param_lower:
            return 8.0
        elif "3b" in param_lower or "3.8b" in param_lower:
            return 7.0
        elif "1.5b" in param_lower or "1b" in param_lower:
            return 6.0
        elif "embed" in model_name.lower():
            return 4.0  # Embedding-Modelle nicht für Text-Generation
        elif "23m" in param_lower or "137m" in param_lower:
            return 3.0  # Sehr klein
        else:
            return 6.5  # Default
    
    async def run_full_benchmark(self) -> List[ModelBenchmarkResult]:
        """Führt Benchmark für alle Modelle aus."""
        
        print("\n" + "="*60)
        print("🚀 OLLAMA MODEL BENCHMARK - FULL SUITE")
        print("="*60)
        
        models = await self.get_available_models()
        
        if not models:
            print("❌ No models found!")
            return []
        
        results = []
        
        for i, model_data in enumerate(models, 1):
            model_name = model_data["name"]
            
            print(f"\n[{i}/{len(models)}] Testing: {model_name}")
            
            result = await self.benchmark_model(model_name, model_data)
            results.append(result)
        
        return results
    
    def print_summary(self, results: List[ModelBenchmarkResult]):
        """Druckt Zusammenfassung aller Ergebnisse."""
        
        print("\n" + "="*80)
        print("📊 BENCHMARK RESULTS SUMMARY")
        print("="*80)
        
        # Sort by score
        sorted_results = sorted(
            [r for r in results if r.available],
            key=lambda x: x.score,
            reverse=True
        )
        
        # Table Header
        print(f"\n{'Rank':<6} {'Model':<25} {'Latency':<12} {'Quality':<10} {'Score':<8} {'Rec':<12}")
        print("-" * 80)
        
        for i, result in enumerate(sorted_results, 1):
            latency_str = f"{result.avg_latency_ms:.0f}ms"
            quality_str = f"{result.quality_score:.1f}/10"
            score_str = f"{result.score:.1f}/10"
            
            print(f"{i:<6} {result.model_name:<25} {latency_str:<12} {quality_str:<10} {score_str:<8} {result.recommended_for:<12}")
        
        # Failed models
        failed = [r for r in results if not r.available]
        if failed:
            print(f"\n❌ Failed Models: {len(failed)}")
            for result in failed:
                print(f"   - {result.model_name}: {result.error}")
        
        # Recommendations
        print("\n" + "="*80)
        print("💡 RECOMMENDATIONS")
        print("="*80)
        
        if sorted_results:
            best = sorted_results[0]
            print(f"\n🥇 BEST OVERALL: {best.model_name}")
            print(f"   Avg Latency: {best.avg_latency_ms:.0f}ms")
            print(f"   Quality: {best.quality_score:.1f}/10")
            print(f"   Score: {best.score:.1f}/10")
            
            # Best for production (fastest with acceptable quality)
            production_candidates = [
                r for r in sorted_results 
                if r.avg_latency_ms < 500 and r.quality_score >= 6.0
            ]
            
            if production_candidates:
                prod_best = production_candidates[0]
                print(f"\n🚀 BEST FOR PRODUCTION (<500ms): {prod_best.model_name}")
                print(f"   Avg Latency: {prod_best.avg_latency_ms:.0f}ms")
                print(f"   Quality: {prod_best.quality_score:.1f}/10")
            
            # Best for quality (if speed not critical)
            quality_best = max(sorted_results, key=lambda x: x.quality_score)
            print(f"\n⭐ BEST QUALITY: {quality_best.model_name}")
            print(f"   Quality: {quality_best.quality_score:.1f}/10")
            print(f"   Avg Latency: {quality_best.avg_latency_ms:.0f}ms")
        
        print("\n" + "="*80)
    
    def save_results(self, results: List[ModelBenchmarkResult], filename: str = "ollama_benchmark_results.json"):
        """Speichert Ergebnisse als JSON."""
        
        data = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "base_url": self.base_url,
            "results": [asdict(r) for r in results]
        }
        
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Results saved to: {filename}")
    
    def get_best_model(self, results: List[ModelBenchmarkResult]) -> Optional[str]:
        """Gibt das beste Modell zurück."""
        
        available = [r for r in results if r.available]
        
        if not available:
            return None
        
        # Best for production: <500ms latency, quality >= 6.0
        production = [
            r for r in available 
            if r.avg_latency_ms < 500 and r.quality_score >= 6.0
        ]
        
        if production:
            return max(production, key=lambda x: x.score).model_name
        
        # Fallback: best overall score
        return max(available, key=lambda x: x.score).model_name


async def main():
    """Main benchmark execution."""
    
    benchmark = OllamaModelBenchmark()
    
    # Run full benchmark
    results = await benchmark.run_full_benchmark()
    
    # Print summary
    benchmark.print_summary(results)
    
    # Save results
    benchmark.save_results(results)
    
    # Get recommendation
    best_model = benchmark.get_best_model(results)
    
    if best_model:
        print("\n" + "="*80)
        print("✅ FINAL RECOMMENDATION")
        print("="*80)
        print(f"\n🎯 Use Model: {best_model}")
        print(f"\n📝 Update config/phase5_config.py:")
        print(f"   QUERY_EXPANSION_MODEL = '{best_model}'")
        print("\n" + "="*80)
    else:
        print("\n❌ No suitable model found!")


if __name__ == "__main__":
    asyncio.run(main())
