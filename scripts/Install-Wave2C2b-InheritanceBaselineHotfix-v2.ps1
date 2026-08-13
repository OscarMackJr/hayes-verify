[CmdletBinding()]
param([string]$EMSPath="C:\temp\standars\ems")

$ErrorActionPreference="Stop"
$here=Split-Path -Parent $MyInvocation.MyCommand.Path

foreach($n in @(
    "Patch-Wave2B1-InheritanceBaselinePath-v2.ps1",
    "Test-Wave2B1-InheritanceBaselinePath-v2.ps1"
)){
    Copy-Item (Join-Path $here $n) (Join-Path $EMSPath "scripts\$n") -Force
}

Write-Host "Wave 2C.2b inheritance baseline hotfix v2 installed." -ForegroundColor Green
