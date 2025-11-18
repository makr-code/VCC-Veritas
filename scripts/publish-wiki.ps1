<<<<<<< Updated upstream
﻿<#!.SYNOPSIS  Generiert Sidebars und ver├Âffentlicht die Inhalte aus `docs/` ins GitHub Wiki..DESCRIPTION  Funktionsumfang (kombiniert):  1. Optional: Generiert/aktualisiert Auto-Abschnitte in `_sidebar.md` (Docsify) und `_Sidebar.md` (Wiki) mittels Marker `<!-- AUTO:EXTRA_DOCS:BEGIN -->` / `END`.  2. Klont das Wiki-Repository (`*.wiki.git`) in ein tempor├ñres Arbeitsverzeichnis.  3. Kopiert alle Markdown-Dateien sowie erkannte Asset-Ordner (assets,img,images,media).  4. Mappt README.md -> Home.md; bevorzugt `_Sidebar.md` gegen├╝ber `_sidebar.md`.  5. Commit + Push, falls ├änderungen vorhanden..PARAMETER RepoOwner  GitHub Owner/Organisation (Default: makr-code).PARAMETER RepoName  GitHub Repository-Name (Default: VCC-Veritas).PARAMETER DocsPath  Pfad zum lokalen docs/-Ordner (Default: <repo>/docs).PARAMETER WorkDir  Tempor├ñres Arbeitsverzeichnis f├╝r das Wiki (Default: $env:TEMP/<RepoName>.wiki.work).PARAMETER AssetFolders  Ordnerliste f├╝r statische Assets, wird rekursiv kopiert (Default: assets,img,images,media).PARAMETER SkipSidebarGeneration  Wenn gesetzt, wird die automatische Sidebar-Erweiterung ├╝bersprungen..ENVIRONMENT  Erfordert einen GitHub Token mit 'repo' Scope in $env:GITHUB_TOKEN oder $env:GH_TOKEN..EXAMPLE  powershell -ExecutionPolicy Bypass -File .\scripts\publish-wiki.ps1.EXAMPLE  powershell -ExecutionPolicy Bypass -File .\scripts\publish-wiki.ps1 -SkipSidebarGeneration  F├╝hrt nur Publish aus (kein Sidebar-Update).#>[CmdletBinding()]param(  [string]$RepoOwner = 'makr-code',  [string]$RepoName = 'VCC-Veritas',  [string]$DocsPath = (Join-Path $PSScriptRoot '..' 'docs'),  [string]$WorkDir,  [string[]]$AssetFolders = @('assets','img','images','media'),  [switch]$SkipSidebarGeneration)Set-StrictMode -Version Latest$ErrorActionPreference = 'Stop'function Resolve-FullPath([string]$Path) { (Resolve-Path -Path $Path).Path }function Ensure-Command([string]$Name) { if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) { throw "Erforderliches Tool nicht gefunden: $Name" } }# --- Sidebar Generation Functions (merged from generate-sidebar.ps1) ---function Get-MarkdownFiles([string]$base) { Get-ChildItem -Path $base -Recurse -File | Where-Object { $_.Extension -ieq '.md' } }function Get-ReferencedFilesFromDocsifySidebar([string]$content) {  $refs = New-Object System.Collections.Generic.HashSet[string]  $pattern = '\[[^\]]+\]\(([^)]+\.md)\)'  foreach ($m in [regex]::Matches($content, $pattern)) { [void]$refs.Add(($m.Groups[1].Value.Trim())) }  return $refs}function Get-ReferencedFilesFromWikiSidebar([string]$content) {  $refs = New-Object System.Collections.Generic.HashSet[string]  $pattern = '\[\[([^\]]+)\]\]'  foreach ($m in [regex]::Matches($content, $pattern)) {    $name = $m.Groups[1].Value.Trim()    if (-not [string]::IsNullOrWhiteSpace($name)) { [void]$refs.Add("$name.md") }  }  return $refs}function Replace-AutoSection([string]$content, [string[]]$lines) {  $begin = '<!-- AUTO:EXTRA_DOCS:BEGIN -->'  $end = '<!-- AUTO:EXTRA_DOCS:END -->'  $autoBlock = @($begin) + $lines + @($end)  if ($content -match [regex]::Escape($begin) -and $content -match [regex]::Escape($end)) {    $pattern = [regex]::Escape($begin) + '.*?' + [regex]::Escape($end)    return ([regex]::Replace($content, $pattern, [string]::Join("`n", $autoBlock), 'Singleline'))  } else {    return ($content.TrimEnd() + "`n`n" + [string]::Join("`n", $autoBlock) + "`n")  }}function Invoke-GenerateSidebars([string]$DocsPath) {  $all = Get-MarkdownFiles $DocsPath  $relAll = $all | ForEach-Object { $_.FullName.Substring($DocsPath.Length).TrimStart('\\','/') }  $exclude = @('_Sidebar.md','_sidebar.md','README.md','Home.md')  $relAll = $relAll | Where-Object { $exclude -notcontains $_ }  $sidebarPath = Join-Path $DocsPath '_sidebar.md'  $sidebarContent = ''  $referencedDocsify = New-Object System.Collections.Generic.HashSet[string]  if (Test-Path $sidebarPath) {    $sidebarContent = Get-Content -Path $sidebarPath -Raw    $referencedDocsify = Get-ReferencedFilesFromDocsifySidebar $sidebarContent    [void]$referencedDocsify.Add('README.md')  }  $wikiSidebarPath = Join-Path $DocsPath '_Sidebar.md'  $wikiSidebarContent = ''  $referencedWiki = New-Object System.Collections.Generic.HashSet[string]  if (Test-Path $wikiSidebarPath) {    $wikiSidebarContent = Get-Content -Path $wikiSidebarPath -Raw    $referencedWiki = Get-ReferencedFilesFromWikiSidebar $wikiSidebarContent    [void]$referencedWiki.Add('Home.md'); [void]$referencedWiki.Add('README.md')  }  $extraDocsify = @(); foreach ($rel in $relAll) { if (-not $referencedDocsify.Contains($rel)) { $extraDocsify += $rel } }  $extraWiki = @(); foreach ($rel in $relAll) { $name = [System.IO.Path]::GetFileName($rel); if (-not $referencedWiki.Contains($name)) { $extraWiki += $name } }  $docsifyLines = @('','* Weitere Dokumente'); foreach ($rel in ($extraDocsify | Sort-Object)) { $display = [System.IO.Path]::GetFileNameWithoutExtension($rel); $encodedRel = $rel -replace '\\','/'; $docsifyLines += "  * [$display]($encodedRel)" }  $wikiLines = @('','* Weitere Dokumente'); foreach ($name in ($extraWiki | Sort-Object)) { $display = [System.IO.Path]::GetFileNameWithoutExtension($name); $wikiLines += "  * [[${display}]]" }  if ($sidebarContent) { $sidebarNew = Replace-AutoSection $sidebarContent $docsifyLines; if ($sidebarNew -ne $sidebarContent) { Set-Content -Path $sidebarPath -Value $sidebarNew -NoNewline } }  if ($wikiSidebarContent) { $wikiNew = Replace-AutoSection $wikiSidebarContent $wikiLines; if ($wikiNew -ne $wikiSidebarContent) { Set-Content -Path $wikiSidebarPath -Value $wikiNew -NoNewline } }  Write-Host 'Sidebars generiert/aktualisiert.' -ForegroundColor Cyan}try {  Ensure-Command git  if (-not (Test-Path $DocsPath)) {    throw "DocsPath nicht gefunden: $DocsPath"  }  $DocsPath = Resolve-FullPath $DocsPath  if (-not $SkipSidebarGeneration) {    Invoke-GenerateSidebars -DocsPath $DocsPath  } else {    Write-Host '├£berspringe Sidebar-Generierung (Parameter gesetzt).' -ForegroundColor Yellow  }  $token = $env:GITHUB_TOKEN  if (-not $token) { $token = $env:GH_TOKEN }  if (-not $token) {    throw 'Bitte Umgebungsvariable GITHUB_TOKEN oder GH_TOKEN mit repo-Rechten setzen.'  }  if (-not $WorkDir) {    $WorkDir = Join-Path $env:TEMP ("{0}.wiki.work" -f $RepoName)  }  if (Test-Path $WorkDir) {    Remove-Item -Path $WorkDir -Recurse -Force -ErrorAction SilentlyContinue  }  New-Item -ItemType Directory -Path $WorkDir | Out-Null  $WorkDir = Resolve-FullPath $WorkDir  $wikiUrl = "https://${token}@github.com/${RepoOwner}/${RepoName}.wiki.git"  Write-Host "Clonen des Wiki-Repos nach" $WorkDir  git clone $wikiUrl $WorkDir | Out-Null  # Alles au├ƒer .git im Wiki-Workdir l├Âschen  Get-ChildItem -Path $WorkDir -Force | Where-Object { $_.Name -ne '.git' } | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue  # Markdown-Dateien rekursiv kopieren und Ordnerstruktur erhalten  $mdFiles = Get-ChildItem -Path $DocsPath -Recurse -File | Where-Object { $_.Extension -ieq '.md' }  foreach ($file in $mdFiles) {    $rel = (Resolve-Path $file.FullName).Path.Substring($DocsPath.Length).TrimStart('\\','/')    $dest = Join-Path $WorkDir $rel    $destDir = Split-Path -Parent $dest    if (-not (Test-Path $destDir)) { New-Item -ItemType Directory -Path $destDir -Force | Out-Null }    Copy-Item -Path $file.FullName -Destination $dest -Force  }  # Assets kopieren (Bilder/Medien)  foreach ($folder in $AssetFolders) {    $src = Join-Path $DocsPath $folder    if (Test-Path $src) {      $dest = Join-Path $WorkDir $folder      if (Test-Path $dest) { Remove-Item -Path $dest -Recurse -Force -ErrorAction SilentlyContinue }      Copy-Item -Path $src -Destination $dest -Recurse -Force    }  }  # README.md -> Home.md mappen (Root der Wiki)  $readmePath = Join-Path $DocsPath 'README.md'  if (Test-Path $readmePath) {    Copy-Item -Path $readmePath -Destination (Join-Path $WorkDir 'Home.md') -Force  }  # _Sidebar.md bevorzugen; Fallback auf _sidebar.md (GitHub Wiki Konvention, Root)  $sidebarUpper = Join-Path $DocsPath '_Sidebar.md'  $sidebarLower = Join-Path $DocsPath '_sidebar.md'  if (Test-Path $sidebarUpper) {    Copy-Item -Path $sidebarUpper -Destination (Join-Path $WorkDir '_Sidebar.md') -Force  } elseif (Test-Path $sidebarLower) {    Copy-Item -Path $sidebarLower -Destination (Join-Path $WorkDir '_Sidebar.md') -Force  }  # Optional: _Footer.md/_Header.md k├Ânnten hier ebenfalls gemappt werden, falls vorhanden  # Git User konfigurieren (falls nicht gesetzt)  git -C $WorkDir config user.name | Out-Null 2>$null  if ($LASTEXITCODE -ne 0) {    git -C $WorkDir config user.name 'veritas-docs-bot' | Out-Null  }  git -C $WorkDir config user.email | Out-Null 2>$null  if ($LASTEXITCODE -ne 0) {    git -C $WorkDir config user.email 'veritas-docs-bot@example.local' | Out-Null  }  # ├änderungen committen und pushen  git -C $WorkDir add -A  $status = git -C $WorkDir status --porcelain  if (-not [string]::IsNullOrWhiteSpace($status)) {    $msg = "docs: publish to wiki from docs/ on $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"    git -C $WorkDir commit -m $msg | Out-Null    # Standard-Wiki-Branch ist meist 'master'    git -C $WorkDir push origin HEAD:master    Write-Host "Wiki aktualisiert und gepusht." -ForegroundColor Green  } else {    Write-Host "Keine ├änderungen zu ver├Âffentlichen." -ForegroundColor Yellow  }} catch {  Write-Error $_  exit 1}
=======
<#!
.SYNOPSIS
  Generiert Sidebars und veröffentlicht die Inhalte aus `docs/` ins GitHub Wiki.

