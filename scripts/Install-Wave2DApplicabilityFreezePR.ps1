[CmdletBinding()]
param([string]$EMSPath="C:\temp\standars\ems")
$ErrorActionPreference="Stop"
$pkg=(Resolve-Path (Join-Path $PSScriptRoot "..")).Path
New-Item -ItemType Directory -Force -Path "$EMSPath\scripts","$EMSPath\registry","$EMSPath\schemas"|Out-Null

foreach($n in @(
    "Freeze-Wave2DApplicability.py",
    "Validate-Wave2DApplicabilityFreeze.py",
    "Run-Wave2DApplicabilityFreeze.ps1",
    "Stage-Wave2DDefinitionPackage.ps1",
    "Test-Wave2DDefinitionPRReadiness.ps1",
    "CommitPush-Wave2DDefinitionPackage.ps1",
    "Create-Wave2DDefinitionPR.ps1",
    "Run-Wave2DDefinitionCommitPushPR.ps1"
)){
    Copy-Item "$pkg\scripts\$n" "$EMSPath\scripts\$n" -Force
}
Copy-Item "$pkg\registry\wave2d_applicability_freeze_pr_spec.json" "$EMSPath\registry\wave2d_applicability_freeze_pr_spec.json" -Force
Copy-Item "$pkg\schemas\wave2d_applicability_freeze.schema.json" "$EMSPath\schemas\wave2d_applicability_freeze.schema.json" -Force
Write-Host "Wave 2D Applicability Freeze / Commit / PR tooling installed." -ForegroundColor Green
