[CmdletBinding()]
param([string]$EMSPath="C:\temp\standars\ems")

$ErrorActionPreference="Stop"
$pkg=(Resolve-Path (Join-Path $PSScriptRoot "..")).Path

New-Item -ItemType Directory -Force -Path `
    "$EMSPath\scripts","$EMSPath\registry","$EMSPath\schemas" | Out-Null

foreach($n in @(
    "Register-Wave2CBaseline.py",
    "Archive-Wave2CRelease.ps1",
    "Run-Wave2CPostReleaseBaselineRegistration.ps1",
    "Show-Wave2CPostReleaseBaseline.ps1"
)){
    Copy-Item (Join-Path $pkg "scripts\$n") (Join-Path $EMSPath "scripts\$n") -Force
}

Copy-Item (Join-Path $pkg "registry\wave2c_post_release_archive_spec.json") `
          (Join-Path $EMSPath "registry\wave2c_post_release_archive_spec.json") -Force

Copy-Item (Join-Path $pkg "schemas\wave2c_baseline_registration.schema.json") `
          (Join-Path $EMSPath "schemas\wave2c_baseline_registration.schema.json") -Force

Write-Host "Wave 2C Post-Release Archive & Baseline Registration tooling installed." -ForegroundColor Green
