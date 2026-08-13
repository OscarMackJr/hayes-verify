[CmdletBinding()]param([string]$EMSPath="C:\temp\standars\ems",[switch]$Promote)
$ErrorActionPreference="Stop"
$py=Join-Path $EMSPath ".venv\Scripts\python.exe";if(-not(Test-Path $py)){$py="python"}
$c=Join-Path $EMSPath "generated\wave2\higher-scope-collectors\management-review"
$q=Join-Path $EMSPath "generated\wave2\higher-scope-collectors\management-review-qualified"
New-Item -ItemType Directory -Path $c -Force|Out-Null;New-Item -ItemType Directory -Path $q -Force|Out-Null

& $py (Join-Path $EMSPath "scripts\collectors\higher-scope\Collect-HSManagementReview.py") --ems-root $EMSPath --outdir $c
if($LASTEXITCODE-ne 0){throw "Management-review collector failed."}

& $py (Join-Path $EMSPath "scripts\Validate-HSManagementReview.py") --envelopes (Join-Path $c "evidence_envelopes.jsonl") --report (Join-Path $c "envelope_validation.json")
if($LASTEXITCODE-ne 0){throw "Management-review envelope validation failed."}

& $py (Join-Path $EMSPath "scripts\Qualify-HSManagementReview.py") --envelopes (Join-Path $c "evidence_envelopes.jsonl") --outdir $q
if($LASTEXITCODE-ne 0){throw "Management-review qualification failed."}

if($Promote){
    & $py (Join-Path $EMSPath "scripts\Promote-HSManagementReview.py") --qualified (Join-Path $q "qualified_management_review.csv") --envelopes (Join-Path $c "evidence_envelopes.jsonl") --evidence-root (Join-Path $EMSPath "evidence") --report (Join-Path $q "promotion_report.json")
    if($LASTEXITCODE-ne 0){throw "Management-review promotion failed."}

    & (Join-Path $EMSPath "scripts\Run-Wave2B1-Inheritance.ps1") -EMSPath $EMSPath
    if($LASTEXITCODE-ne 0){throw "Inheritance rerun failed."}
}else{
    Write-Host "No evidence promoted. Review management-review qualification first." -ForegroundColor Yellow
}
Write-Host "Wave 2B.2.4 complete." -ForegroundColor Green
