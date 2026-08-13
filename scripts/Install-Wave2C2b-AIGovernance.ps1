[CmdletBinding()]
param([string]$EMSPath="C:\temp\standars\ems")

$ErrorActionPreference="Stop"
$pkg=(Resolve-Path (Join-Path $PSScriptRoot "..")).Path
New-Item -ItemType Directory -Force -Path "$EMSPath\scripts","$EMSPath\registry","$EMSPath\schemas" | Out-Null

foreach($n in @(
    "Review-Wave2C2b-AIGovernance.py",
    "Promote-Wave2C2b-AIGovernance.py",
    "Validate-Wave2C2b-AIGovernance.py",
    "Run-Wave2C2b-AIGovernance.ps1",
    "Show-Wave2C2b-AIGovernance.ps1"
)){
    Copy-Item (Join-Path $pkg "scripts\$n") (Join-Path $EMSPath "scripts\$n") -Force
}

Copy-Item (Join-Path $pkg "registry\wave2c2b_ai_governance_promotion_spec.json") (Join-Path $EMSPath "registry\wave2c2b_ai_governance_promotion_spec.json") -Force
Copy-Item (Join-Path $pkg "schemas\wave2c2b_ai_governance_promotion_record.schema.json") (Join-Path $EMSPath "schemas\wave2c2b_ai_governance_promotion_record.schema.json") -Force

Write-Host "Wave 2C.2b AI Governance Review & Explicit Promotion tooling installed." -ForegroundColor Green
