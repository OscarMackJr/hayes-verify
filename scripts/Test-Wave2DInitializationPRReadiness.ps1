[CmdletBinding()]
param([string]$EMSPath="C:\temp\standars\ems")

$ErrorActionPreference="Stop"
function Fail([string]$m){throw "WAVE 2D INIT PR READINESS BLOCKED: $m"}

$root=(Resolve-Path $EMSPath).Path
$branch=(git -C $root branch --show-current).Trim()
if($branch -ne "feature/wave2d-initialization"){
    Fail "Expected feature/wave2d-initialization; current=$branch"
}

$protect=Join-Path $root "scripts\Test-Wave2DProtectedBaseline.ps1"
if(-not(Test-Path $protect)){Fail "Protected-baseline validator missing: $protect"}

& $protect -EMSPath $root
if(-not $?){Fail "Wave 2C protected-baseline validation failed."}

$allowed=@(
    "generated/wave2d/initialization_record.json",
    "registry/wave2d/population.json",
    "registry/wave2d/scope.json",
    "registry/wave2d_initialization_spec.json",
    "schemas/wave2d_initialization_record.schema.json",
    "scripts/Show-Wave2DInitialization.ps1",
    "scripts/Stage-Wave2DInitialization.ps1",
    "scripts/Test-Wave2DProtectedBaseline.ps1"
)

$staged=@(git -C $root diff --cached --name-only)
if($staged.Count -eq 0){Fail "No staged Wave 2D initialization files found."}

$bad=@($staged | Where-Object {$_ -notin $allowed})
if($bad.Count -gt 0){
    Write-Host "Out-of-scope staged paths:" -ForegroundColor Red
    $bad | ForEach-Object {Write-Host $_}
    Fail "Staged scope is invalid."
}

$missing=@($allowed | Where-Object {$_ -notin $staged})
if($missing.Count -gt 0){
    Write-Host "Missing expected staged paths:" -ForegroundColor Red
    $missing | ForEach-Object {Write-Host $_}
    Fail "Wave 2D initialization staging is incomplete."
}

Write-Host "=== Staged Wave 2D initialization ===" -ForegroundColor Cyan
git -C $root diff --cached --name-status
git -C $root diff --cached --stat

Write-Host "PASS: Wave 2D initialization branch is ready for commit/push." -ForegroundColor Green
