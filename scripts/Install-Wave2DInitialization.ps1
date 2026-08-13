[CmdletBinding()]
param([string]$EMSPath="C:\temp\standars\ems")
$ErrorActionPreference="Stop"
$pkg=(Resolve-Path (Join-Path $PSScriptRoot "..")).Path

New-Item -ItemType Directory -Force -Path "$EMSPath\scripts","$EMSPath\registry","$EMSPath\schemas"|Out-Null

foreach($n in @(
    "Verify-Wave2DBaseline.py",
    "Initialize-Wave2D.py",
    "Test-Wave2DProtectedBaseline.ps1",
    "Bootstrap-Wave2D.ps1",
    "Show-Wave2DInitialization.ps1",
    "Stage-Wave2DInitialization.ps1"
)){
    Copy-Item (Join-Path $pkg "scripts\$n") (Join-Path $EMSPath "scripts\$n") -Force
}
Copy-Item (Join-Path $pkg "registry\wave2d_initialization_spec.json") (Join-Path $EMSPath "registry\wave2d_initialization_spec.json") -Force
Copy-Item (Join-Path $pkg "schemas\wave2d_initialization_record.schema.json") (Join-Path $EMSPath "schemas\wave2d_initialization_record.schema.json") -Force

Write-Host "Wave 2D Baseline Intake & Scope Initialization tooling installed." -ForegroundColor Green
