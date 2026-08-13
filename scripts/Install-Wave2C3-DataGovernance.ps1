[CmdletBinding()]
param([string]$EMSPath="C:\temp\standars\ems")

$ErrorActionPreference="Stop"
$pkg=(Resolve-Path (Join-Path $PSScriptRoot "..")).Path
New-Item -ItemType Directory -Force -Path "$EMSPath\scripts","$EMSPath\registry","$EMSPath\schemas"|Out-Null

foreach($n in @(
"Initialize-Wave2C3DataGovernanceRegisters.py",
"Validate-Wave2C3DataGovernanceRegisters.py",
"Qualify-Wave2C3DataGovernance.py",
"Run-Wave2C3-DataGovernance.ps1",
"Show-Wave2C3-DataGovernance.ps1",
"Add-DataClassificationRecord.ps1",
"Add-DataRetentionRecord.ps1",
"Add-ProductionDataProtectionRecord.ps1"
)){
    Copy-Item (Join-Path $pkg "scripts\$n") (Join-Path $EMSPath "scripts\$n") -Force
}
Copy-Item (Join-Path $pkg "registry\wave2c3_data_governance_spec.json") (Join-Path $EMSPath "registry\wave2c3_data_governance_spec.json") -Force
Copy-Item (Join-Path $pkg "schemas\wave2c3_qualification_summary.schema.json") (Join-Path $EMSPath "schemas\wave2c3_qualification_summary.schema.json") -Force

Write-Host "Wave 2C.3 Data Governance Operating Registers & Qualification tooling installed."
