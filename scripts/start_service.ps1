# Wrapper-Skript: Aufrufkompatibilität
# Leitet auf start_services.ps1 weiter

param(
    [switch]$BackendOnly,
    [switch]$FrontendOnly
)

$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$target = Join-Path $scriptRoot 'start_services.ps1'
if (-not (Test-Path $target)) {
    Write-Host "start_services.ps1 nicht gefunden im scripts-Verzeichnis." -ForegroundColor Red
    exit 1
}

& powershell -NoProfile -ExecutionPolicy Bypass -File $target @PSBoundParameters
exit $LASTEXITCODE
