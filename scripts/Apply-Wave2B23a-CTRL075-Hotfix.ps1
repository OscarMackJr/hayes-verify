[CmdletBinding()]
param(
    [string]$EMSPath = (Get-Location).Path
)

$ErrorActionPreference = "Stop"
$collector = Join-Path $EMSPath "scripts\collectors\higher-scope\Collect-HSContinuousCompliance.py"

if (-not (Test-Path $collector)) {
    throw "Collector not found: $collector"
}

$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$backup = "$collector.pre-2B23a-hotfix-$stamp.bak"
Copy-Item $collector $backup -Force

$text = Get-Content $collector -Raw

# The failing collector calls status(A), but a local/global assignment named
# 'status' shadows the function. Rename assignments/references conservatively.
if ($text -notmatch 'def\s+status\s*\(') {
    throw "Expected status(...) function was not found. Refusing blind patch."
}

# Find simple Python assignments to status, excluding comparisons and function definition.
$matches = [regex]::Matches($text, '(?m)^(\s*)status\s*=(?!=)(.+)$')
if ($matches.Count -eq 0) {
    # It may already be patched.
    if ($text -match '\bcollector_status\b' -and $text -match '\bstatus\s*\(\s*A\s*\)') {
        Write-Host "Collector appears already patched; no assignment named status remains."
        exit 0
    }
    throw "No shadowing 'status =' assignment found. Refusing to modify collector."
}

# Rename assignment target(s).
$text = [regex]::Replace(
    $text,
    '(?m)^(\s*)status\s*=(?!=)(.+)$',
    '${1}collector_status =${2}'
)

# Rename common references to the assigned variable while preserving status(...).
# Handles dict entries, comparisons, f-strings/expressions, and return/use sites.
$text = [regex]::Replace($text, '\bstatus\b(?!\s*\()', 'collector_status')

# Restore the actual function definition if the broad replacement touched its name.
$text = [regex]::Replace($text, '(?m)^(\s*)def\s+collector_status\s*\(', '${1}def status(')

Set-Content -Path $collector -Value $text -Encoding UTF8

# Compile validation catches syntax errors before rerun.
& python -m py_compile $collector
if ($LASTEXITCODE -ne 0) {
    Copy-Item $backup $collector -Force
    throw "Python compile validation failed; original collector restored from $backup"
}

# Verify status(A) remains callable and no assignment named status remains.
$verify = Get-Content $collector -Raw
$remainingAssignments = [regex]::Matches($verify, '(?m)^\s*status\s*=(?!=)')
if ($remainingAssignments.Count -gt 0) {
    Copy-Item $backup $collector -Force
    throw "Shadowing assignment still present; original collector restored."
}
if ($verify -notmatch '\bstatus\s*\(\s*A\s*\)') {
    Copy-Item $backup $collector -Force
    throw "Expected status(A) call missing after patch; original collector restored."
}

Write-Host "PASS: CTRL-075 collector status() shadowing hotfix applied."
Write-Host "Backup: $backup"
Write-Host "Collector: $collector"
