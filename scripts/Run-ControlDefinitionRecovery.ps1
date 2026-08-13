[CmdletBinding()]
param(
    [string]$EMSPath="C:\temp\standars\ems",
    [string]$SearchRoot="C:\temp\standars"
)
$ErrorActionPreference="Stop"
$py=Join-Path $EMSPath ".venv\Scripts\python.exe"
if(-not(Test-Path $py)){$py="python"}

$catalog=Join-Path $EMSPath "registry\control_catalog.yaml"
if(-not(Test-Path $catalog)){throw "Control catalog not found: $catalog"}

$out=Join-Path $EMSPath "generated\wave2\control-definition-recovery"
& $py (Join-Path $EMSPath "scripts\Recover-ControlDefinitions.py") `
  --search-root $SearchRoot `
  --catalog $catalog `
  --outdir $out `
  --min-confidence 0.90

if($LASTEXITCODE-ne 0){throw "Control definition recovery failed."}

Write-Host ""
Write-Host "Control definition recovery complete." -ForegroundColor Green
Write-Host "Review:"
Write-Host "  $out\recovered_control_definitions.csv"
Write-Host "  $out\unresolved_control_definitions.csv"
Write-Host "  $out\recovery_summary.json"
