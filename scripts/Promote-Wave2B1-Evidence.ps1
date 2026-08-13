[CmdletBinding()]
param(
    [string]$EMSPath="C:\temp\standars\ems",
    [switch]$SkipInheritanceRerun
)

$ErrorActionPreference="Stop"
$py=Join-Path $EMSPath ".venv\Scripts\python.exe"
if(-not(Test-Path $py)){$py="python"}

$out=Join-Path $EMSPath "generated\wave2\higher-scope-evidence"

& $py (Join-Path $EMSPath "scripts\Promote-HigherScopeEvidence.py") `
  --candidates (Join-Path $out "evidence_candidates.csv") `
  --proposed-dir (Join-Path $out "proposed_evidence_records") `
  --evidence-root (Join-Path $EMSPath "evidence") `
  --report (Join-Path $out "promotion_report.json") `
  --min-confidence 0.90

if($LASTEXITCODE-ne 0){throw "Higher-scope evidence promotion failed."}

if(-not $SkipInheritanceRerun){
    Write-Host ""
    Write-Host "Re-running Wave 2B.1 inheritance..." -ForegroundColor Cyan
    & (Join-Path $EMSPath "scripts\Run-Wave2B1-Inheritance.ps1") -EMSPath $EMSPath
    if($LASTEXITCODE-ne 0){throw "Post-promotion inheritance rerun failed."}
}

Write-Host ""
Write-Host "Higher-scope evidence promotion complete." -ForegroundColor Green
