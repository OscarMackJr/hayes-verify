[CmdletBinding()]
param([string]$HayesPath="C:\temp\standars\hayes-verify")
$ErrorActionPreference="Stop"
$pkg=(Resolve-Path (Join-Path $PSScriptRoot "..")).Path

New-Item -ItemType Directory -Force -Path `
  "$HayesPath\src\hayes_verify\pilots", `
  "$HayesPath\tests", `
  "$HayesPath\scripts", `
  "$HayesPath\registry", `
  "$HayesPath\schemas" | Out-Null

Copy-Item "$pkg\templates\src\hayes_verify\pilots\*" "$HayesPath\src\hayes_verify\pilots\" -Force
Copy-Item "$pkg\templates\tests\*" "$HayesPath\tests\" -Force
Copy-Item "$pkg\scripts\*" "$HayesPath\scripts\" -Force
Copy-Item "$pkg\registry\hayes_verify_pilot_evaluator_spec.json" "$HayesPath\registry\hayes_verify_pilot_evaluator_spec.json" -Force
Copy-Item "$pkg\schemas\hayes_verify_pilot_summary.schema.json" "$HayesPath\schemas\hayes_verify_pilot_summary.schema.json" -Force

Write-Host "Hayes Verify Pilot Evaluator Vertical Slice tooling installed." -ForegroundColor Green
