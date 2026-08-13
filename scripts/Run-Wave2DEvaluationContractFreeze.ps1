[CmdletBinding()]
param([string]$EMSPath="C:\temp\standars\ems")
$ErrorActionPreference="Stop"
function Fail([string]$m){throw "WAVE 2D CONTRACT FREEZE BLOCKED: $m"}

$root=(Resolve-Path $EMSPath).Path
$spec="$root\registry\wave2d_evaluation_contract_spec.json"
if((git -C $root branch --show-current).Trim() -ne "feature/wave2d-evaluation-contract"){Fail "Wrong branch"}

$py=if($env:VIRTUAL_ENV -and (Test-Path "$env:VIRTUAL_ENV\Scripts\python.exe")){"$env:VIRTUAL_ENV\Scripts\python.exe"}else{(Get-Command python).Source}

Write-Host "=== Freeze Wave 2D evidence/evaluation contracts ===" -ForegroundColor Cyan
& $py "$root\scripts\Freeze-Wave2DEvaluationContract.py" --root $root --spec $spec
if($LASTEXITCODE){Fail "Contract freeze failed"}

Write-Host "`n=== Validate contract hashes and authority boundaries ===" -ForegroundColor Cyan
& $py "$root\scripts\Validate-Wave2DEvaluationContract.py" --root $root --spec $spec
if($LASTEXITCODE){Fail "Contract validation failed"}

Write-Host "PASS: Wave 2D Evidence & Evaluation Contract frozen." -ForegroundColor Green
Write-Host "No evidence collection, evaluation, or promotion performed."
