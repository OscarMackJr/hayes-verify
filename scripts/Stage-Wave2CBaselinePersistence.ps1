[CmdletBinding()]
param([string]$EMSPath="C:\temp\standars\ems")
$ErrorActionPreference="Stop"
function Fail([string]$m){throw "WAVE 2C BASELINE STAGE BLOCKED: $m"}

$root=(Resolve-Path $EMSPath).Path
$spec=Get-Content (Join-Path $root "registry\wave2c_baseline_persistence_spec.json") -Raw|ConvertFrom-Json
$branch=(git -C $root branch --show-current).Trim()
if($branch -ne $spec.branch){Fail "Expected $($spec.branch); current=$branch"}

foreach($rel in @($spec.durable_paths)){
    if(-not(Test-Path (Join-Path $root ($rel -replace '/','\')))){Fail "Missing durable artifact: $rel"}
    git -C $root add -- $rel
    if($LASTEXITCODE){Fail "Failed to stage $rel"}
}
git -C $root add -- "registry/wave2c_baseline_persistence_spec.json"

$staged=@(git -C $root diff --cached --name-only)
$allowed=@($spec.durable_paths + "registry/wave2c_baseline_persistence_spec.json")
$bad=@($staged|Where-Object{$_ -notin $allowed})
if($bad.Count -gt 0){
    $bad|ForEach-Object{Write-Host $_}
    Fail "Out-of-scope staged paths detected."
}

Write-Host "=== Staged baseline-registration changes ===" -ForegroundColor Cyan
git -C $root diff --cached --name-status
Write-Host "PASS: durable baseline-registration artifacts staged." -ForegroundColor Green
