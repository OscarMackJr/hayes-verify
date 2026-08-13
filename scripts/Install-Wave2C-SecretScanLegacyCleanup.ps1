[CmdletBinding()]
param([string]$EMSPath="C:\temp\standars\ems")

$ErrorActionPreference="Stop"
$here=Split-Path -Parent $MyInvocation.MyCommand.Path

foreach($n in @(
    "Cleanup-Wave2C-SecretScanLegacyMaintenance.ps1",
    "Test-Wave2C-SecretScanLegacyCleanup.ps1",
    "CommitPush-Wave2C-SecretScanLegacyCleanup.ps1"
)){
    Copy-Item (Join-Path $here $n) (Join-Path $EMSPath "scripts\$n") -Force
}
Write-Host "Wave 2C secret-scan legacy-maintenance cleanup tooling installed." -ForegroundColor Green
