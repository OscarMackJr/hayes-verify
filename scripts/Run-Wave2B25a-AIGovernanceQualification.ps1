[CmdletBinding()]
param(
    [string]$EMSPath="C:\temp\standars\ems",
    [switch]$Promote
)

$ErrorActionPreference="Stop"
$py=Join-Path $EMSPath ".venv\Scripts\python.exe"
if(-not(Test-Path $py)){$py="python"}

$src=Join-Path $EMSPath "generated\wave2\higher-scope-collectors\ai-governance\evidence_envelopes.jsonl"
if(-not(Test-Path $src)){
    throw "Wave 2B.2.5 evidence envelopes not found. Run Run-Wave2B25-HSAIGovernance.ps1 first."
}

$out=Join-Path $EMSPath "generated\wave2\higher-scope-collectors\ai-governance-qualified-v2"
New-Item -ItemType Directory -Path $out -Force|Out-Null

Write-Host "Classifying AI-governance evidence sources..." -ForegroundColor Cyan
& $py (Join-Path $EMSPath "scripts\Classify-AIGovernanceEvidence.py") `
  --envelopes $src `
  --out (Join-Path $out "evidence_source_classification.csv")
if($LASTEXITCODE-ne 0){throw "Evidence source classification failed."}

Write-Host ""
Write-Host "Building assertion/evidence matrix..." -ForegroundColor Cyan
& $py (Join-Path $EMSPath "scripts\Build-AIGovernanceAssertionEvidenceMatrix.py") `
  --classification (Join-Path $out "evidence_source_classification.csv") `
  --out (Join-Path $out "assertion_evidence_matrix.csv")
if($LASTEXITCODE-ne 0){throw "Assertion evidence matrix failed."}

Write-Host ""
Write-Host "Writing rejected sources..." -ForegroundColor Cyan
& $py (Join-Path $EMSPath "scripts\Write-AIGovernanceRejectedSources.py") `
  --classification (Join-Path $out "evidence_source_classification.csv") `
  --out (Join-Path $out "rejected_sources.csv")
if($LASTEXITCODE-ne 0){throw "Rejected-source report failed."}

Write-Host ""
Write-Host "Qualifying AI-governance operating evidence..." -ForegroundColor Cyan
& $py (Join-Path $EMSPath "scripts\Qualify-AIGovernanceOperatingEvidence.py") `
  --matrix (Join-Path $out "assertion_evidence_matrix.csv") `
  --outdir $out
if($LASTEXITCODE-ne 0){throw "AI-governance operating-evidence qualification failed."}

if($Promote){
    Write-Host ""
    Write-Host "Promoting only operating-evidence-qualified AI controls..." -ForegroundColor Cyan
    & $py (Join-Path $EMSPath "scripts\Promote-AIGovernanceOperatingEvidence.py") `
      --qualified (Join-Path $out "qualified_ai_governance.csv") `
      --matrix (Join-Path $out "assertion_evidence_matrix.csv") `
      --evidence-root (Join-Path $EMSPath "evidence") `
      --report (Join-Path $out "promotion_report.json")
    if($LASTEXITCODE-ne 0){throw "AI-governance promotion failed."}

    & (Join-Path $EMSPath "scripts\Run-Wave2B1-Inheritance.ps1") -EMSPath $EMSPath
    if($LASTEXITCODE-ne 0){throw "Inheritance rerun failed."}
}
else{
    Write-Host ""
    Write-Host "No evidence promoted. Review operating-evidence qualification first." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Wave 2B.2.5a complete." -ForegroundColor Green
