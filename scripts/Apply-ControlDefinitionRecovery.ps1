[CmdletBinding()]
param([string]$EMSPath="C:\temp\standars\ems")
$ErrorActionPreference="Stop"
$py=Join-Path $EMSPath ".venv\Scripts\python.exe"
if(-not(Test-Path $py)){$py="python"}

$catalog=Join-Path $EMSPath "registry\control_catalog.yaml"
$recovered=Join-Path $EMSPath "generated\wave2\control-definition-recovery\recovered_control_definitions.csv"
$report=Join-Path $EMSPath "generated\wave2\control-definition-recovery\apply_report.json"
if(-not(Test-Path $recovered)){throw "Run recovery first."}

& $py (Join-Path $EMSPath "scripts\Apply-RecoveredControlDefinitions.py") `
 --catalog $catalog `
 --recovered $recovered `
 --report $report
if($LASTEXITCODE-ne 0){throw "Applying recovered definitions failed."}

Write-Host ""
Write-Host "Recovered high-confidence definitions applied." -ForegroundColor Green
Write-Host "Next:"
Write-Host "  .\scripts\Run-ScopeExceptionResolver.ps1"
Write-Host "  .\scripts\Show-ScopeExceptionResolution.ps1"
