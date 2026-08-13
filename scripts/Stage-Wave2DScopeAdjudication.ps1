[CmdletBinding()]
param([string]$EMSPath="C:\temp\standars\ems")
$ErrorActionPreference="Stop"
function Fail([string]$m){throw "WAVE 2D ADJUDICATION STAGE BLOCKED: $m"}

$root=(Resolve-Path $EMSPath).Path
$report="$root\generated\wave2d\scope-definition\adjudication_report.json"
if(-not(Test-Path $report)){Fail "Adjudication report missing."}
$r=Get-Content $report -Raw|ConvertFrom-Json
if($r.status -ne "PASS"){Fail "Adjudication report not PASS."}
if([int]$r.review_required_count -ne 0){Fail "REVIEW_REQUIRED rows remain."}
if([int]$r.undecided_count -ne 0){Fail "UNDECIDED rows remain."}
if($r.evaluation_performed -ne $false -or $r.promotion_performed -ne $false){Fail "Unexpected evaluation/promotion state."}

$allowed=@(
    "registry/wave2d_scope_adjudication_spec.json",
    "schemas/wave2d_scope_adjudication_report.schema.json",
    "registry/wave2d/control_scope_decisions.csv",
    "registry/wave2d/evaluation_target_decisions.csv",
    "registry/wave2d/scope.json",
    "registry/wave2d/population.json",
    "generated/wave2d/scope-definition/adjudication_report.json",
    "scripts/Adjudicate-Wave2DControls.py",
    "scripts/Adjudicate-Wave2DTargets.py",
    "scripts/Finalize-Wave2DAdjudication.py",
    "scripts/Run-Wave2DScopeAdjudication.ps1",
    "scripts/Show-Wave2DScopeAdjudication.ps1",
    "scripts/Stage-Wave2DScopeAdjudication.ps1"
)

foreach($rel in $allowed){
    $full=Join-Path $root ($rel -replace '/','\')
    if(-not(Test-Path $full)){Fail "Missing expected adjudication artifact: $rel"}
    if($rel.StartsWith("generated/")){git -C $root add -f -- $rel}else{git -C $root add -- $rel}
    if($LASTEXITCODE){Fail "Failed to stage $rel"}
}

$staged=@(git -C $root diff --cached --name-only)
$bad=@($staged|Where-Object{$_ -notin $allowed -and $_ -notmatch '^generated/wave2d/scope-definition/' -and $_ -notmatch '^registry/wave2d/' -and $_ -notmatch '^scripts/(Discover|Initialize|Build|Validate|Run-Wave2DScopePopulation|Show-Wave2DScopePopulation|Stage-Wave2DScopePopulation)' -and $_ -notmatch '^registry/wave2d_scope_population_spec.json$' -and $_ -notmatch '^schemas/wave2d_scope_population_summary.schema.json$'})
if($bad.Count -gt 0){
    $bad|ForEach-Object{Write-Host $_}
    Fail "Unexpected staged path outside Wave 2D scope/adjudication set."
}

git -C $root diff --cached --name-status
Write-Host "PASS: Wave 2D adjudication artifacts staged." -ForegroundColor Green
