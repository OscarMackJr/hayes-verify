[CmdletBinding()]
param(
    [string]$EMSPath="C:\temp\standars\ems",
    [switch]$Promote
)

$ErrorActionPreference="Stop"
$py=Join-Path $EMSPath ".venv\Scripts\python.exe"
if(-not(Test-Path $py)){$py="python"}

$out=Join-Path $EMSPath "generated\wave2\higher-scope-collectors\ai-governance-gap-remediation"
New-Item -ItemType Directory -Path $out -Force|Out-Null

Write-Host "Running targeted AI-governance gap evidence collection..." -ForegroundColor Cyan
& $py (Join-Path $EMSPath "scripts\collectors\higher-scope\Collect-AIGovernanceGapEvidence.py") `
  --ems-root $EMSPath `
  --outdir $out
if($LASTEXITCODE-ne 0){throw "Targeted AI-governance gap collection failed."}

Write-Host ""
Write-Host "Building remediation queue for unresolved gaps..." -ForegroundColor Cyan
& $py (Join-Path $EMSPath "scripts\Build-AIGovernanceGapRemediationQueue.py") `
  --resolution (Join-Path $out "gap_resolution.csv") `
  --out (Join-Path $out "remediation_queue.csv")
if($LASTEXITCODE-ne 0){throw "AI-governance remediation queue generation failed."}

if($Promote){
    Write-Host ""
    Write-Host "Promoting only resolved AI-governance gaps..." -ForegroundColor Cyan
    & $py (Join-Path $EMSPath "scripts\Promote-AIGovernanceGapEvidence.py") `
      --resolution (Join-Path $out "gap_resolution.csv") `
      --evidence-root (Join-Path $EMSPath "evidence") `
      --report (Join-Path $out "promotion_report.json")
    if($LASTEXITCODE-ne 0){throw "AI-governance gap promotion failed."}

    & (Join-Path $EMSPath "scripts\Run-Wave2B1-Inheritance.ps1") -EMSPath $EMSPath
    if($LASTEXITCODE-ne 0){throw "Inheritance rerun failed."}
}
else{
    Write-Host ""
    Write-Host "No evidence promoted. Review targeted gap resolution first." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Wave 2B.2.5b complete." -ForegroundColor Green
