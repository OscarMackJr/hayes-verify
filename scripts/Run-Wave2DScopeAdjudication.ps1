[CmdletBinding()]
param(
    [string]$EMSPath="C:\temp\standars\ems",
    [switch]$AllowReviewRequired
)
$ErrorActionPreference="Stop"
function Fail([string]$m){throw "WAVE 2D ADJUDICATION BLOCKED: $m"}

$root=(Resolve-Path $EMSPath).Path
$spec=Join-Path $root "registry\wave2d_scope_adjudication_spec.json"
if(-not(Test-Path $spec)){Fail "Adjudication spec missing."}

$branch=(git -C $root branch --show-current).Trim()
if($branch -ne "feature/wave2d-scope-population"){Fail "Expected feature/wave2d-scope-population; current=$branch"}

$py=if($env:VIRTUAL_ENV -and (Test-Path "$env:VIRTUAL_ENV\Scripts\python.exe")){"$env:VIRTUAL_ENV\Scripts\python.exe"}else{(Get-Command python).Source}

Write-Host "=== Pass 1: Adjudicate control scope ===" -ForegroundColor Cyan
& $py "$root\scripts\Adjudicate-Wave2DControls.py" --root $root --spec $spec
if($LASTEXITCODE){Fail "Control adjudication failed."}

Write-Host "`n=== Pass 2: Adjudicate evaluation targets ===" -ForegroundColor Cyan
& $py "$root\scripts\Adjudicate-Wave2DTargets.py" --root $root --spec $spec
if($LASTEXITCODE){Fail "Target adjudication failed."}

Write-Host "`n=== Pass 3: Finalize Wave 2D decisions ===" -ForegroundColor Cyan
& $py "$root\scripts\Finalize-Wave2DAdjudication.py" --root $root --spec $spec
$exit=$LASTEXITCODE

if($exit -eq 2 -and $AllowReviewRequired){
    Write-Host "WARNING: adjudication produced REVIEW_REQUIRED/UNDECIDED rows; no evaluation or promotion performed." -ForegroundColor Yellow
    exit 0
}
if($exit){Fail "Finalization gate blocked. Resolve REVIEW_REQUIRED/UNDECIDED rows."}

Write-Host "`nPASS: Wave 2D scope adjudication finalized with zero unresolved rows." -ForegroundColor Green
Write-Host "No evaluation or promotion performed."
