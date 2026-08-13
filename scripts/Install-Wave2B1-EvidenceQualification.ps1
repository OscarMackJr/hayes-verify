[CmdletBinding()]
param([string]$EMSPath="C:\temp\standars\ems")

$ErrorActionPreference="Stop"
$pkg=Split-Path -Parent $PSScriptRoot

Copy-Item "$pkg\registry\evidence_source_policy.json" "$EMSPath\registry\evidence_source_policy.json" -Force

foreach($n in @(
 "Classify-EvidenceSources.py",
 "Evaluate-EvidenceSufficiency.py",
 "Rebuild-HigherScopeCandidates.py",
 "Validate-EvidencePromotion.py",
 "Run-Wave2B1-EvidenceQualification.ps1",
 "Show-Wave2B1-EvidenceQualification.ps1"
)){
 Copy-Item "$pkg\scripts\$n" "$EMSPath\scripts\$n" -Force
}

$py=Join-Path $EMSPath ".venv\Scripts\python.exe"
if(-not(Test-Path $py)){$py="python"}

foreach($p in @(
 "Classify-EvidenceSources.py",
 "Evaluate-EvidenceSufficiency.py",
 "Rebuild-HigherScopeCandidates.py",
 "Validate-EvidencePromotion.py"
)){
 & $py -m py_compile "$EMSPath\scripts\$p"
 if($LASTEXITCODE-ne 0){throw "Syntax validation failed: $p"}
}

Write-Host "Wave 2B.1 Evidence Source Admissibility tooling installed." -ForegroundColor Green
