[CmdletBinding()]
param([string]$EMSPath="C:\temp\standars\ems")

$ErrorActionPreference="Stop"
$here=Split-Path -Parent $MyInvocation.MyCommand.Path

foreach($n in @(
    "Test-Wave2C-PostPushReadiness.ps1",
    "Patch-Wave2C-MergeGatePostPushReadiness.ps1",
    "Test-Wave2C-MergeGatePostPushReadiness.ps1"
)){
    Copy-Item (Join-Path $here $n) (Join-Path $EMSPath "scripts\$n") -Force
}

Write-Host "Wave 2C post-push merge-gate hotfix installed." -ForegroundColor Green
