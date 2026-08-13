[CmdletBinding()]
param(
    [string]$EMSPath="C:\temp\standars\ems",
    [string]$ArchiveRoot="C:\temp\standars\ems-local-archive\releases",
    [switch]$Archive
)

$ErrorActionPreference="Stop"
function Fail([string]$m){throw "WAVE 2C POST-RELEASE BLOCKED: $m"}

$root=(Resolve-Path $EMSPath).Path
$spec=Join-Path $root "registry\wave2c_post_release_archive_spec.json"
$out=Join-Path $root "registry\release_baselines\wave2c_baseline_registration.json"

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

Write-Host "=== Register Wave 2C authoritative baseline ===" -ForegroundColor Cyan
& $py (Join-Path $root "scripts\Register-Wave2CBaseline.py") `
    --root $root `
    --spec $spec `
    --out $out
if($LASTEXITCODE){Fail "Baseline registration failed."}

if($Archive){
    Write-Host "`n=== Archive Wave 2C release externally ===" -ForegroundColor Cyan
    & (Join-Path $root "scripts\Archive-Wave2CRelease.ps1") `
        -EMSPath $root `
        -ArchiveRoot $ArchiveRoot
    if(-not $?){Fail "External archive failed."}
}

Write-Host "`nPASS: Wave 2C post-release baseline registration complete." -ForegroundColor Green
