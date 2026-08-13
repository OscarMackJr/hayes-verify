[CmdletBinding()]
param(
    [string]$EMSPath = "C:\temp\standars\ems"
)

$ErrorActionPreference = "Stop"
$here = Split-Path -Parent $MyInvocation.MyCommand.Path

if (-not (Test-Path $EMSPath)) { throw "EMS repository not found: $EMSPath" }
$dest = Join-Path $EMSPath "scripts"
New-Item -ItemType Directory -Path $dest -Force | Out-Null

foreach ($name in @(
    "Apply-Wave2B23a-CTRL075-Hotfix.ps1",
    "Test-Wave2B23a-CTRL075-Hotfix.ps1",
    "Rerun-Wave2B23a-CTRL075.ps1"
)) {
    Copy-Item (Join-Path $here $name) (Join-Path $dest $name) -Force
}

Write-Host "Wave 2B.2.3a CTRL-075 hotfix installed."
Write-Host "Next:"
Write-Host "  cd $EMSPath"
Write-Host "  .\scripts\Apply-Wave2B23a-CTRL075-Hotfix.ps1"
Write-Host "  .\scripts\Test-Wave2B23a-CTRL075-Hotfix.ps1"
Write-Host "  .\scripts\Rerun-Wave2B23a-CTRL075.ps1"
