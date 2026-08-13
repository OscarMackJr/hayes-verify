[CmdletBinding()]
param(
    [string]$EMSPath="C:\temp\standars\ems",
    [string]$BaselinePath="C:\temp\standars\ems-local-archive\wave1-input\effective_compliance_postpolicy.csv"
)

$ErrorActionPreference="Stop"

$runner=Join-Path $EMSPath "scripts\Run-Wave2B1-Inheritance.ps1"
if(-not(Test-Path $runner)){throw "Inheritance runner not found: $runner"}
if(-not(Test-Path $BaselinePath)){
    throw "Wave 1 baseline not found at expected archive path: $BaselinePath"
}

Write-Host "=== Rerun inheritance after Wave 2C.2b promotion ===" -ForegroundColor Cyan
Write-Host "Baseline: $BaselinePath"

& $runner -BaselinePath $BaselinePath
if($LASTEXITCODE-ne 0){
    throw "Inheritance rerun failed."
}

$impact=Join-Path $EMSPath "generated\wave2\inheritance\inheritance_impact_report.json"
$higher=Join-Path $EMSPath "generated\wave2\inheritance\higher_scope_results.json"

if(-not(Test-Path $impact)){throw "Inheritance impact report missing after rerun."}
if(-not(Test-Path $higher)){throw "Higher-scope results missing after rerun."}

Write-Host ""
Write-Host "PASS: inheritance rerun completed after Wave 2C.2b promotion." -ForegroundColor Green
