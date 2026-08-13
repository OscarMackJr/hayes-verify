[CmdletBinding()]
param([string]$EMSPath="C:\temp\standars\ems")

$ErrorActionPreference="Stop"
$pkg=Split-Path -Parent $PSScriptRoot

Copy-Item "$pkg\registry\higher_scope_evidence_discovery_config.json" `
  "$EMSPath\registry\higher_scope_evidence_discovery_config.json" -Force

foreach($n in @(
 "Discover-HigherScopeEvidence.py",
 "Validate-HigherScopeEvidenceCandidates.py",
 "Promote-HigherScopeEvidence.py",
 "Run-Wave2B1-EvidenceDiscovery.ps1",
 "Promote-Wave2B1-Evidence.ps1",
 "Show-Wave2B1-EvidenceDiscovery.ps1"
)){
  Copy-Item "$pkg\scripts\$n" "$EMSPath\scripts\$n" -Force
}

$py=Join-Path $EMSPath ".venv\Scripts\python.exe"
if(-not(Test-Path $py)){$py="python"}

foreach($p in @(
 "Discover-HigherScopeEvidence.py",
 "Validate-HigherScopeEvidenceCandidates.py",
 "Promote-HigherScopeEvidence.py"
)){
  & $py -m py_compile "$EMSPath\scripts\$p"
  if($LASTEXITCODE-ne 0){throw "Syntax validation failed: $p"}
}

Write-Host "Wave 2B.1 Higher-Scope Evidence Discovery tooling installed." -ForegroundColor Green
