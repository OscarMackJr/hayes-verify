[CmdletBinding()]
param([string]$EMSPath="C:\temp\standars\ems")

$ErrorActionPreference="Stop"
$here=Split-Path -Parent $MyInvocation.MyCommand.Path

foreach($n in @(
    "Test-Wave2C4-AlreadyPromotedState.ps1",
    "Patch-Wave2C4-AlreadyPromotedResume.ps1",
    "Resume-Wave2C4-Closeout.ps1"
)){
    Copy-Item (Join-Path $here $n) (Join-Path $EMSPath "scripts\$n") -Force
}

Write-Host "Wave 2C.4 already-promoted closeout resume hotfix installed." -ForegroundColor Green
