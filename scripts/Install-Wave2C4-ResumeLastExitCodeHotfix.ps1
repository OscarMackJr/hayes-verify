[CmdletBinding()]
param([string]$EMSPath="C:\temp\standars\ems")
$ErrorActionPreference="Stop"
$here=Split-Path -Parent $MyInvocation.MyCommand.Path

foreach($n in @(
    "Patch-Wave2C4-ResumeLastExitCode.ps1",
    "Test-Wave2C4-ResumeLastExitCode.ps1"
)){
    Copy-Item (Join-Path $here $n) (Join-Path $EMSPath "scripts\$n") -Force
}

Write-Host "Wave 2C.4 resume stale-LASTEXITCODE hotfix installed." -ForegroundColor Green