.DESCRIPTION
  Funktionsumfang (kombiniert):
  1. Optional: Generiert/aktualisiert Auto-Abschnitte in `_sidebar.md` (Docsify) und `_Sidebar.md` (Wiki) mittels Marker `<!-- AUTO:EXTRA_DOCS:BEGIN -->` / `END`.
  2. Klont das Wiki-Repository (`*.wiki.git`) in ein temporäres Arbeitsverzeichnis.
  3. Kopiert alle Markdown-Dateien sowie erkannte Asset-Ordner (assets,img,images,media).
  4. Mappt README.md -> Home.md; bevorzugt `_Sidebar.md` gegenüber `_sidebar.md`.
  5. Commit + Push, falls Änderungen vorhanden.

.PARAMETER RepoOwner
  GitHub Owner/Organisation (Default: makr-code)

.PARAMETER RepoName
  GitHub Repository-Name (Default: VCC-Veritas)

.PARAMETER DocsPath
  Pfad zum lokalen docs/-Ordner (Default: <repo>/docs)

.PARAMETER WorkDir
  Temporäres Arbeitsverzeichnis für das Wiki (Default: $env:TEMP/<RepoName>.wiki.work)

.PARAMETER AssetFolders
  Ordnerliste für statische Assets, wird rekursiv kopiert (Default: assets,img,images,media)

