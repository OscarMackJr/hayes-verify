[CmdletBinding()]
param(
    [string]$EMSPath="C:\temp\standars\ems",
    [string]$Message="persist Wave 2C baseline registration"
)
$ErrorActionPreference="Stop"
function Fail([string]$m){throw "WAVE 2C BASELINE COMMIT BLOCKED: $m"}

$root=(Resolve-Path $EMSPath).Path
& (Join-Path $root "scripts\Stage-Wave2CBaselinePersistence.ps1") -EMSPath $root
if(-not $?){Fail "Staging validation failed"}

git -C $root commit -m $Message
if($LASTEXITCODE){Fail "git commit failed"}

git -C $root push -u origin chore/wave2c-baseline-registration
if($LASTEXITCODE){Fail "git push failed"}

Write-Host "PASS: baseline-registration branch committed and pushed." -ForegroundColor Green
