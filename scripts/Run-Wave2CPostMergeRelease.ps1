[CmdletBinding()]
param(
    [string]$EMSPath="C:\temp\standars\ems"
)

$ErrorActionPreference="Stop"
function Fail([string]$m){throw "WAVE 2C POST-MERGE RELEASE BLOCKED: $m"}

$root=(Resolve-Path $EMSPath).Path
$spec=Join-Path $root "registry\wave2c_post_merge_release_spec.json"
$out=Join-Path $root "release\wave2c\post-merge"
New-Item -ItemType Directory -Force -Path $out|Out-Null

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

Write-Host "=== Verify main branch and post-merge state ===" -ForegroundColor Cyan
git -C $root fetch origin main --tags
if($LASTEXITCODE){Fail "git fetch failed."}

Write-Host "`n=== Certify Wave 2C post-merge state ===" -ForegroundColor Cyan
$cert=Join-Path $out "post_merge_certification.json"
& $py (Join-Path $root "scripts\Certify-Wave2CPostMerge.py") `
    --root $root `
    --spec $spec `
    --out $cert
if($LASTEXITCODE){Fail "Post-merge certification failed."}

Write-Host "`n=== Freeze final Wave 2C release package ===" -ForegroundColor Cyan
& $py (Join-Path $root "scripts\Freeze-Wave2CPostMergeRelease.py") `
    --root $root `
    --spec $spec `
    --certification $cert `
    --outdir $out
if($LASTEXITCODE){Fail "Post-merge release freeze failed."}

Write-Host "`nPASS: Wave 2C post-merge release certification complete. Tag not yet created." -ForegroundColor Green
