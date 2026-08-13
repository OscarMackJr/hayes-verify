[CmdletBinding()]
param([string]$EMSPath="C:\temp\standars\ems")

$ErrorActionPreference="Stop"
$pkg=Split-Path -Parent $PSScriptRoot

foreach($n in @(
 "Apply-Wave2B23a-CTRL075Refinement.ps1",
 "Test-Wave2B23a-CTRL075Refinement.ps1",
 "Run-Wave2B23a-CTRL075Refinement.ps1",
 "Show-Wave2B23a-CTRL075Refinement.ps1"
)){
    Copy-Item "$pkg\scripts\$n" "$EMSPath\scripts\$n" -Force
}

Write-Host "Wave 2B.2.3a CTRL-075 refinement tooling installed." -ForegroundColor Green
