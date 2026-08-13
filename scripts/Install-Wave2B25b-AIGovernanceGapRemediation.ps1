[CmdletBinding()]
param([string]$EMSPath="C:\temp\standars\ems")

$ErrorActionPreference="Stop"
$pkg=Split-Path -Parent $PSScriptRoot

New-Item -ItemType Directory -Path "$EMSPath\scripts\collectors\higher-scope" -Force|Out-Null

Copy-Item "$pkg\registry\ai_governance_gap_remediation_spec.json" `
  "$EMSPath\registry\ai_governance_gap_remediation_spec.json" -Force

Copy-Item "$pkg\scripts\collectors\higher-scope\Collect-AIGovernanceGapEvidence.py" `
  "$EMSPath\scripts\collectors\higher-scope\Collect-AIGovernanceGapEvidence.py" -Force

foreach($n in @(
 "Build-AIGovernanceGapRemediationQueue.py",
 "Promote-AIGovernanceGapEvidence.py",
 "Run-Wave2B25b-AIGovernanceGapRemediation.ps1",
 "Show-Wave2B25b-AIGovernanceGapRemediation.ps1"
)){
    Copy-Item "$pkg\scripts\$n" "$EMSPath\scripts\$n" -Force
}

$py=Join-Path $EMSPath ".venv\Scripts\python.exe"
if(-not(Test-Path $py)){$py="python"}

foreach($p in @(
 "scripts\collectors\higher-scope\Collect-AIGovernanceGapEvidence.py",
 "scripts\Build-AIGovernanceGapRemediationQueue.py",
 "scripts\Promote-AIGovernanceGapEvidence.py"
)){
    & $py -m py_compile "$EMSPath\$p"
    if($LASTEXITCODE-ne 0){throw "Syntax validation failed: $p"}
}

Write-Host "Wave 2B.2.5b AI-governance gap remediation tooling installed." -ForegroundColor Green
