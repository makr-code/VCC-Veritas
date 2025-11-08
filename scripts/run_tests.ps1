# PowerShell Script zum Ausführen der Test-Suite
# ==============================================

param(
    [string]$TestType = "all",  # all, unit, integration, api, websocket, lint
    [switch]$Coverage = $false,
    [switch]$Verbose = $false,
    [switch]$Parallel = $false,
    [int]$Workers = 4
)

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "ThemisDB Adapter Test Suite" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# Farbige Output-Funktion
function Write-ColorOutput {
    param([string]$Message, [string]$Color = "White")
    Write-Host $Message -ForegroundColor $Color
}

# Check ob Python vorhanden ist
try {
    $pythonVersion = python --version
    Write-ColorOutput "✓ Python gefunden: $pythonVersion" "Green"
} catch {
    Write-ColorOutput "✗ Python nicht gefunden!" "Red"
    exit 1
}

# Virtual Environment aktivieren (falls vorhanden)
if (Test-Path ".venv\Scripts\Activate.ps1") {
    Write-ColorOutput "Aktiviere Virtual Environment..." "Yellow"
    & .venv\Scripts\Activate.ps1
}

# Dependencies installieren
Write-ColorOutput "`nInstalliere Dependencies..." "Yellow"
pip install -q -r requirements.txt
pip install -q -r requirements-dev.txt

# Basis pytest Argumente
$pytestArgs = @()

if ($Verbose) {
    $pytestArgs += "-v"
}

if ($Coverage) {
    $pytestArgs += @(
        "--cov=backend",
        "--cov-report=term-missing",
        "--cov-report=html",
        "--cov-report=xml"
    )
}

if ($Parallel) {
    $pytestArgs += @("-n", $Workers)
}

# Test-Typ spezifische Argumente
switch ($TestType.ToLower()) {
    "lint" {
        Write-ColorOutput "`n=== Running Code Quality Checks ===" "Cyan"
        
        Write-ColorOutput "`n→ Black (Code Formatter Check)..." "Yellow"
        black --check backend/ tests/
        
        Write-ColorOutput "`n→ isort (Import Sorting Check)..." "Yellow"
        isort --check-only backend/ tests/
        
        Write-ColorOutput "`n→ Flake8 (Linting)..." "Yellow"
        flake8 backend/ tests/ --count --statistics
        
        Write-ColorOutput "`n→ Pylint..." "Yellow"
        pylint backend/ --exit-zero
        
        Write-ColorOutput "`n→ mypy (Type Checking)..." "Yellow"
        mypy backend/ --ignore-missing-imports
        
        Write-ColorOutput "`n→ Bandit (Security)..." "Yellow"
        bandit -r backend/ -ll
    }
    
    "unit" {
        Write-ColorOutput "`n=== Running Unit Tests ===" "Cyan"
        $pytestArgs += @("-m", "unit or not (integration or e2e)")
        pytest @pytestArgs tests/
    }
    
    "integration" {
        Write-ColorOutput "`n=== Running Integration Tests ===" "Cyan"
        $pytestArgs += @("-m", "integration")
        pytest @pytestArgs tests/
    }
    
    "api" {
        Write-ColorOutput "`n=== Running API Tests ===" "Cyan"
        $pytestArgs += @(
            "tests/test_themis_router.py",
            "tests/test_adapter_router.py"
        )
        pytest @pytestArgs
    }
    
    "websocket" {
        Write-ColorOutput "`n=== Running WebSocket Tests ===" "Cyan"
        $pytestArgs += "tests/test_websocket_router.py"
        pytest @pytestArgs
    }
    
    "adapter" {
        Write-ColorOutput "`n=== Running Adapter Tests ===" "Cyan"
        $pytestArgs += "tests/test_themisdb_adapter.py"
        pytest @pytestArgs
    }
    
    "all" {
        Write-ColorOutput "`n=== Running All Tests ===" "Cyan"
        
        # 1. Linting
        Write-ColorOutput "`n→ Step 1: Code Quality Checks" "Yellow"
        & $PSCommandPath -TestType "lint"
        
        # 2. Unit Tests
        Write-ColorOutput "`n→ Step 2: Unit Tests" "Yellow"
        $pytestArgs += @("-m", "not integration and not e2e")
        pytest @pytestArgs tests/
        
        # 3. Integration Tests
        Write-ColorOutput "`n→ Step 3: Integration Tests" "Yellow"
        & $PSCommandPath -TestType "integration" -Verbose:$Verbose
        
        # 4. API Tests
        Write-ColorOutput "`n→ Step 4: API Tests" "Yellow"
        & $PSCommandPath -TestType "api" -Verbose:$Verbose
        
        # 5. WebSocket Tests
        Write-ColorOutput "`n→ Step 5: WebSocket Tests" "Yellow"
        & $PSCommandPath -TestType "websocket" -Verbose:$Verbose
    }
    
    default {
        Write-ColorOutput "Unknown test type: $TestType" "Red"
        Write-ColorOutput "Available types: all, unit, integration, api, websocket, adapter, lint" "Yellow"
        exit 1
    }
}

# Summary
Write-ColorOutput "`n================================================" "Cyan"
if ($LASTEXITCODE -eq 0) {
    Write-ColorOutput "✓ All tests passed!" "Green"
} else {
    Write-ColorOutput "✗ Some tests failed!" "Red"
}
Write-ColorOutput "================================================" "Cyan"

# Coverage Report
if ($Coverage -and (Test-Path "htmlcov/index.html")) {
    Write-ColorOutput "`nCoverage Report: htmlcov/index.html" "Yellow"
    Start-Process "htmlcov/index.html"
}

exit $LASTEXITCODE
