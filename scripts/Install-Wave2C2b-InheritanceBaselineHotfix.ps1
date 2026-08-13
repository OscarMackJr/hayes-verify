[CmdletBinding()]
param([string]$EMSPath="C:\temp\standars\ems")

$ErrorActionPreference="Stop"
$here=Split-Path -Parent $MyInvocation.MyCommand.Path

foreach($n in @(
    "Patch-Wave2B1-InheritanceBaselinePath.ps1",
    "Rerun-Wave2C2b-Inheritance.ps1",
    "Show-Wave2C2b-Inheritance.ps1"
)){
    Copy-Item (Join-Path $here $n) (Join-Path $EMSPath "scripts\$n") -Force
}

Write-Host "Wave 2C.2b inheritance baseline hotfix tooling installed." -ForegroundColor Green
