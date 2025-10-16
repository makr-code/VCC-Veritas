#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Deploy VERITAS Phase 5 to Staging - Phase 1 (Hybrid Search)

.DESCRIPTION
    Deploys Phase 5 with Hybrid Search enabled (Dense + Sparse + RRF).
    Query Expansion is disabled for initial testing.
    
    Deployment Steps:
    1. Set environment variables for Staging Phase 1
    2. Validate configuration
    3. Index corpus for BM25
    4. Start backend with Phase 5 features
    5. Monitor performance metrics

.PARAMETER RolloutPercentage
    Percentage of traffic to use Phase 5 features (default: 10)

.PARAMETER CorpusPath
    Path to corpus for BM25 indexing (optional)

.EXAMPLE
    .\deploy_staging_phase1.ps1
    Deploy with default 10% rollout

.EXAMPLE
    .\deploy_staging_phase1.ps1 -RolloutPercentage 25
    Deploy with 25% rollout
#>

param(
    [int]$RolloutPercentage = 10,
    [string]$CorpusPath = ""
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "VERITAS Phase 5 - Staging Phase 1 Deploy" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Validate rollout percentage
if ($RolloutPercentage -lt 0 -or $RolloutPercentage -gt 100) {
    Write-Host "❌ Error: Rollout percentage must be 0-100, got $RolloutPercentage" -ForegroundColor Red
    exit 1
}

Write-Host "📋 Configuration:" -ForegroundColor Yellow
Write-Host "   - Deployment Stage: Staging" -ForegroundColor White
Write-Host "   - Hybrid Search: ✅ ENABLED" -ForegroundColor Green
Write-Host "   - Query Expansion: ❌ DISABLED" -ForegroundColor Gray
Write-Host "   - Re-Ranking: ✅ ENABLED" -ForegroundColor Green
Write-Host "   - Rollout: $RolloutPercentage%" -ForegroundColor White
Write-Host ""

# Set environment variables
Write-Host "🔧 Setting environment variables..." -ForegroundColor Yellow

$env:VERITAS_DEPLOYMENT_STAGE = "staging"
$env:VERITAS_ENABLE_HYBRID_SEARCH = "true"
$env:VERITAS_ENABLE_QUERY_EXPANSION = "false"
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

# Performance Monitoring
$env:VERITAS_ENABLE_PERFORMANCE_MONITORING = "true"
$env:VERITAS_MAX_HYBRID_LATENCY_MS = "200"

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

# Optional: Index corpus for BM25
if ($CorpusPath -ne "") {
    Write-Host "📚 Indexing corpus for BM25..." -ForegroundColor Yellow
    Write-Host "   Path: $CorpusPath" -ForegroundColor White
    
    # TODO: Add corpus indexing script
    # python scripts/index_corpus_bm25.py --corpus-path "$CorpusPath"
    
    Write-Host "   ⚠️  Corpus indexing script not yet implemented" -ForegroundColor Yellow
    Write-Host "   Manual indexing required via RAGContextService.index_corpus_for_hybrid_search()" -ForegroundColor Gray
    Write-Host ""
}

# Start backend
Write-Host "🚀 Starting backend with Phase 5..." -ForegroundColor Yellow
Write-Host ""
Write-Host "   Run one of:" -ForegroundColor White
Write-Host "   1. python start_backend.py" -ForegroundColor Cyan
Write-Host "   2. Start backend manually and it will use environment variables" -ForegroundColor Cyan
Write-Host ""

# Show monitoring commands
Write-Host "📊 Monitoring Commands:" -ForegroundColor Yellow
Write-Host "   - Logs: Get-Content data/veritas_auto_server.log -Wait -Tail 50" -ForegroundColor Cyan
Write-Host "   - Performance: grep 'Phase5' data/veritas_auto_server.log | grep 'latency'" -ForegroundColor Cyan
Write-Host "   - Errors: grep 'ERROR' data/veritas_auto_server.log | grep 'Phase5'" -ForegroundColor Cyan
Write-Host ""

# Show test commands
Write-Host "🧪 Testing Commands:" -ForegroundColor Yellow
Write-Host "   - Unit Tests: pytest tests/test_phase5_hybrid_search.py -v" -ForegroundColor Cyan
Write-Host "   - Integration: pytest tests/test_phase5_integration.py -v" -ForegroundColor Cyan
Write-Host "   - Evaluation: python tests/test_phase5_evaluation.py" -ForegroundColor Cyan
Write-Host ""

# Show rollback procedure
Write-Host "⚠️  Rollback Procedure:" -ForegroundColor Yellow
Write-Host "   1. Set VERITAS_ENABLE_HYBRID_SEARCH=false" -ForegroundColor White
Write-Host "   2. Restart backend" -ForegroundColor White
Write-Host "   3. Verify metrics return to baseline" -ForegroundColor White
Write-Host ""

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "✅ Staging Phase 1 setup complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Start backend: python start_backend.py" -ForegroundColor White
Write-Host "2. Monitor latency (target: <200ms)" -ForegroundColor White
Write-Host "3. Check BM25 indexing in logs" -ForegroundColor White
Write-Host "4. Run integration tests" -ForegroundColor White
Write-Host "5. After 24h monitoring, proceed to Phase 2" -ForegroundColor White
Write-Host ""
