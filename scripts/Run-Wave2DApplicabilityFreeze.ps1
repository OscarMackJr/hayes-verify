[CmdletBinding()]
param([string]$EMSPath="C:\temp\standars\ems")
$ErrorActionPreference="Stop"
function Fail([string]$m){throw "WAVE 2D APPLICABILITY FREEZE BLOCKED: $m"}

$root=(Resolve-Path $EMSPath).Path
$spec=Join-Path $root "registry\wave2d_applicability_freeze_pr_spec.json"
$branch=(git -C $root branch --show-current).Trim()
if($branch -ne "feature/wave2d-scope-population"){Fail "Expected feature/wave2d-scope-population; current=$branch"}

$py=if($env:VIRTUAL_ENV -and (Test-Path "$env:VIRTUAL_ENV\Scripts\python.exe")){"$env:VIRTUAL_ENV\Scripts\python.exe"}else{(Get-Command python).Source}

Write-Host "=== Freeze final Wave 2D applicability matrix ===" -ForegroundColor Cyan
& $py "$root\scripts\Freeze-Wave2DApplicability.py" --root $root --spec $spec
if($LASTEXITCODE){Fail "Applicability freeze failed"}

Write-Host "`n=== Validate frozen applicability ===" -ForegroundColor Cyan
& $py "$root\scripts\Validate-Wave2DApplicabilityFreeze.py" --root $root --spec $spec
if($LASTEXITCODE){Fail "Applicability freeze validation failed"}

Write-Host "PASS: Wave 2D applicability frozen for evaluation." -ForegroundColor Green
