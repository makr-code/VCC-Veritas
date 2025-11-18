<#!
.SYNOPSIS
  Generiert bzw. ergänzt Sidebars für Docsify (`_sidebar.md`) und GitHub Wiki (`_Sidebar.md`).

.DESCRIPTION
  - Liest bestehende Sidebar (falls vorhanden) und ermittelt bereits verlinkte Dateien
  - Sucht alle weiteren `.md` Dateien unter `docs/` und ergänzt sie unter einem Auto-Abschnitt
  - Schreibt die Auto-Sektionen zwischen `<!-- AUTO:EXTRA_DOCS:BEGIN -->` und `<!-- AUTO:EXTRA_DOCS:END -->`

.PARAMETER DocsPath
  Pfad zum docs-Ordner (Default: <repo>/docs)

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File .\scripts\generate-sidebar.ps1
#>

[CmdletBinding()]
param(
  [string]$DocsPath = (Join-Path $PSScriptRoot '..' 'docs')
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Resolve-FullPath([string]$Path) { (Resolve-Path -Path $Path).Path }

function Get-MarkdownFiles([string]$base) {
  Get-ChildItem -Path $base -Recurse -File | Where-Object { $_.Extension -ieq '.md' }
}

function Get-ReferencedFilesFromDocsifySidebar([string]$content) {
  $refs = New-Object System.Collections.Generic.HashSet[string]
  $pattern = '\[[^\]]+\]\(([^)]+\.md)\)'
  foreach ($m in [regex]::Matches($content, $pattern)) {
    [void]$refs.Add(($m.Groups[1].Value.Trim()))
  }
  return $refs
}

function Get-ReferencedFilesFromWikiSidebar([string]$content) {
  $refs = New-Object System.Collections.Generic.HashSet[string]
  # [[PageName]] -> PageName.md (Heuristik)
  $pattern = '\[\[([^\]]+)\]\]'
  foreach ($m in [regex]::Matches($content, $pattern)) {
    $name = $m.Groups[1].Value.Trim()
    if (-not [string]::IsNullOrWhiteSpace($name)) {
      [void]$refs.Add("$name.md")
    }
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

try {
  if (-not (Test-Path $DocsPath)) { throw "DocsPath nicht gefunden: $DocsPath" }
  $DocsPath = Resolve-FullPath $DocsPath

  $all = Get-MarkdownFiles $DocsPath

  # Dateien relativ zu docs
  $relAll = $all | ForEach-Object {
    $_.FullName.Substring($DocsPath.Length).TrimStart('\\','/')
  }

  # Excludes
  $exclude = @('_Sidebar.md','_sidebar.md','README.md','Home.md')
  $relAll = $relAll | Where-Object { $exclude -notcontains $_ }

  # --- Docsify Sidebar ---
  $sidebarPath = Join-Path $DocsPath '_sidebar.md'
  $sidebarContent = ''
  $referencedDocsify = New-Object System.Collections.Generic.HashSet[string]
  if (Test-Path $sidebarPath) {
    $sidebarContent = Get-Content -Path $sidebarPath -Raw
    $referencedDocsify = Get-ReferencedFilesFromDocsifySidebar $sidebarContent
    # Startseite auslassen
    [void]$referencedDocsify.Add('README.md')
  }

  # --- Wiki Sidebar ---
  $wikiSidebarPath = Join-Path $DocsPath '_Sidebar.md'
  $wikiSidebarContent = ''
  $referencedWiki = New-Object System.Collections.Generic.HashSet[string]
  if (Test-Path $wikiSidebarPath) {
    $wikiSidebarContent = Get-Content -Path $wikiSidebarPath -Raw
    $referencedWiki = Get-ReferencedFilesFromWikiSidebar $wikiSidebarContent
    # Home.md/README.md sind Startseiten – exklusiv behandeln
    [void]$referencedWiki.Add('Home.md')
    [void]$referencedWiki.Add('README.md')
  }

  # Zusätzliche Dateien ermitteln
  $extraDocsify = @()
  foreach ($rel in $relAll) {
    # bereits referenziert?
    if (-not $referencedDocsify.Contains($rel)) { $extraDocsify += $rel }
  }
  $extraWiki = @()
  foreach ($rel in $relAll) {
    $name = [System.IO.Path]::GetFileName($rel)
    if (-not $referencedWiki.Contains($name)) { $extraWiki += $name }
  }

  # Auto-Abschnitte bauen
  $docsifyLines = @('','* Weitere Dokumente')
  foreach ($rel in ($extraDocsify | Sort-Object)) {
    $display = [System.IO.Path]::GetFileNameWithoutExtension($rel)
    $encodedRel = $rel -replace '\\','/'
    $docsifyLines += "  * [$display]($encodedRel)"
  }

  $wikiLines = @('','* Weitere Dokumente')
  foreach ($name in ($extraWiki | Sort-Object)) {
    $display = [System.IO.Path]::GetFileNameWithoutExtension($name)
    $wikiLines += "  * [[${display}]]"
  }

  if ($sidebarContent) {
    $sidebarNew = Replace-AutoSection $sidebarContent $docsifyLines
    if ($sidebarNew -ne $sidebarContent) {
      Set-Content -Path $sidebarPath -Value $sidebarNew -NoNewline
    }
  }

  if ($wikiSidebarContent) {
    $wikiNew = Replace-AutoSection $wikiSidebarContent $wikiLines
    if ($wikiNew -ne $wikiSidebarContent) {
      Set-Content -Path $wikiSidebarPath -Value $wikiNew -NoNewline
    }
  }

  Write-Host "Sidebars aktualisiert." -ForegroundColor Green

} catch {
  Write-Error $_
  exit 1
}
