[CmdletBinding()]
param([string]$EMSPath = "C:\temp\standars\ems")

$ErrorActionPreference = "Stop"
$here = Split-Path -Parent $MyInvocation.MyCommand.Path

foreach ($n in @(
    "Populate-Wave2DHumanApplicabilityDecisions.ps1",
    "Test-Wave2DHumanApplicabilityDecisions.ps1"
)) {
    Copy-Item (Join-Path $here $n) (Join-Path $EMSPath "scripts\$n") -Force
}

Write-Host "Wave 2D human applicability population tooling installed." -ForegroundColor Green
