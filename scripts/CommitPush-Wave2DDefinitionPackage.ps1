[CmdletBinding()]
param(
    [string]$EMSPath="C:\temp\standars\ems",
    [string]$CommitMessage="freeze Wave 2D scope and applicability matrix"
)
$ErrorActionPreference="Stop"
function Fail([string]$m){throw "WAVE 2D DEFINITION COMMIT/PUSH BLOCKED: $m"}

$root=(Resolve-Path $EMSPath).Path
& "$root\scripts\Test-Wave2DDefinitionPRReadiness.ps1" -EMSPath $root
if(-not $?){Fail "Readiness validation failed"}

git -C $root commit -m $CommitMessage
if($LASTEXITCODE){Fail "git commit failed"}

git -C $root push -u origin feature/wave2d-scope-population
if($LASTEXITCODE){Fail "git push failed"}

$local=(git -C $root rev-parse HEAD).Trim()
$remote=(git -C $root rev-parse origin/feature/wave2d-scope-population).Trim()
if($local -ne $remote){Fail "Local/remote HEAD mismatch"}

Write-Host "PASS: Wave 2D definition branch committed and pushed." -ForegroundColor Green
Write-Host "HEAD: $local"
