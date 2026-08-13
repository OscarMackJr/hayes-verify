[CmdletBinding()]
param([string]$EMSPath="C:\temp\standars\ems")

$ErrorActionPreference="Stop"
$py=Join-Path $EMSPath ".venv\Scripts\python.exe"
if(-not(Test-Path $py)){$py="python"}

$scope=Join-Path $EMSPath "registry\control_scope_registry.yaml"
$catalog=Join-Path $EMSPath "registry\control_catalog.yaml"
$out=Join-Path $EMSPath "generated\wave2\higher-scope-evidence"
New-Item -ItemType Directory -Path $out -Force | Out-Null

Write-Host "Discovering higher-scope evidence candidates..." -ForegroundColor Cyan
& $py (Join-Path $EMSPath "scripts\Discover-HigherScopeEvidence.py") `
  --ems-root $EMSPath `
  --scope-registry $scope `
  --catalog $catalog `
  --outdir $out
if($LASTEXITCODE-ne 0){throw "Higher-scope evidence discovery failed."}

Write-Host ""
Write-Host "Validating discovered candidates..." -ForegroundColor Cyan
& $py (Join-Path $EMSPath "scripts\Validate-HigherScopeEvidenceCandidates.py") `
  --candidates (Join-Path $out "evidence_candidates.csv") `
  --proposed-dir (Join-Path $out "proposed_evidence_records") `
  --report (Join-Path $out "candidate_validation.json") `
  --min-confidence 0.90
if($LASTEXITCODE-ne 0){throw "Candidate validation failed."}

Write-Host ""
Write-Host "Discovery complete. Nothing authoritative has been changed." -ForegroundColor Green
Write-Host "Review:"
Write-Host "  generated\wave2\higher-scope-evidence\evidence_discovery_summary.json"
Write-Host "  generated\wave2\higher-scope-evidence\evidence_candidates.csv"
Write-Host "  generated\wave2\higher-scope-evidence\evidence_gaps.csv"
