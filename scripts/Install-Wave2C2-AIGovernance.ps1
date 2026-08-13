param([string]$EMSPath="C:\temp\standars\ems");$ErrorActionPreference="Stop";$pkg=(Resolve-Path (Join-Path $PSScriptRoot "..")).Path
New-Item -ItemType Directory -Force "$EMSPath\scripts","$EMSPath\registry"|Out-Null
Get-ChildItem "$pkg\scripts" -File|?{$_.Name -ne "Install-Wave2C2-AIGovernance.ps1"}|%{Copy-Item $_.FullName "$EMSPath\scripts\$($_.Name)" -Force}
Copy-Item "$pkg\registry\wave2c2_ai_governance_spec.json" "$EMSPath\registry\wave2c2_ai_governance_spec.json" -Force
Write-Host "Wave 2C.2 Organization Evidence Framework & AI Governance Intake tooling installed."