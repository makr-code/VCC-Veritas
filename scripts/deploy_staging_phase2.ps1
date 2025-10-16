#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Deploy VERITAS Phase 5 to Staging - Phase 2 (Hybrid + Query Expansion)

.DESCRIPTION
    Deploys Phase 5 with full pipeline:
    - Dense + Sparse + RRF (Hybrid Search)
    - LLM-based Query Expansion via Ollama
    - Cross-Encoder Re-Ranking
    
    Prerequisites:
    - Staging Phase 1 deployed and validated
    - Ollama running with llama2 model
    - 24h monitoring data from Phase 1

.PARAMETER RolloutPercentage
    Percentage of traffic to use Phase 5 features (default: 10)

.PARAMETER OllamaUrl
    Ollama API base URL (default: http://localhost:11434)

.PARAMETER OllamaModel
    Ollama model to use for query expansion (default: llama2)

.EXAMPLE
    .\deploy_staging_phase2.ps1
    Deploy with default settings

.EXAMPLE
    .\deploy_staging_phase2.ps1 -RolloutPercentage 25 -OllamaModel "mistral"
    Deploy with 25% rollout using Mistral model
#>

param(
    [int]$RolloutPercentage = 10,
    [string]$OllamaUrl = "http://localhost:11434",
    [string]$OllamaModel = "llama2"
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "VERITAS Phase 5 - Staging Phase 2 Deploy" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Validate rollout percentage
if ($RolloutPercentage -lt 0 -or $RolloutPercentage -gt 100) {
    Write-Host "❌ Error: Rollout percentage must be 0-100, got $RolloutPercentage" -ForegroundColor Red
    exit 1
}

Write-Host "📋 Configuration:" -ForegroundColor Yellow
Write-Host "   - Deployment Stage: Staging Phase 2" -ForegroundColor White
Write-Host "   - Hybrid Search: ✅ ENABLED" -ForegroundColor Green
Write-Host "   - Query Expansion: ✅ ENABLED" -ForegroundColor Green
Write-Host "   - Re-Ranking: ✅ ENABLED" -ForegroundColor Green
Write-Host "   - Rollout: $RolloutPercentage%" -ForegroundColor White
Write-Host "   - Ollama: $OllamaUrl" -ForegroundColor White
Write-Host "   - Model: $OllamaModel" -ForegroundColor White
Write-Host ""

# Check Ollama availability
Write-Host "🔍 Checking Ollama availability..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$OllamaUrl/api/tags" -Method Get -TimeoutSec 5 -ErrorAction Stop
    $models = $response.models | ForEach-Object { $_.name }
    
    if ($models -contains $OllamaModel) {
        Write-Host "   ✅ Ollama available, model '$OllamaModel' found" -ForegroundColor Green
    } else {
        Write-Host "   ⚠️  Ollama available, but model '$OllamaModel' NOT found" -ForegroundColor Yellow
        Write-Host "   Available models: $($models -join ', ')" -ForegroundColor Gray
        Write-Host "   Run: ollama pull $OllamaModel" -ForegroundColor Cyan
        $continue = Read-Host "Continue anyway? (y/n)"
        if ($continue -ne 'y') {
            exit 1
        }
    }
} catch {
    Write-Host "   ❌ Ollama not available at $OllamaUrl" -ForegroundColor Red
    Write-Host "   Start Ollama: ollama serve" -ForegroundColor Cyan
    Write-Host "   Pull model: ollama pull $OllamaModel" -ForegroundColor Cyan
    exit 1
}
Write-Host ""

# Set environment variables
Write-Host "🔧 Setting environment variables..." -ForegroundColor Yellow

$env:VERITAS_DEPLOYMENT_STAGE = "staging"
$env:VERITAS_ENABLE_HYBRID_SEARCH = "true"
$env:VERITAS_ENABLE_QUERY_EXPANSION = "true"  # NEW in Phase 2
$env:VERITAS_ENABLE_RERANKING = "true"
$env:VERITAS_ROLLOUT_PERCENTAGE = "$RolloutPercentage"

# Hybrid Search Parameters
$env:VERITAS_HYBRID_SPARSE_TOP_K = "20"
$env:VERITAS_HYBRID_DENSE_TOP_K = "20"
$env:VERITAS_RRF_K = "60"
$env:VERITAS_DENSE_WEIGHT = "0.6"
$env:VERITAS_SPARSE_WEIGHT = "0.4"

# BM25 Parameters
$env:VERITAS_BM25_K1 = "1.5"
$env:VERITAS_BM25_B = "0.75"
$env:VERITAS_BM25_CACHE_TTL = "3600"

# Query Expansion Parameters
$env:VERITAS_QUERY_EXPANSION_VARIANTS = "2"
$env:VERITAS_QUERY_EXPANSION_STRATEGY = "multi_perspective"
$env:VERITAS_OLLAMA_BASE_URL = $OllamaUrl
$env:VERITAS_OLLAMA_MODEL = $OllamaModel
$env:VERITAS_OLLAMA_TIMEOUT = "30"

# Performance Monitoring
$env:VERITAS_ENABLE_PERFORMANCE_MONITORING = "true"
$env:VERITAS_MAX_HYBRID_LATENCY_MS = "200"
$env:VERITAS_MAX_QE_LATENCY_MS = "2000"

Write-Host "   ✅ Environment configured" -ForegroundColor Green
Write-Host ""

# Validate configuration
Write-Host "✔️  Validating configuration..." -ForegroundColor Yellow
python -c "from config.phase5_config import get_config; config = get_config(); print(f'Config: {config}'); errors = config.validate(); exit(1) if errors else exit(0)"

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Configuration validation failed!" -ForegroundColor Red
    exit 1
}