.PARAMETER SkipSidebarGeneration
  Wenn gesetzt, wird die automatische Sidebar-Erweiterung übersprungen.

.ENVIRONMENT
  Erfordert einen GitHub Token mit 'repo' Scope in $env:GITHUB_TOKEN oder $env:GH_TOKEN.

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File .\scripts\publish-wiki.ps1

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File .\scripts\publish-wiki.ps1 -SkipSidebarGeneration
  Führt nur Publish aus (kein Sidebar-Update).
#>

[CmdletBinding()]
param(
  [string]$RepoOwner = 'makr-code',
  [string]$RepoName = 'VCC-Veritas',
  [string]$DocsPath = (Join-Path $PSScriptRoot '..' 'docs'),
  [string]$WorkDir,
  [string[]]$AssetFolders = @('assets','img','images','media'),
  [switch]$SkipSidebarGeneration
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Resolve-FullPath([string]$Path) { (Resolve-Path -Path $Path).Path }
function Ensure-Command([string]$Name) { if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) { throw "Erforderliches Tool nicht gefunden: $Name" } }

# --- Sidebar Generation Functions (merged from generate-sidebar.ps1) ---
function Get-MarkdownFiles([string]$base) { Get-ChildItem -Path $base -Recurse -File | Where-Object { $_.Extension -ieq '.md' } }
function Get-ReferencedFilesFromDocsifySidebar([string]$content) {
  $refs = New-Object System.Collections.Generic.HashSet[string]
  $pattern = '\[[^\]]+\]\(([^)]+\.md)\)'
  foreach ($m in [regex]::Matches($content, $pattern)) { [void]$refs.Add(($m.Groups[1].Value.Trim())) }
  return $refs
}
function Get-ReferencedFilesFromWikiSidebar([string]$content) {
  $refs = New-Object System.Collections.Generic.HashSet[string]
  $pattern = '\[\[([^\]]+)\]\]'
  foreach ($m in [regex]::Matches($content, $pattern)) {
    $name = $m.Groups[1].Value.Trim()
    if (-not [string]::IsNullOrWhiteSpace($name)) { [void]$refs.Add("$name.md") }
  }
  return $refs
}
function Replace-AutoSection([string]$content, [string[]]$lines) {
  $begin = '<!-- AUTO:EXTRA_DOCS:BEGIN -->'
  $end = '<!-- AUTO:EXTRA_DOCS:END -->'
  $autoBlock = @($begin) + $lines + @($end)
  if ($content -match [regex]::Escape($begin) -and $content -match [regex]::Escape($end)) {
    $pattern = [regex]::Escape($begin) + '.*?' + [regex]::Escape($end)
    return ([regex]::Replace($content, $pattern, [string]::Join("`n", $autoBlock), 'Singleline'))
  } else {
    return ($content.TrimEnd() + "`n`n" + [string]::Join("`n", $autoBlock) + "`n")
  }
}
function Invoke-GenerateSidebars([string]$DocsPath) {
  $all = Get-MarkdownFiles $DocsPath
  $relAll = $all | ForEach-Object { $_.FullName.Substring($DocsPath.Length).TrimStart('\\','/') }
  $exclude = @('_Sidebar.md','_sidebar.md','README.md','Home.md')
  $relAll = $relAll | Where-Object { $exclude -notcontains $_ }
  $sidebarPath = Join-Path $DocsPath '_sidebar.md'
  $sidebarContent = ''
  $referencedDocsify = New-Object System.Collections.Generic.HashSet[string]
  if (Test-Path $sidebarPath) {
    $sidebarContent = Get-Content -Path $sidebarPath -Raw
    $referencedDocsify = Get-ReferencedFilesFromDocsifySidebar $sidebarContent
    [void]$referencedDocsify.Add('README.md')
  }
  $wikiSidebarPath = Join-Path $DocsPath '_Sidebar.md'
  $wikiSidebarContent = ''
  $referencedWiki = New-Object System.Collections.Generic.HashSet[string]
  if (Test-Path $wikiSidebarPath) {
    $wikiSidebarContent = Get-Content -Path $wikiSidebarPath -Raw
    $referencedWiki = Get-ReferencedFilesFromWikiSidebar $wikiSidebarContent
    [void]$referencedWiki.Add('Home.md'); [void]$referencedWiki.Add('README.md')
  }
  $extraDocsify = @(); foreach ($rel in $relAll) { if (-not $referencedDocsify.Contains($rel)) { $extraDocsify += $rel } }
  $extraWiki = @(); foreach ($rel in $relAll) { $name = [System.IO.Path]::GetFileName($rel); if (-not $referencedWiki.Contains($name)) { $extraWiki += $name } }
  $docsifyLines = @('','* Weitere Dokumente'); foreach ($rel in ($extraDocsify | Sort-Object)) { $display = [System.IO.Path]::GetFileNameWithoutExtension($rel); $encodedRel = $rel -replace '\\','/'; $docsifyLines += "  * [$display]($encodedRel)" }
  $wikiLines = @('','* Weitere Dokumente'); foreach ($name in ($extraWiki | Sort-Object)) { $display = [System.IO.Path]::GetFileNameWithoutExtension($name); $wikiLines += "  * [[${display}]]" }
  if ($sidebarContent) { $sidebarNew = Replace-AutoSection $sidebarContent $docsifyLines; if ($sidebarNew -ne $sidebarContent) { Set-Content -Path $sidebarPath -Value $sidebarNew -NoNewline } }
  if ($wikiSidebarContent) { $wikiNew = Replace-AutoSection $wikiSidebarContent $wikiLines; if ($wikiNew -ne $wikiSidebarContent) { Set-Content -Path $wikiSidebarPath -Value $wikiNew -NoNewline } }
  Write-Host 'Sidebars generiert/aktualisiert.' -ForegroundColor Cyan
}

