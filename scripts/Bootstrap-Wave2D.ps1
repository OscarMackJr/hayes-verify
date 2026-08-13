[CmdletBinding()]
param(
    [string]$EMSPath="C:\temp\standars\ems",
    [string]$Branch="feature/wave2d-initialization"
)

$ErrorActionPreference="Stop"
function Fail([string]$m){throw "WAVE 2D BOOTSTRAP BLOCKED: $m"}

$root=(Resolve-Path $EMSPath).Path

git -C $root fetch origin main --tags
if($LASTEXITCODE){Fail "git fetch failed."}

$branch=(git -C $root branch --show-current).Trim()
if($branch -ne "main"){Fail "Expected main; current=$branch"}

$status=@(git -C $root status --porcelain)
if($status.Count -gt 0){
    $status|ForEach-Object{Write-Host $_}
    Fail "main must be clean before Wave 2D bootstrap."
}

Write-Host "=== Verify authoritative Wave 2C baseline ===" -ForegroundColor Cyan
$py=$null
if($env:VIRTUAL_ENV){
    $candidate=Join-Path $env:VIRTUAL_ENV "Scripts\python.exe"
    if(Test-Path $candidate){$py=$candidate}
}
if(-not $py){
    $cmd=Get-Command python -ErrorAction SilentlyContinue
    if($cmd){$py=$cmd.Source}
}
if(-not $py){Fail "No usable Python interpreter found."}

& $py (Join-Path $root "scripts\Verify-Wave2DBaseline.py") `
    --root $root `
    --spec (Join-Path $root "registry\wave2d_initialization_spec.json")
if($LASTEXITCODE){Fail "Wave 2C baseline verification failed."}

git -C $root switch -c $Branch
if($LASTEXITCODE){Fail "Failed to create Wave 2D branch."}

Write-Host "=== Initialize Wave 2D scope and population ===" -ForegroundColor Cyan
& $py (Join-Path $root "scripts\Initialize-Wave2D.py") `
    --root $root `
    --spec (Join-Path $root "registry\wave2d_initialization_spec.json") `
    --out (Join-Path $root "generated\wave2d\initialization_record.json")
if($LASTEXITCODE){Fail "Wave 2D initialization failed."}

& (Join-Path $root "scripts\Test-Wave2DProtectedBaseline.ps1") -EMSPath $root
if(-not $?){Fail "Wave 2C protection gate failed."}

Write-Host "PASS: Wave 2D initialized from authoritative Wave 2C baseline." -ForegroundColor Green
