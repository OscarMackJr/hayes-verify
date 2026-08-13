[CmdletBinding()]
param([string]$EMSPath="C:\temp\standars\ems")
$ErrorActionPreference="Stop"
$pkg=(Resolve-Path (Join-Path $PSScriptRoot "..")).Path
New-Item -ItemType Directory -Force -Path "$EMSPath\scripts","$EMSPath\registry","$EMSPath\schemas"|Out-Null

foreach($n in @(
    "Build-Wave2DApplicabilityRules.py",
    "Adjudicate-Wave2DApplicability.py",
    "Apply-Wave2DApplicability.py",
    "Validate-Wave2DApplicability.py",
    "Run-Wave2DApplicabilityAdjudication.ps1",
    "Show-Wave2DApplicabilityAdjudication.ps1",
    "Stage-Wave2DApplicabilityAdjudication.ps1"
)){
    Copy-Item "$pkg\scripts\$n" "$EMSPath\scripts\$n" -Force
}
Copy-Item "$pkg\registry\wave2d_applicability_adjudication_spec.json" "$EMSPath\registry\wave2d_applicability_adjudication_spec.json" -Force
Copy-Item "$pkg\schemas\wave2d_applicability_adjudication_summary.schema.json" "$EMSPath\schemas\wave2d_applicability_adjudication_summary.schema.json" -Force
Write-Host "Wave 2D Applicability Rules & Matrix Adjudication tooling installed." -ForegroundColor Green
