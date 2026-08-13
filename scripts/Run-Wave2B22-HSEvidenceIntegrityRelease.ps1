[CmdletBinding()]param([string]$EMSPath="C:\temp\standars\ems",[switch]$Promote)
$ErrorActionPreference="Stop"
$py=Join-Path $EMSPath ".venv\Scripts\python.exe";if(-not(Test-Path $py)){$py="python"}
$c=Join-Path $EMSPath "generated\wave2\higher-scope-collectors\evidence-integrity-release"
$q=Join-Path $EMSPath "generated\wave2\higher-scope-collectors\evidence-integrity-release-qualified"
New-Item -ItemType Directory -Path $c -Force|Out-Null;New-Item -ItemType Directory -Path $q -Force|Out-Null
& $py (Join-Path $EMSPath "scripts\collectors\higher-scope\Collect-HSEvidenceIntegrityRelease.py") --ems-root $EMSPath --spec (Join-Path $EMSPath "registry\hs_evidence_integrity_release_spec.json") --outdir $c
if($LASTEXITCODE-ne 0){throw "Collector failed."}
& $py (Join-Path $EMSPath "scripts\Validate-HSEvidenceIntegrityRelease.py") --envelopes (Join-Path $c "evidence_envelopes.jsonl") --report (Join-Path $c "envelope_validation.json")
if($LASTEXITCODE-ne 0){throw "Envelope validation failed."}
& $py (Join-Path $EMSPath "scripts\Qualify-HSEvidenceIntegrityRelease.py") --envelopes (Join-Path $c "evidence_envelopes.jsonl") --outdir $q
if($LASTEXITCODE-ne 0){throw "Qualification failed."}
if($Promote){
  & $py (Join-Path $EMSPath "scripts\Promote-HSEvidenceIntegrityRelease.py") --qualified (Join-Path $q "qualified_evidence_integrity_release.csv") --envelopes (Join-Path $c "evidence_envelopes.jsonl") --evidence-root (Join-Path $EMSPath "evidence") --report (Join-Path $q "promotion_report.json")
  if($LASTEXITCODE-ne 0){throw "Promotion failed."}
  & (Join-Path $EMSPath "scripts\Run-Wave2B1-Inheritance.ps1") -EMSPath $EMSPath
  if($LASTEXITCODE-ne 0){throw "Inheritance rerun failed."}
}else{Write-Host "No evidence promoted. Review qualification before using -Promote." -ForegroundColor Yellow}
Write-Host "Wave 2B.2.2 complete." -ForegroundColor Green
