#!/usr/bin/env powershell
# Phase 4: Link Fixing - Update broken links due to file consolidation

param([string]$Mode = "analyze")

$docsPath = "docs"

# Map old locations to new locations
$linkMaps = @{
    "getting-started/QUICK_START" = "getting-started/QUICK_START"
    "api/VERITAS_API" = "api/VERITAS_API"
    "architecture/BACKEND_ARCH" = "architecture/BACKEND_ARCH"
    "components/DATABASE_AGENT" = "components/DATABASE_AGENT"
    "integration/UDS3_INTEGRATION" = "integration/UDS3_INTEGRATION"
    "deployment/QUICKSTART" = "deployment/QUICKSTART"
}

# Common link patterns that need fixing
$linkPatterns = @(
    @{old = "QUICK_START\.md"; new = "getting-started/QUICK_START.md"}
    @{old = "\[API\]\((.*?)VERITAS_API"; new = "[API](../api/VERITAS_API"}
    @{old = "BACKEND_ARCH\.md"; new = "architecture/BACKEND_ARCH.md"}
    @{old = "DATABASE_AGENT\.md"; new = "components/DATABASE_AGENT.md"}
    @{old = "UDS3_INTEGRATION\.md"; new = "integration/UDS3_INTEGRATION.md"}
)

function Analyze-Links {
    Write-Host "`n📊 ANALYZING INTERNAL LINKS`n" -ForegroundColor Cyan
    
    $files = Get-ChildItem -Path $docsPath -File -Filter "*.md" -Recurse -ErrorAction SilentlyContinue
    $brokenLinks = @()
    
    foreach ($file in $files) {
        $content = Get-Content -Path $file.FullName -Raw -ErrorAction SilentlyContinue
        
        # Look for markdown links: [text](path)
        $linkRegex = '\[([^\]]+)\]\(([^)]+)\)'
        $matches = [regex]::Matches($content, $linkRegex)
        
        foreach ($match in $matches) {
            $linkText = $match.Groups[1].Value
            $linkPath = $match.Groups[2].Value
            
            # Skip external links and anchors
            if ($linkPath -match "^(http|#|mailto:)") {
                continue
            }
            
            # Resolve relative path
            $linkPathFull = Join-Path (Split-Path $file.FullName) $linkPath
            $linkPathFull = [System.IO.Path]::GetFullPath($linkPathFull)
            
            # Check if link target exists
            if (-not (Test-Path $linkPathFull -ErrorAction SilentlyContinue)) {
                $brokenLinks += @{
                    file = $file.Name
                    filePath = $file.FullName
                    linkText = $linkText
                    linkPath = $linkPath
                }
            }
        }
    }
    
    Write-Host "Found $($brokenLinks.Count) potential broken links`n" -ForegroundColor Yellow
    
    if ($brokenLinks.Count -gt 0) {
        Write-Host "BROKEN LINKS BY FILE:`n" -ForegroundColor Red
        $brokenLinks | Group-Object -Property file | ForEach-Object {
            Write-Host "  📄 $($_.Name): $($_.Count) broken links"
            $_.Group | ForEach-Object {
                Write-Host "     - [$($_.linkText)]($($_.linkPath))" -ForegroundColor DarkGray
            }
        }
    }
    
    return $brokenLinks
}

function Fix-Links {
    Write-Host "`n⚙️  FIXING LINKS`n" -ForegroundColor Cyan
    
    $files = Get-ChildItem -Path $docsPath -File -Filter "*.md" -Recurse -ErrorAction SilentlyContinue
    $fixedCount = 0
    
    foreach ($file in $files) {
        $content = Get-Content -Path $file.FullName -Raw -ErrorAction SilentlyContinue
        $originalContent = $content
        
        # Apply fixes
        foreach ($pattern in $linkPatterns) {
            if ($content -match $pattern.old) {
                $content = $content -replace $pattern.old, $pattern.new
            }
        }
        
        # Write back if changed
        if ($content -ne $originalContent) {
            Set-Content -Path $file.FullName -Value $content -ErrorAction SilentlyContinue
            $fixedCount++
            Write-Host "✓ Fixed links in: $($file.Name)" -ForegroundColor Green
        }
    }
    
    Write-Host "`n✅ Fixed $fixedCount files" -ForegroundColor Green
}

function Validate-Links {
    Write-Host "`n✅ VALIDATING LINKS`n" -ForegroundColor Cyan
    
    $files = Get-ChildItem -Path $docsPath -File -Filter "*.md" -Recurse -ErrorAction SilentlyContinue
    $totalLinks = 0
    $brokenCount = 0
    
    foreach ($file in $files) {
        $content = Get-Content -Path $file.FullName -Raw -ErrorAction SilentlyContinue
        $linkRegex = '\[([^\]]+)\]\(([^)]+)\)'
        $matches = [regex]::Matches($content, $linkRegex)
        
        foreach ($match in $matches) {
            $linkPath = $match.Groups[2].Value
            
            if ($linkPath -match "^(http|#|mailto:)") {
                continue
            }
            
            $totalLinks++
            $linkPathFull = Join-Path (Split-Path $file.FullName) $linkPath
            $linkPathFull = [System.IO.Path]::GetFullPath($linkPathFull)
            
            if (-not (Test-Path $linkPathFull -ErrorAction SilentlyContinue)) {
                $brokenCount++
            }
        }
    }
    
    Write-Host "📊 LINK VALIDATION REPORT:`n" -ForegroundColor Cyan
    Write-Host "  Total Links: $totalLinks" -ForegroundColor DarkGray
    Write-Host "  Broken Links: $brokenCount" -ForegroundColor $(if ($brokenCount -eq 0) { "Green" } else { "Yellow" })
    Write-Host "  Health: $(100 - [math]::Round(($brokenCount / $totalLinks) * 100))%" -ForegroundColor $(if ($brokenCount -eq 0) { "Green" } else { "Yellow" })
}

# Main
switch ($Mode) {
    "analyze" {
        Analyze-Links
    }
    "fix" {
        Fix-Links
    }
    "validate" {
        Validate-Links
    }
    default {
        Write-Host @"

PHASE 4: LINK FIXING

USAGE: .\phase4-fix-links.ps1 -Mode <mode>

MODES:
  analyze   - Find broken links
  fix       - Attempt to fix links
  validate  - Check link health

"@
    }
}

Write-Host "`n"
