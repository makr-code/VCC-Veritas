# Start helper for VERITAS backend (PowerShell)
# Usage: In PowerShell run: .\start-backend.ps1
# Assumes a Python 3.13 virtual environment in `.venv` at repository root.
# This script activates the venv and runs uvicorn pointing at the FastAPI ASGI app.

param(
    [string]$Host = "127.0.0.1",
    [int]$Port = 8000,
    [int]$Workers = 1,
    [string]$LogLevel = "info",
    [switch]$UseUvloop
)

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Definition
Push-Location $repoRoot

# Activate venv
if (Test-Path -Path ".venv\Scripts\Activate.ps1") {
    Write-Output "Activating .venv..."
    . .\.venv\Scripts\Activate.ps1
} elseif (Test-Path -Path ".venv\Scripts\activate") {
    Write-Output "Sourcing .venv activate script..."
    . .\.venv\Scripts\activate
} else {
    Write-Warning "Virtual environment not found at .venv. Attempting to continue with current Python." 
}

# Optionally enable uvloop if installed
if ($UseUvloop) {
    try {
        py -3.13 -c "import uvloop" > $null 2>&1
        Write-Output "uvloop available; uvicorn will attempt to use it (if supported)."
    } catch {
        Write-Warning "uvloop not available in the environment. Continuing without uvloop."
    }
}

# Default uvicorn app target - adjust if your ASGI app lives elsewhere
# Common targets: `backend.main:app` or `backend.server:app` — update as needed.
$asgiTarget = "backend.main:app"

Write-Output "Starting uvicorn $asgiTarget on $Host:$Port (workers=$Workers, log=$LogLevel)"

# Use the project's python executable if available
$pythonExe = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $pythonExe)) {
    # fall back to system python
    $pythonExe = "python"
}

# Build uvicorn command
$uvicornArgs = @("-m", "uvicorn", $asgiTarget, "--host", $Host, "--port", "$Port", "--log-level", $LogLevel, "--workers", "$Workers")

# Run uvicorn
& $pythonExe @uvicornArgs

# Return to previous directory
Pop-Location
