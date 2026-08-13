[CmdletBinding()]
param([string]$EMSPath="C:\temp\standars\ems")

$ErrorActionPreference="Stop"
$here=Split-Path -Parent $MyInvocation.MyCommand.Path

foreach($n in @(
    "Test-Wave2DInitializationPRReadiness.ps1",
    "CommitPush-Wave2DInitialization.ps1",
    "Create-Wave2DInitializationPR.ps1",
    "Run-Wave2DInitializationCommitPushPR.ps1"
)){
    Copy-Item (Join-Path $here $n) (Join-Path $EMSPath "scripts\$n") -Force
}

Write-Host "Wave 2D initialization commit/push/PR tooling installed." -ForegroundColor Green
