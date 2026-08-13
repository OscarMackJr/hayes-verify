[CmdletBinding()]
param(
    [string]$EMSPath="C:\temp\standars\ems",
    [switch]$BuildQueueOnly
)
$ErrorActionPreference="Stop"
function Fail([string]$m){throw "WAVE 2D HUMAN ADJUDICATION BLOCKED: $m"}

$root=(Resolve-Path $EMSPath).Path
$spec=Join-Path $root "registry\wave2d_applicability_human_review_spec.json"
if((git -C $root branch --show-current).Trim() -ne "feature/wave2d-scope-population"){Fail "Wrong branch"}

$py=if($env:VIRTUAL_ENV -and (Test-Path "$env:VIRTUAL_ENV\Scripts\python.exe")){"$env:VIRTUAL_ENV\Scripts\python.exe"}else{(Get-Command python).Source}

Write-Host "=== Build focused REVIEW_REQUIRED queue ===" -ForegroundColor Cyan
& $py "$root\scripts\Build-Wave2DApplicabilityReviewQueue.py" --root $root --spec $spec
if($LASTEXITCODE){Fail "Review queue build failed"}

if($BuildQueueOnly){
    Write-Host "PASS: review queue created. Complete the human decision file before applying." -ForegroundColor Green
    exit 0
}

$reviewFile="$root\registry\wave2d\applicability_review_decisions.csv"
if(-not(Test-Path $reviewFile)){
    Copy-Item "$root\registry\wave2d\applicability_review_template.csv" $reviewFile
    Fail "Human review file initialized at registry\wave2d\applicability_review_decisions.csv. Fill all 60 rows, then rerun."
}

Write-Host "`n=== Validate human review decisions ===" -ForegroundColor Cyan
& $py "$root\scripts\Validate-Wave2DHumanApplicabilityDecisions.py" --root $root --spec $spec
if($LASTEXITCODE){Fail "Human decision validation failed"}

Write-Host "`n=== Apply human decisions as preserved HUMAN_* overrides ===" -ForegroundColor Cyan
& $py "$root\scripts\Apply-Wave2DHumanApplicabilityDecisions.py" --root $root --spec $spec
if($LASTEXITCODE){Fail "Applying human decisions failed"}

Write-Host "`n=== Reconcile adjudicated matrix ===" -ForegroundColor Cyan
& $py "$root\scripts\Reconcile-Wave2DApplicabilityAfterHumanReview.py" --root $root --spec $spec
if($LASTEXITCODE){Fail "Matrix reconciliation failed"}

Write-Host "`n=== Re-run applicability adjudication to prove HUMAN_* persistence ===" -ForegroundColor Cyan
& "$root\scripts\Run-Wave2DApplicabilityAdjudication.ps1" -EMSPath $root
if(-not $?){Fail "Applicability rerun failed"}

$summary=Get-Content "$root\generated\wave2d\evaluation-matrix\applicability_adjudication_summary.json" -Raw|ConvertFrom-Json
if([int]$summary.review_required_count -ne 0){Fail "REVIEW_REQUIRED rows remain after human adjudication"}
if([int]$summary.pending_count -ne 0){Fail "Pending rows remain after human adjudication"}
if([int]$summary.matrix_row_count -ne 560){Fail "Matrix row count is not 560"}
if($summary.evaluation_performed -ne $false -or $summary.promotion_performed -ne $false){Fail "Unexpected evaluation/promotion state"}

Write-Host "PASS: all 560 applicability rows resolved by policy or preserved human adjudication." -ForegroundColor Green
