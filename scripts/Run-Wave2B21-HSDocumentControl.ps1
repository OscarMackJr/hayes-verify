[CmdletBinding()]
param(
    [string]$EMSPath="C:\temp\standars\ems",
    [switch]$Promote
)

$ErrorActionPreference="Stop"
$py=Join-Path $EMSPath ".venv\Scripts\python.exe"
if(-not(Test-Path $py)){$py="python"}

$collectorDir=Join-Path $EMSPath "generated\wave2\higher-scope-collectors\document-control"
$qualDir=Join-Path $EMSPath "generated\wave2\higher-scope-collectors\document-control-qualified"
New-Item -ItemType Directory -Path $collectorDir -Force | Out-Null
New-Item -ItemType Directory -Path $qualDir -Force | Out-Null

Write-Host "Running HS-DOCUMENT-CONTROL..." -ForegroundColor Cyan
& $py (Join-Path $EMSPath "scripts\collectors\higher-scope\Collect-HSDocumentControl.py") `
  --ems-root $EMSPath `
  --spec (Join-Path $EMSPath "registry\hs_document_control_spec.json") `
  --outdir $collectorDir
if($LASTEXITCODE-ne 0){throw "HS-DOCUMENT-CONTROL collection failed."}

Write-Host ""
Write-Host "Validating evidence envelopes..." -ForegroundColor Cyan
& $py (Join-Path $EMSPath "scripts\Validate-HSDocumentControlEvidence.py") `
  --envelopes (Join-Path $collectorDir "evidence_envelopes.jsonl") `
  --report (Join-Path $collectorDir "envelope_validation.json")
if($LASTEXITCODE-ne 0){throw "Document-control evidence validation failed."}

Write-Host ""
Write-Host "Qualifying collector evidence..." -ForegroundColor Cyan
& $py (Join-Path $EMSPath "scripts\Qualify-HSDocumentControlEvidence.py") `
  --envelopes (Join-Path $collectorDir "evidence_envelopes.jsonl") `
  --outdir $qualDir
if($LASTEXITCODE-ne 0){throw "Document-control qualification failed."}

if($Promote){
    Write-Host ""
    Write-Host "Promoting only eligible document-control evidence..." -ForegroundColor Cyan
    & $py (Join-Path $EMSPath "scripts\Promote-HSDocumentControlEvidence.py") `
      --qualified (Join-Path $qualDir "qualified_document_control.csv") `
      --envelopes (Join-Path $collectorDir "evidence_envelopes.jsonl") `
      --evidence-root (Join-Path $EMSPath "evidence") `
      --report (Join-Path $qualDir "promotion_report.json")
    if($LASTEXITCODE-ne 0){throw "Document-control evidence promotion failed."}

    Write-Host ""
    Write-Host "Re-running Wave 2B.1 inheritance..." -ForegroundColor Cyan
    & (Join-Path $EMSPath "scripts\Run-Wave2B1-Inheritance.ps1") -EMSPath $EMSPath
    if($LASTEXITCODE-ne 0){throw "Post-promotion inheritance rerun failed."}
}
else {
    Write-Host ""
    Write-Host "No evidence promoted. Review qualification before using -Promote." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Wave 2B.2.1 HS-DOCUMENT-CONTROL run complete." -ForegroundColor Green
