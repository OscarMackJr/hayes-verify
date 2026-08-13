[CmdletBinding()]
param(
    [string]$EMSPath="C:\temp\standars\ems",
    [switch]$AllowReviewRequired
)
$ErrorActionPreference="Stop"
function Fail([string]$m){throw "WAVE 2D APPLICABILITY BLOCKED: $m"}

$root=(Resolve-Path $EMSPath).Path
$spec=Join-Path $root "registry\wave2d_applicability_adjudication_spec.json"
if((git -C $root branch --show-current).Trim() -ne "feature/wave2d-scope-population"){Fail "Wrong branch"}

$py=if($env:VIRTUAL_ENV -and (Test-Path "$env:VIRTUAL_ENV\Scripts\python.exe")){"$env:VIRTUAL_ENV\Scripts\python.exe"}else{(Get-Command python).Source}

Write-Host "=== Build applicability rules from repository classifications ===" -ForegroundColor Cyan
& $py "$root\scripts\Build-Wave2DApplicabilityRules.py" --root $root --spec $spec
if($LASTEXITCODE){Fail "Applicability-rule build failed"}

Write-Host "`n=== Adjudicate 560 control-target pairs ===" -ForegroundColor Cyan
& $py "$root\scripts\Adjudicate-Wave2DApplicability.py" --root $root --spec $spec
if($LASTEXITCODE){Fail "Applicability adjudication failed"}

Write-Host "`n=== Apply decisions to matrix without evaluating controls ===" -ForegroundColor Cyan
& $py "$root\scripts\Apply-Wave2DApplicability.py" --root $root --spec $spec
if($LASTEXITCODE){Fail "Applying applicability decisions failed"}

Write-Host "`n=== Validate matrix adjudication ===" -ForegroundColor Cyan
& $py "$root\scripts\Validate-Wave2DApplicability.py" --root $root --spec $spec
if($LASTEXITCODE){Fail "Applicability validation failed"}

$summary=Get-Content "$root\generated\wave2d\evaluation-matrix\applicability_adjudication_summary.json" -Raw|ConvertFrom-Json
if([int]$summary.review_required_count -gt 0 -and -not $AllowReviewRequired){
    Fail "$($summary.review_required_count) REVIEW_REQUIRED matrix row(s) remain."
}

if([int]$summary.review_required_count -gt 0){
    Write-Host "WARNING: applicability has unresolved REVIEW_REQUIRED rows. No evaluation/promotion performed." -ForegroundColor Yellow
}else{
    Write-Host "PASS: Wave 2D applicability fully adjudicated." -ForegroundColor Green
}
