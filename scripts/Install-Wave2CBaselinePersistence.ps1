[CmdletBinding()]
param([string]$EMSPath="C:\temp\standars\ems")
$ErrorActionPreference="Stop"
$pkg=(Resolve-Path (Join-Path $PSScriptRoot "..")).Path

New-Item -ItemType Directory -Force -Path "$EMSPath\scripts","$EMSPath\registry","$EMSPath\schemas"|Out-Null

foreach($n in @(
 "Bootstrap-Wave2CBaselinePersistence.ps1",
 "Stage-Wave2CBaselinePersistence.ps1",
 "CommitPush-Wave2CBaselinePersistence.ps1",
 "Create-Wave2CBaselinePersistencePR.ps1",
 "Inspect-And-Merge-Wave2CBaselinePersistencePR.ps1",
 "Cleanup-MainAfterWave2CBaselinePersistence.ps1"
)){
    Copy-Item (Join-Path $pkg "scripts\$n") (Join-Path $EMSPath "scripts\$n") -Force
}
Copy-Item (Join-Path $pkg "registry\wave2c_baseline_persistence_spec.json") (Join-Path $EMSPath "registry\wave2c_baseline_persistence_spec.json") -Force

Write-Host "Wave 2C Baseline Registration Persistence & Main Cleanup tooling installed." -ForegroundColor Green
