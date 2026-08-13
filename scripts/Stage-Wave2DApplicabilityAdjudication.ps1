[CmdletBinding()]
param([string]$EMSPath="C:\temp\standars\ems")
$ErrorActionPreference="Stop"
function Fail([string]$m){throw "WAVE 2D APPLICABILITY STAGE BLOCKED: $m"}

$root=(Resolve-Path $EMSPath).Path
$validation="$root\generated\wave2d\evaluation-matrix\applicability_adjudication_validation.json"
$summary="$root\generated\wave2d\evaluation-matrix\applicability_adjudication_summary.json"

if(-not(Test-Path $validation) -or -not(Test-Path $summary)){Fail "Applicability artifacts missing"}
$v=Get-Content $validation -Raw|ConvertFrom-Json
$s=Get-Content $summary -Raw|ConvertFrom-Json

if($v.status -ne "PASS"){Fail "Applicability validation is not PASS"}
if([int]$v.matrix_row_count -ne 560){Fail "Matrix row count is not 560"}
if([int]$s.pending_count -ne 0){Fail "Pending applicability rows remain"}
if([int]$s.review_required_count -ne 0){Fail "REVIEW_REQUIRED rows remain"}
if($s.evaluation_performed -ne $false -or $s.promotion_performed -ne $false){Fail "Unexpected evaluation/promotion state"}

$allowed=@(
    "registry/wave2d_applicability_adjudication_spec.json",
    "schemas/wave2d_applicability_adjudication_summary.schema.json",
    "registry/wave2d/applicability_rules.json",
    "registry/wave2d/applicability_decisions.csv",
    "generated/wave2d/evaluation-matrix/evaluation_matrix_adjudicated.csv",
    "generated/wave2d/evaluation-matrix/applicability_adjudication_summary.json",
    "generated/wave2d/evaluation-matrix/applicability_adjudication_validation.json",
    "scripts/Build-Wave2DApplicabilityRules.py",
    "scripts/Adjudicate-Wave2DApplicability.py",
    "scripts/Apply-Wave2DApplicability.py",
    "scripts/Validate-Wave2DApplicability.py",
    "scripts/Run-Wave2DApplicabilityAdjudication.ps1",
    "scripts/Show-Wave2DApplicabilityAdjudication.ps1",
    "scripts/Stage-Wave2DApplicabilityAdjudication.ps1"
)

foreach($rel in $allowed){
    $full=Join-Path $root ($rel -replace '/','\')
    if(-not(Test-Path $full)){Fail "Missing expected applicability artifact: $rel"}
    if($rel.StartsWith("generated/")){git -C $root add -f -- $rel}else{git -C $root add -- $rel}
    if($LASTEXITCODE){Fail "Failed to stage $rel"}
}

git -C $root diff --cached --name-status
Write-Host "PASS: Wave 2D applicability adjudication artifacts staged." -ForegroundColor Green
