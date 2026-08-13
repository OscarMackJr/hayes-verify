[CmdletBinding()]
param([string]$EMSPath="C:\temp\standars\ems")
$ErrorActionPreference="Stop"
function Fail([string]$m){throw "WAVE 2D MATRIX STAGE BLOCKED: $m"}

$root=(Resolve-Path $EMSPath).Path
$validation="$root\generated\wave2d\evaluation-matrix\evaluation_matrix_validation.json"
if(-not(Test-Path $validation)){Fail "Matrix validation artifact missing"}
$v=Get-Content $validation -Raw|ConvertFrom-Json
if($v.status -ne "PASS"){Fail "Matrix validation is not PASS"}
if([int]$v.matrix_row_count -ne 560){Fail "Matrix row count is not 560"}
if($v.evaluation_performed -ne $false -or $v.promotion_performed -ne $false){Fail "Unexpected evaluation/promotion state"}

$allowed=@(
    "registry/wave2d_scope_freeze_matrix_spec.json",
    "schemas/wave2d_evaluation_matrix_summary.schema.json",
    "generated/wave2d/scope-freeze/scope_freeze.json",
    "generated/wave2d/scope-freeze/population_freeze.json",
    "generated/wave2d/evaluation-matrix/evaluation_matrix.csv",
    "generated/wave2d/evaluation-matrix/evaluation_matrix_summary.json",
    "generated/wave2d/evaluation-matrix/evaluation_matrix_validation.json",
    "scripts/Freeze-Wave2DScopePopulation.py",
    "scripts/Build-Wave2DEvaluationMatrix.py",
    "scripts/Validate-Wave2DEvaluationMatrix.py",
    "scripts/Run-Wave2DScopeFreezeMatrix.ps1",
    "scripts/Show-Wave2DScopeFreezeMatrix.ps1",
    "scripts/Stage-Wave2DScopeFreezeMatrix.ps1"
)

foreach($rel in $allowed){
    $full=Join-Path $root ($rel -replace '/','\')
    if(-not(Test-Path $full)){Fail "Missing expected matrix artifact: $rel"}
    if($rel.StartsWith("generated/")){git -C $root add -f -- $rel}else{git -C $root add -- $rel}
    if($LASTEXITCODE){Fail "Failed to stage $rel"}
}

git -C $root diff --cached --name-status
Write-Host "PASS: Wave 2D scope-freeze/matrix artifacts staged." -ForegroundColor Green
