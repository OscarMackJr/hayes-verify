[CmdletBinding()]
param(
    [string]$EMSPath="C:\temp\standars\ems"
)

$ErrorActionPreference="Stop"

$py=Join-Path $EMSPath ".venv\Scripts\python.exe"
if(-not(Test-Path $py)){$py="python"}

$scope=Join-Path $EMSPath "registry\control_scope_registry.yaml"
$auth=Join-Path $EMSPath "registry\evidence_authority_registry.yaml"
$evidence=Join-Path $EMSPath "evidence"
$outdir=Join-Path $EMSPath "generated\wave2\inheritance"
New-Item -ItemType Directory -Path $outdir -Force | Out-Null

# Prefer final Wave 1 post-policy compliance.
$candidates=@(
    (Join-Path $EMSPath "releases\Pass4_5_Wave1_Baseline\generated\policy-review\effective_compliance_postpolicy.csv"),
    (Join-Path $EMSPath "generated\policy-review\effective_compliance_postpolicy.csv"),
    (Join-Path $EMSPath "generated\collector-acceptance\effective_compliance.csv")
)
$baseline=$candidates|Where-Object{Test-Path $_}|Select-Object -First 1
if(-not $baseline){throw "Wave 1 compliance baseline not found."}

Write-Host "Seeding higher-scope evidence records..." -ForegroundColor Cyan
& $py (Join-Path $EMSPath "scripts\Seed-HigherScopeEvidence.py") `
    --scope-registry $scope `
    --authority-registry $auth `
    --out-root $evidence
if($LASTEXITCODE-ne 0){throw "Evidence seeding failed."}

Write-Host ""
Write-Host "Evaluating EMS + ORGANIZATION controls..." -ForegroundColor Cyan
$higher=Join-Path $outdir "higher_scope_results.json"
& $py (Join-Path $EMSPath "scripts\Evaluate-HigherScopeControls.py") `
    --scope-registry $scope `
    --evidence-root $evidence `
    --out $higher
if($LASTEXITCODE-ne 0){throw "Higher-scope evaluation failed."}

Write-Host ""
Write-Host "Resolving inherited repository compliance..." -ForegroundColor Cyan
$effective=Join-Path $outdir "effective_compliance_with_inheritance.csv"
$report=Join-Path $outdir "inheritance_impact_report.json"
& $py (Join-Path $EMSPath "scripts\Resolve-InheritedCompliance.py") `
    --compliance $baseline `
    --scope-registry $scope `
    --higher-scope-results $higher `
    --out $effective `
    --report $report
if($LASTEXITCODE-ne 0){throw "Inheritance resolution failed."}

Write-Host ""
Write-Host "Validating inheritance..." -ForegroundColor Cyan
$validation=Join-Path $outdir "inheritance_validation.json"
& $py (Join-Path $EMSPath "scripts\Validate-Inheritance.py") `
    --compliance $effective `
    --report $validation
if($LASTEXITCODE-ne 0){throw "Inheritance validation failed."}

Write-Host ""
Write-Host "Wave 2B.1 inheritance run complete." -ForegroundColor Green
Write-Host "Review:"
Write-Host "  generated\wave2\inheritance\higher_scope_results.json"
Write-Host "  generated\wave2\inheritance\inheritance_impact_report.json"
Write-Host "  generated\wave2\inheritance\effective_compliance_with_inheritance.csv"
