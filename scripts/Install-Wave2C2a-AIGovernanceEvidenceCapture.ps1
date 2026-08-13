[CmdletBinding()]
param([string]$EMSPath="C:\temp\standars\ems")
$ErrorActionPreference="Stop"
$pkg=(Resolve-Path (Join-Path $PSScriptRoot "..")).Path
New-Item -ItemType Directory -Force -Path "$EMSPath\scripts","$EMSPath\registry" | Out-Null
foreach($n in @(
"Validate-Wave2C2a-AIGovernanceRegisters.py",
"Add-AIPlatformRecord.ps1",
"Add-PromptDataClassificationRecord.ps1",
"Add-AISecurityReviewRecord.ps1",
"Run-Wave2C2a-AIGovernanceEvidenceCapture.ps1",
"Show-Wave2C2a-AIGovernanceEvidenceCapture.ps1"
)){
    Copy-Item (Join-Path $pkg "scripts\$n") (Join-Path $EMSPath "scripts\$n") -Force
}
Copy-Item (Join-Path $pkg "registry\wave2c2a_ai_governance_capture_spec.json") (Join-Path $EMSPath "registry\wave2c2a_ai_governance_capture_spec.json") -Force
Write-Host "Wave 2C.2a AI Governance Operating Register Population & Evidence Capture tooling installed."
