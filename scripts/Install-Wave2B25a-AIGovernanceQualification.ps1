[CmdletBinding()]
param([string]$EMSPath="C:\temp\standars\ems")

$ErrorActionPreference="Stop"
$pkg=Split-Path -Parent $PSScriptRoot

foreach($n in @(
 "Classify-AIGovernanceEvidence.py",
 "Build-AIGovernanceAssertionEvidenceMatrix.py",
 "Write-AIGovernanceRejectedSources.py",
 "Qualify-AIGovernanceOperatingEvidence.py",
 "Promote-AIGovernanceOperatingEvidence.py",
 "Run-Wave2B25a-AIGovernanceQualification.ps1",
 "Show-Wave2B25a-AIGovernanceQualification.ps1"
)){
    Copy-Item "$pkg\scripts\$n" "$EMSPath\scripts\$n" -Force
}

Copy-Item "$pkg\registry\ai_governance_evidence_admissibility_policy.json" `
  "$EMSPath\registry\ai_governance_evidence_admissibility_policy.json" -Force

$py=Join-Path $EMSPath ".venv\Scripts\python.exe"
if(-not(Test-Path $py)){$py="python"}

foreach($p in @(
 "Classify-AIGovernanceEvidence.py",
 "Build-AIGovernanceAssertionEvidenceMatrix.py",
 "Write-AIGovernanceRejectedSources.py",
 "Qualify-AIGovernanceOperatingEvidence.py",
 "Promote-AIGovernanceOperatingEvidence.py"
)){
    & $py -m py_compile "$EMSPath\scripts\$p"
    if($LASTEXITCODE-ne 0){throw "Syntax validation failed: $p"}
}

Write-Host "Wave 2B.2.5a AI-governance qualification tooling installed." -ForegroundColor Green
