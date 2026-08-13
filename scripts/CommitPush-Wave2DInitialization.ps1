[CmdletBinding()]
param(
    [string]$EMSPath="C:\temp\standars\ems",
    [string]$CommitMessage="initialize Wave 2D from authoritative Wave 2C baseline"
)

$ErrorActionPreference="Stop"
function Fail([string]$m){throw "WAVE 2D INIT COMMIT/PUSH BLOCKED: $m"}

$root=(Resolve-Path $EMSPath).Path

Write-Host "=== Validate Wave 2D initialization readiness ===" -ForegroundColor Cyan
& (Join-Path $root "scripts\Test-Wave2DInitializationPRReadiness.ps1") -EMSPath $root
if(-not $?){Fail "Wave 2D initialization readiness failed."}

Write-Host "`n=== Commit Wave 2D initialization ===" -ForegroundColor Cyan
git -C $root commit -m $CommitMessage
if($LASTEXITCODE){Fail "git commit failed."}

Write-Host "`n=== Push Wave 2D initialization branch ===" -ForegroundColor Cyan
git -C $root push -u origin feature/wave2d-initialization
if($LASTEXITCODE){Fail "git push failed."}

$local=(git -C $root rev-parse HEAD).Trim()
$remote=(git -C $root rev-parse origin/feature/wave2d-initialization).Trim()
if($local -ne $remote){Fail "Local HEAD does not match pushed remote branch."}

Write-Host "PASS: Wave 2D initialization committed and pushed." -ForegroundColor Green
Write-Host "HEAD: $local"
