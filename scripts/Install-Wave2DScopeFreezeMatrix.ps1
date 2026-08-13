[CmdletBinding()]
param([string]$EMSPath="C:\temp\standars\ems")
$ErrorActionPreference="Stop"
$pkg=(Resolve-Path (Join-Path $PSScriptRoot "..")).Path
New-Item -ItemType Directory -Force -Path "$EMSPath\scripts","$EMSPath\registry","$EMSPath\schemas"|Out-Null

foreach($n in @(
    "Freeze-Wave2DScopePopulation.py",
    "Build-Wave2DEvaluationMatrix.py",
    "Validate-Wave2DEvaluationMatrix.py",
    "Run-Wave2DScopeFreezeMatrix.ps1",
    "Show-Wave2DScopeFreezeMatrix.ps1",
    "Stage-Wave2DScopeFreezeMatrix.ps1"
)){
    Copy-Item "$pkg\scripts\$n" "$EMSPath\scripts\$n" -Force
}
Copy-Item "$pkg\registry\wave2d_scope_freeze_matrix_spec.json" "$EMSPath\registry\wave2d_scope_freeze_matrix_spec.json" -Force
Copy-Item "$pkg\schemas\wave2d_evaluation_matrix_summary.schema.json" "$EMSPath\schemas\wave2d_evaluation_matrix_summary.schema.json" -Force
Write-Host "Wave 2D Scope Freeze & Evaluation Matrix tooling installed." -ForegroundColor Green
