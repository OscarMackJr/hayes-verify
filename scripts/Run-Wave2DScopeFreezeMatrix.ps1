[CmdletBinding()]
param([string]$EMSPath="C:\temp\standars\ems")
$ErrorActionPreference="Stop"
function Fail([string]$m){throw "WAVE 2D SCOPE FREEZE BLOCKED: $m"}

$root=(Resolve-Path $EMSPath).Path
$spec=Join-Path $root "registry\wave2d_scope_freeze_matrix_spec.json"
$branch=(git -C $root branch --show-current).Trim()
if($branch -ne "feature/wave2d-scope-population"){Fail "Expected feature/wave2d-scope-population; current=$branch"}

$py=if($env:VIRTUAL_ENV -and (Test-Path "$env:VIRTUAL_ENV\Scripts\python.exe")){"$env:VIRTUAL_ENV\Scripts\python.exe"}else{(Get-Command python).Source}

Write-Host "=== Freeze Wave 2D scope and population ===" -ForegroundColor Cyan
& $py "$root\scripts\Freeze-Wave2DScopePopulation.py" --root $root --spec $spec
if($LASTEXITCODE){Fail "Scope/population freeze failed"}

Write-Host "`n=== Construct 80 x 7 evaluation matrix ===" -ForegroundColor Cyan
& $py "$root\scripts\Build-Wave2DEvaluationMatrix.py" --root $root --spec $spec
if($LASTEXITCODE){Fail "Evaluation matrix construction failed"}

Write-Host "`n=== Validate matrix coverage and fail-closed state ===" -ForegroundColor Cyan
& $py "$root\scripts\Validate-Wave2DEvaluationMatrix.py" --root $root --spec $spec
if($LASTEXITCODE){Fail "Evaluation matrix validation failed"}

Write-Host "`nPASS: Wave 2D scope frozen and evaluation matrix constructed." -ForegroundColor Green
Write-Host "No evaluation or promotion performed."