Write-Host "   ✅ Configuration valid" -ForegroundColor Green
Write-Host ""

# Performance expectations
Write-Host "📊 Performance Expectations:" -ForegroundColor Yellow
Write-Host "   - Hybrid Latency: ~60-120ms (Phase 1 baseline)" -ForegroundColor White
Write-Host "   - Query Expansion: +30-60ms (LLM overhead)" -ForegroundColor White
Write-Host "   - Total Pipeline: <200ms (target)" -ForegroundColor White
Write-Host "   - NDCG Improvement: +7-10% over Phase 1" -ForegroundColor White
Write-Host "   - MRR Improvement: +10-15% over Phase 1" -ForegroundColor White
Write-Host ""

# Start backend
Write-Host "🚀 Starting backend with Phase 5 (Full Pipeline)..." -ForegroundColor Yellow
Write-Host ""
Write-Host "   Run: python start_backend.py" -ForegroundColor Cyan
Write-Host ""

# Show monitoring commands
Write-Host "📊 Monitoring Commands:" -ForegroundColor Yellow
Write-Host "   - Logs: Get-Content data/veritas_auto_server.log -Wait -Tail 50" -ForegroundColor Cyan
Write-Host "   - Query Expansion: grep 'QueryExpansion' data/veritas_auto_server.log" -ForegroundColor Cyan
Write-Host "   - Performance: grep 'Phase5.*latency' data/veritas_auto_server.log" -ForegroundColor Cyan
Write-Host "   - Ollama calls: grep 'Ollama' data/veritas_auto_server.log" -ForegroundColor Cyan
Write-Host ""

# Show test commands
Write-Host "🧪 Testing Commands:" -ForegroundColor Yellow
Write-Host "   - Unit Tests: pytest tests/test_phase5_hybrid_search.py::TestQueryExpansion -v" -ForegroundColor Cyan
Write-Host "   - Integration: pytest tests/test_phase5_integration.py -v" -ForegroundColor Cyan
Write-Host "   - Evaluation: python tests/test_phase5_evaluation.py" -ForegroundColor Cyan
Write-Host ""

# Show A/B comparison
Write-Host "📈 A/B Comparison Metrics:" -ForegroundColor Yellow
Write-Host "   Compare Phase 2 (Hybrid+QE) vs Phase 1 (Hybrid-only):" -ForegroundColor White
Write-Host "   - NDCG@10: Should improve by +7-10%" -ForegroundColor White
Write-Host "   - MRR: Should improve by +10-15%" -ForegroundColor White
Write-Host "   - Recall@10: Should improve by +5-10%" -ForegroundColor White
Write-Host "   - Latency: +30-60ms overhead acceptable" -ForegroundColor White
Write-Host ""

# Show rollback procedure
Write-Host "⚠️  Rollback to Phase 1:" -ForegroundColor Yellow
Write-Host "   1. Set VERITAS_ENABLE_QUERY_EXPANSION=false" -ForegroundColor White
Write-Host "   2. Restart backend" -ForegroundColor White
Write-Host "   3. Verify metrics return to Phase 1 baseline" -ForegroundColor White
Write-Host ""

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "✅ Staging Phase 2 setup complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Start backend: python start_backend.py" -ForegroundColor White
Write-Host "2. Monitor Query Expansion in logs" -ForegroundColor White
Write-Host "3. Verify Ollama API calls successful" -ForegroundColor White
Write-Host "4. Check latency stays <200ms" -ForegroundColor White
Write-Host "5. Run full evaluation suite" -ForegroundColor White
Write-Host "6. Compare metrics with Phase 1" -ForegroundColor White
Write-Host "7. After validation, plan Production rollout" -ForegroundColor White
Write-Host ""
