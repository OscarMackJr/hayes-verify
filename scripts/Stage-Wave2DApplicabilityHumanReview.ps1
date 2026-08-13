[CmdletBinding()]
param([string]$EMSPath="C:\temp\standars\ems")
$ErrorActionPreference="Stop"
function Fail([string]$m){throw "WAVE 2D HUMAN ADJUDICATION STAGE BLOCKED: $m"}

$root=(Resolve-Path $EMSPath).Path
$record="$root\generated\wave2d\evaluation-matrix\applicability_human_review_record.json"
$summary="$root\generated\wave2d\evaluation-matrix\applicability_adjudication_summary.json"

if(-not(Test-Path $record) -or -not(Test-Path $summary)){Fail "Required review artifacts missing"}
$r=Get-Content $record -Raw|ConvertFrom-Json
$s=Get-Content $summary -Raw|ConvertFrom-Json

if($r.status -ne "PASS"){Fail "Human review record not PASS"}
if([int]$r.remaining_review_required_count -ne 0){Fail "Human review record still has unresolved rows"}
if([int]$s.review_required_count -ne 0 -or [int]$s.pending_count -ne 0){Fail "Applicability summary still unresolved"}
if([int]$s.matrix_row_count -ne 560){Fail "Matrix row count is not 560"}
if($s.evaluation_performed -ne $false -or $s.promotion_performed -ne $false){Fail "Unexpected evaluation/promotion state"}

$allowed=@(
    "registry/wave2d_applicability_human_review_spec.json",
    "schemas/wave2d_applicability_human_review_record.schema.json",
    "registry/wave2d/applicability_review_queue.csv",
    "registry/wave2d/applicability_review_template.csv",
    "registry/wave2d/applicability_review_decisions.csv",
    "registry/wave2d/applicability_decisions.csv",
    "generated/wave2d/evaluation-matrix/evaluation_matrix_adjudicated.csv",
    "generated/wave2d/evaluation-matrix/applicability_adjudication_summary.json",
    "generated/wave2d/evaluation-matrix/applicability_human_review_record.json",
    "scripts/Build-Wave2DApplicabilityReviewQueue.py",
    "scripts/Validate-Wave2DHumanApplicabilityDecisions.py",
    "scripts/Apply-Wave2DHumanApplicabilityDecisions.py",
    "scripts/Reconcile-Wave2DApplicabilityAfterHumanReview.py",
    "scripts/Run-Wave2DApplicabilityHumanReview.ps1",
    "scripts/Show-Wave2DApplicabilityHumanReview.ps1",
    "scripts/Stage-Wave2DApplicabilityHumanReview.ps1"
)

foreach($rel in $allowed){
    $full=Join-Path $root ($rel -replace '/','\')
    if(-not(Test-Path $full)){Fail "Missing expected human-review artifact: $rel"}
    if($rel.StartsWith("generated/")){git -C $root add -f -- $rel}else{git -C $root add -- $rel}
    if($LASTEXITCODE){Fail "Failed to stage $rel"}
}

git -C $root diff --cached --name-status
Write-Host "PASS: Wave 2D applicability human-adjudication artifacts staged." -ForegroundColor Green
