[CmdletBinding()]
param([string]$EMSPath="C:\temp\standars\ems")

$ErrorActionPreference="Stop"
$py=Join-Path $EMSPath ".venv\Scripts\python.exe"
if(-not(Test-Path $py)){$py="python"}

$src=Join-Path $EMSPath "generated\wave2\higher-scope-evidence\evidence_candidates.csv"
if(-not(Test-Path $src)){
    throw "Evidence candidates not found. Run Run-Wave2B1-EvidenceDiscovery.ps1 first."
}

$out=Join-Path $EMSPath "generated\wave2\higher-scope-evidence-qualified"
New-Item -ItemType Directory -Path $out -Force | Out-Null

$policy=Join-Path $EMSPath "registry\evidence_source_policy.json"
$classed=Join-Path $out "classified_evidence_candidates.csv"
$qualified=Join-Path $out "qualified_evidence_candidates.csv"

Write-Host "Classifying evidence sources..." -ForegroundColor Cyan
& $py (Join-Path $EMSPath "scripts\Classify-EvidenceSources.py") `
    --candidates $src `
    --policy $policy `
    --out $classed
if($LASTEXITCODE-ne 0){throw "Evidence source classification failed."}

Write-Host ""
Write-Host "Evaluating evidence sufficiency..." -ForegroundColor Cyan
& $py (Join-Path $EMSPath "scripts\Evaluate-EvidenceSufficiency.py") `
    --classified $classed `
    --out $qualified
if($LASTEXITCODE-ne 0){throw "Evidence sufficiency evaluation failed."}

Write-Host ""
Write-Host "Rebuilding best candidate set..." -ForegroundColor Cyan
& $py (Join-Path $EMSPath "scripts\Rebuild-HigherScopeCandidates.py") `
    --qualified $qualified `
    --scope-registry (Join-Path $EMSPath "registry\control_scope_registry.yaml") `
    --outdir $out
if($LASTEXITCODE-ne 0){throw "Qualified candidate rebuild failed."}

Write-Host ""
Write-Host "Validating promotion eligibility..." -ForegroundColor Cyan
& $py (Join-Path $EMSPath "scripts\Validate-EvidencePromotion.py") `
    --qualified-best (Join-Path $out "qualified_best_candidates.csv") `
    --report (Join-Path $out "promotion_validation.json")
if($LASTEXITCODE-ne 0){throw "Evidence promotion validation failed."}

Write-Host ""
Write-Host "Wave 2B.1 evidence qualification complete." -ForegroundColor Green
Write-Host "No evidence has been promoted."
Write-Host "Review:"
Write-Host "  generated\wave2\higher-scope-evidence-qualified\evidence_qualification_summary.json"
Write-Host "  generated\wave2\higher-scope-evidence-qualified\qualified_best_candidates.csv"
Write-Host "  generated\wave2\higher-scope-evidence-qualified\qualified_evidence_gaps.csv"
