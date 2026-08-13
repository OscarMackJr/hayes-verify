[CmdletBinding()]
param([string]$EMSPath="C:\temp\standars\ems")

$ErrorActionPreference="Stop"
$pkg=Split-Path -Parent $PSScriptRoot

New-Item -ItemType Directory -Path "$EMSPath\scripts\collectors\higher-scope" -Force|Out-Null

Copy-Item "$pkg\registry\hs_security_data_governance_spec.json" "$EMSPath\registry\hs_security_data_governance_spec.json" -Force
Copy-Item "$pkg\registry\security_data_governance_admissibility_policy.json" "$EMSPath\registry\security_data_governance_admissibility_policy.json" -Force
Copy-Item "$pkg\scripts\collectors\higher-scope\Collect-HSSecurityDataGovernance.py" "$EMSPath\scripts\collectors\higher-scope\Collect-HSSecurityDataGovernance.py" -Force

foreach($n in @(
 "Classify-HSSecurityDataGovernanceEvidence.py",
 "Build-HSSecurityDataGovernanceMatrix.py",
 "Qualify-HSSecurityDataGovernance.py",
 "Build-HSSecurityDataGovernanceRemediation.py",
 "Promote-HSSecurityDataGovernance.py",
 "Run-Wave2B26-HSSecurityDataGovernance.ps1",
 "Show-Wave2B26-HSSecurityDataGovernance.ps1"
)){
    Copy-Item "$pkg\scripts\$n" "$EMSPath\scripts\$n" -Force
}

$py=Join-Path $EMSPath ".venv\Scripts\python.exe"
if(-not(Test-Path $py)){$py="python"}

foreach($p in @(
 "scripts\collectors\higher-scope\Collect-HSSecurityDataGovernance.py",
 "scripts\Classify-HSSecurityDataGovernanceEvidence.py",
 "scripts\Build-HSSecurityDataGovernanceMatrix.py",
 "scripts\Qualify-HSSecurityDataGovernance.py",
 "scripts\Build-HSSecurityDataGovernanceRemediation.py",
 "scripts\Promote-HSSecurityDataGovernance.py"
)){
    & $py -m py_compile "$EMSPath\$p"
    if($LASTEXITCODE-ne 0){throw "Syntax validation failed: $p"}
}

Write-Host "Wave 2B.2.6 HS-SECURITY-DATA-GOVERNANCE tooling installed." -ForegroundColor Green
