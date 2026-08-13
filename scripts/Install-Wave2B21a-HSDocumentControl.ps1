
[CmdletBinding()]
param([string]$EMSPath="C:\temp\standars\ems")

$ErrorActionPreference="Stop"
$pkg=Split-Path -Parent $PSScriptRoot

foreach($n in @(
    "Apply-Wave2B21a-HSDocumentControlFix.ps1",
    "Test-Wave2B21a-HSDocumentControlFix.ps1",
    "Run-Wave2B21a-HSDocumentControl.ps1",
    "Show-Wave2B21a-HSDocumentControl.ps1"
)){
    Copy-Item "$pkg\scripts\$n" "$EMSPath\scripts\$n" -Force
}

Write-Host "Wave 2B.2.1a tooling installed." -ForegroundColor Green
