[CmdletBinding()]
param([string]$EMSPath="C:\temp\standars\ems")
$ErrorActionPreference="Stop"
$pkg=(Resolve-Path (Join-Path $PSScriptRoot "..")).Path

New-Item -ItemType Directory -Force -Path "$EMSPath\scripts","$EMSPath\registry"|Out-Null

Get-ChildItem (Join-Path $pkg "scripts") -File | ForEach-Object {
    Copy-Item $_.FullName (Join-Path $EMSPath "scripts\$($_.Name)") -Force
}
Copy-Item (Join-Path $pkg "registry\wave2c_branch_finalization_spec.json") `
          (Join-Path $EMSPath "registry\wave2c_branch_finalization_spec.json") -Force

Write-Host "Wave 2C Branch Finalization & Merge Gate tooling installed." -ForegroundColor Green
