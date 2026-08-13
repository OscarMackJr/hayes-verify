[CmdletBinding()]
param(
    [string]$EMSPath="C:\temp\standars\ems"
)

$ErrorActionPreference="Stop"

$py=Join-Path $EMSPath ".venv\Scripts\python.exe"
if(-not(Test-Path $py)){$py="python"}

$dir=Join-Path $EMSPath "generated\wave2\scope-adjudication"
$resolved=Join-Path $dir "scope_registry_adjudication_queue.resolved.csv"
$authoritative=Join-Path $dir "scope_registry_adjudication_queue.authoritative.csv"
$report=Join-Path $dir "authoritative_scope_override_report.json"
$overrides=Join-Path $EMSPath "registry\authoritative_scope_overrides.json"

if(-not(Test-Path $resolved)){
    throw "Resolved adjudication queue not found: $resolved"
}

Write-Host "Applying nine authoritative scope overrides..." -ForegroundColor Cyan

& $py (Join-Path $EMSPath "scripts\Apply-AuthoritativeScopeOverrides.py") `
    --queue $resolved `
    --overrides $overrides `
    --out $authoritative `
    --report $report

if($LASTEXITCODE-ne 0){
    throw "Authoritative scope override application failed."
}

Write-Host ""
Write-Host "Validating authoritative 80-control queue..." -ForegroundColor Cyan

# Temporarily validate the authoritative queue using the existing validator.
$validation=Join-Path $dir "authoritative_scope_validation.json"

& $py (Join-Path $EMSPath "scripts\Validate-ScopeRegistryAdjudication.py") `
    --queue $authoritative `
    --report $validation `
    --require-complete

if($LASTEXITCODE-ne 0){
    throw "Authoritative scope queue validation failed."
}

Write-Host ""
Write-Host "Promoting authoritative queue..." -ForegroundColor Cyan

$canonical=Join-Path $dir "scope_registry_adjudication_queue.csv"
if(Test-Path $canonical){
    Copy-Item $canonical "$canonical.pre-authoritative-overrides.bak" -Force
}
Copy-Item $authoritative $canonical -Force

Write-Host ""
Write-Host "Applying approved scope registry adjudication..." -ForegroundColor Cyan

& (Join-Path $EMSPath "scripts\Apply-ScopeRegistryAdjudication.ps1") -EMSPath $EMSPath

if($LASTEXITCODE-ne 0){
    throw "Applying scope registry adjudication failed."
}

Write-Host ""
Write-Host "Wave 2A.1 authoritative scope override sequence complete." -ForegroundColor Green
Write-Host ""
Write-Host "Review updated impact:"
Write-Host "  generated\wave2\scope_summary.json"
Write-Host "  generated\wave2\scope_impact_analysis.csv"
