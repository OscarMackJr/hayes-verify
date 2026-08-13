[CmdletBinding()]
param([string]$EMSPath="C:\temp\standars\ems",[switch]$Promote)

$ErrorActionPreference="Stop"
$py=Join-Path $EMSPath ".venv\Scripts\python.exe"
if(-not(Test-Path $py)){$py="python"}

$out=Join-Path $EMSPath "generated\wave2\higher-scope-collectors\security-data-governance"
New-Item -ItemType Directory -Path $out -Force|Out-Null

Write-Host "Collecting Security & Data Governance evidence candidates..." -ForegroundColor Cyan
& $py (Join-Path $EMSPath "scripts\collectors\higher-scope\Collect-HSSecurityDataGovernance.py") --ems-root $EMSPath --outdir $out
if($LASTEXITCODE-ne 0){throw "Collector failed."}

Write-Host ""
Write-Host "Classifying evidence admissibility..." -ForegroundColor Cyan
& $py (Join-Path $EMSPath "scripts\Classify-HSSecurityDataGovernanceEvidence.py") --envelopes (Join-Path $out "evidence_envelopes.jsonl") --out (Join-Path $out "evidence_source_classification.csv")
if($LASTEXITCODE-ne 0){throw "Evidence classification failed."}

Write-Host ""
Write-Host "Building assertion/evidence matrix..." -ForegroundColor Cyan
& $py (Join-Path $EMSPath "scripts\Build-HSSecurityDataGovernanceMatrix.py") --classification (Join-Path $out "evidence_source_classification.csv") --out (Join-Path $out "assertion_evidence_matrix.csv")
if($LASTEXITCODE-ne 0){throw "Matrix build failed."}

Write-Host ""
Write-Host "Qualifying operating evidence..." -ForegroundColor Cyan
& $py (Join-Path $EMSPath "scripts\Qualify-HSSecurityDataGovernance.py") --matrix (Join-Path $out "assertion_evidence_matrix.csv") --outdir $out
if($LASTEXITCODE-ne 0){throw "Qualification failed."}

Write-Host ""
Write-Host "Building remediation queue..." -ForegroundColor Cyan
& $py (Join-Path $EMSPath "scripts\Build-HSSecurityDataGovernanceRemediation.py") --gaps (Join-Path $out "security_data_governance_gaps.csv") --out (Join-Path $out "remediation_queue.csv")
if($LASTEXITCODE-ne 0){throw "Remediation queue failed."}

if($Promote){
    Write-Host ""
    Write-Host "Promoting qualified Security & Data Governance evidence..." -ForegroundColor Cyan
    & $py (Join-Path $EMSPath "scripts\Promote-HSSecurityDataGovernance.py") --qualified (Join-Path $out "qualified_security_data_governance.csv") --matrix (Join-Path $out "assertion_evidence_matrix.csv") --evidence-root (Join-Path $EMSPath "evidence") --report (Join-Path $out "promotion_report.json")
    if($LASTEXITCODE-ne 0){throw "Promotion failed."}

    & (Join-Path $EMSPath "scripts\Run-Wave2B1-Inheritance.ps1") -EMSPath $EMSPath
    if($LASTEXITCODE-ne 0){throw "Inheritance rerun failed."}
}
else{
    Write-Host ""
    Write-Host "No evidence promoted. Review qualification and remediation first." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Wave 2B.2.6 complete." -ForegroundColor Green
