[CmdletBinding()]
param([string]$EMSPath="C:\temp\standars\ems")

$ErrorActionPreference="Stop"
$pkg=(Resolve-Path (Join-Path $PSScriptRoot "..")).Path

New-Item -ItemType Directory -Force -Path "$EMSPath\scripts","$EMSPath\registry","$EMSPath\schemas"|Out-Null

foreach($n in @(
    "Certify-Wave2CPostMerge.py",
    "Freeze-Wave2CPostMergeRelease.py",
    "Run-Wave2CPostMergeRelease.ps1",
    "Publish-Wave2CPostMergeTag.ps1",
    "Show-Wave2CPostMergeRelease.ps1"
)){
    Copy-Item (Join-Path $pkg "scripts\$n") (Join-Path $EMSPath "scripts\$n") -Force
}

Copy-Item (Join-Path $pkg "registry\wave2c_post_merge_release_spec.json") `
          (Join-Path $EMSPath "registry\wave2c_post_merge_release_spec.json") -Force

Copy-Item (Join-Path $pkg "schemas\wave2c_post_merge_certification.schema.json") `
          (Join-Path $EMSPath "schemas\wave2c_post_merge_certification.schema.json") -Force

Write-Host "Wave 2C Post-Merge Release & Tag Certification tooling installed." -ForegroundColor Green