try {
  Ensure-Command git

  if (-not (Test-Path $DocsPath)) {
    throw "DocsPath nicht gefunden: $DocsPath"
  }
  $DocsPath = Resolve-FullPath $DocsPath

  if (-not $SkipSidebarGeneration) {
    Invoke-GenerateSidebars -DocsPath $DocsPath
  } else {
    Write-Host 'Überspringe Sidebar-Generierung (Parameter gesetzt).' -ForegroundColor Yellow
  }

  $token = $env:GITHUB_TOKEN
  if (-not $token) { $token = $env:GH_TOKEN }
  if (-not $token) {
    throw 'Bitte Umgebungsvariable GITHUB_TOKEN oder GH_TOKEN mit repo-Rechten setzen.'
  }

  if (-not $WorkDir) {
    $WorkDir = Join-Path $env:TEMP ("{0}.wiki.work" -f $RepoName)
  }
  if (Test-Path $WorkDir) {
    Remove-Item -Path $WorkDir -Recurse -Force -ErrorAction SilentlyContinue
  }
  New-Item -ItemType Directory -Path $WorkDir | Out-Null
  $WorkDir = Resolve-FullPath $WorkDir

  $wikiUrl = "https://${token}@github.com/${RepoOwner}/${RepoName}.wiki.git"

  Write-Host "Clonen des Wiki-Repos nach" $WorkDir
  git clone $wikiUrl $WorkDir | Out-Null

  # Alles außer .git im Wiki-Workdir löschen
  Get-ChildItem -Path $WorkDir -Force | Where-Object { $_.Name -ne '.git' } | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue

  # Markdown-Dateien rekursiv kopieren und Ordnerstruktur erhalten
  $mdFiles = Get-ChildItem -Path $DocsPath -Recurse -File | Where-Object { $_.Extension -ieq '.md' }
  foreach ($file in $mdFiles) {
    $rel = (Resolve-Path $file.FullName).Path.Substring($DocsPath.Length).TrimStart('\\','/')
    $dest = Join-Path $WorkDir $rel
    $destDir = Split-Path -Parent $dest
    if (-not (Test-Path $destDir)) { New-Item -ItemType Directory -Path $destDir -Force | Out-Null }
    Copy-Item -Path $file.FullName -Destination $dest -Force
  }

  # Assets kopieren (Bilder/Medien)
  foreach ($folder in $AssetFolders) {
    $src = Join-Path $DocsPath $folder
    if (Test-Path $src) {
      $dest = Join-Path $WorkDir $folder
      if (Test-Path $dest) { Remove-Item -Path $dest -Recurse -Force -ErrorAction SilentlyContinue }
      Copy-Item -Path $src -Destination $dest -Recurse -Force
    }
  }

  # README.md -> Home.md mappen (Root der Wiki)
  $readmePath = Join-Path $DocsPath 'README.md'
  if (Test-Path $readmePath) {
    Copy-Item -Path $readmePath -Destination (Join-Path $WorkDir 'Home.md') -Force
  }

  # _Sidebar.md bevorzugen; Fallback auf _sidebar.md (GitHub Wiki Konvention, Root)
  $sidebarUpper = Join-Path $DocsPath '_Sidebar.md'
  $sidebarLower = Join-Path $DocsPath '_sidebar.md'
  if (Test-Path $sidebarUpper) {
    Copy-Item -Path $sidebarUpper -Destination (Join-Path $WorkDir '_Sidebar.md') -Force
  } elseif (Test-Path $sidebarLower) {
    Copy-Item -Path $sidebarLower -Destination (Join-Path $WorkDir '_Sidebar.md') -Force
  }

  # Optional: _Footer.md/_Header.md könnten hier ebenfalls gemappt werden, falls vorhanden

  # Git User konfigurieren (falls nicht gesetzt)
  git -C $WorkDir config user.name | Out-Null 2>$null
  if ($LASTEXITCODE -ne 0) {
    git -C $WorkDir config user.name 'veritas-docs-bot' | Out-Null
  }
  git -C $WorkDir config user.email | Out-Null 2>$null
  if ($LASTEXITCODE -ne 0) {
    git -C $WorkDir config user.email 'veritas-docs-bot@example.local' | Out-Null
  }

  # Änderungen committen und pushen
  git -C $WorkDir add -A
  $status = git -C $WorkDir status --porcelain
  if (-not [string]::IsNullOrWhiteSpace($status)) {
    $msg = "docs: publish to wiki from docs/ on $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
    git -C $WorkDir commit -m $msg | Out-Null
    # Standard-Wiki-Branch ist meist 'master'
    git -C $WorkDir push origin HEAD:master
    Write-Host "Wiki aktualisiert und gepusht." -ForegroundColor Green
  } else {
    Write-Host "Keine Änderungen zu veröffentlichen." -ForegroundColor Yellow
  }

} catch {
  Write-Error $_
  exit 1
}
>>>>>>> Stashed changes
