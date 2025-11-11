# PowerShell helper to install and initialize pre-commit for this project
# Usage: open PowerShell in project root and run:
#   .\tools\precommit-portable\setup-precommit.ps1

param(
    [string] $PythonExe = "C:\\Program Files\\Python313\\python.exe"
)

Write-Host "Using Python: $PythonExe"

# 1) Ensure pre-commit is installed
& $PythonExe -m pip install --user pre-commit | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to install pre-commit via pip. Ensure Python and pip are available."
    exit 1
}

# 2) Install git hooks (this will write .git/hooks/pre-commit)
& $PythonExe -m pre_commit install
if ($LASTEXITCODE -ne 0) {
    Write-Error "pre-commit install failed"
    exit 1
}

# 3) Run all hooks once to populate fixes/warnings
Write-Host "Running pre-commit hooks across all files (this may take a while)..."
& $PythonExe -m pre_commit run --all-files
if ($LASTEXITCODE -ne 0) {
    Write-Warning "Some hooks reported issues. Review output and re-run after fixing."
} else {
    Write-Host "pre-commit hooks completed successfully"
}

Write-Host "Setup complete. Commit and pre-commit will run automatically on future commits."