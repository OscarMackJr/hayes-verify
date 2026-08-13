[CmdletBinding()]
param([string]$EMSPath="C:\temp\standars\ems")

$ErrorActionPreference="Stop"
$pkg=(Resolve-Path (Join-Path $PSScriptRoot "..")).Path

New-Item -ItemType Directory -Force -Path `
    "$EMSPath\scripts","$EMSPath\registry","$EMSPath\schemas" | Out-Null

foreach($n in @(
    "Certify-Wave2CPostCloseoutBranch.py",
    "Validate-Wave2CPostCloseoutScope.py",
    "Freeze-Wave2CPostCloseoutArtifacts.py",
    "Prepare-Wave2CPostCloseoutRelease.ps1",
    "Show-Wave2CPostCloseoutRelease.ps1",
    "Prepare-Wave2CPostCloseoutPR.ps1"
)){
    Copy-Item (Join-Path $pkg "scripts\$n") (Join-Path $EMSPath "scripts\$n") -Force
}

Copy-Item `
    (Join-Path $pkg "registry\wave2c_post_closeout_release_spec.json") `
    (Join-Path $EMSPath "registry\wave2c_post_closeout_release_spec.json") `
    -Force

Copy-Item `
    (Join-Path $pkg "schemas\wave2c_post_closeout_branch_certification.schema.json") `
    (Join-Path $EMSPath "schemas\wave2c_post_closeout_branch_certification.schema.json") `
    -Force

Write-Host "Wave 2C Post-Closeout Branch Certification & Release Preparation tooling installed." -ForegroundColor Green
