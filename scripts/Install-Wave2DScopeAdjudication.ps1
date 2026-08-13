[CmdletBinding()]
param([string]$EMSPath="C:\temp\standars\ems")
$ErrorActionPreference="Stop"
$pkg=(Resolve-Path (Join-Path $PSScriptRoot "..")).Path

New-Item -ItemType Directory -Force -Path "$EMSPath\scripts","$EMSPath\registry","$EMSPath\schemas"|Out-Null
foreach($n in @(
    "Adjudicate-Wave2DControls.py",
    "Adjudicate-Wave2DTargets.py",
    "Finalize-Wave2DAdjudication.py",
    "Run-Wave2DScopeAdjudication.ps1",
    "Show-Wave2DScopeAdjudication.ps1",
    "Stage-Wave2DScopeAdjudication.ps1"
)){
    Copy-Item "$pkg\scripts\$n" "$EMSPath\scripts\$n" -Force
}
Copy-Item "$pkg\registry\wave2d_scope_adjudication_spec.json" "$EMSPath\registry\wave2d_scope_adjudication_spec.json" -Force
Copy-Item "$pkg\schemas\wave2d_scope_adjudication_report.schema.json" "$EMSPath\schemas\wave2d_scope_adjudication_report.schema.json" -Force
Write-Host "Wave 2D Scope Adjudication & Decision Population tooling installed." -ForegroundColor Green
