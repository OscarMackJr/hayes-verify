[CmdletBinding()]
param([string]$EMSPath="C:\temp\standars\ems")

$ErrorActionPreference="Stop"
$pkg=Split-Path -Parent $PSScriptRoot

foreach($d in @(
    (Join-Path $EMSPath "registry"),
    (Join-Path $EMSPath "schemas"),
    (Join-Path $EMSPath "scripts"),
    (Join-Path $EMSPath "evidence\organization"),
    (Join-Path $EMSPath "evidence\ems")
)){
    New-Item -ItemType Directory -Path $d -Force | Out-Null
}

Copy-Item "$pkg\registry\evidence_authority_registry.yaml" "$EMSPath\registry\evidence_authority_registry.yaml" -Force
Copy-Item "$pkg\registry\inheritance_policy.yaml" "$EMSPath\registry\inheritance_policy.yaml" -Force
Copy-Item "$pkg\schemas\higher_scope_evidence.schema.json" "$EMSPath\schemas\higher_scope_evidence.schema.json" -Force
Copy-Item "$pkg\evidence\organization\README.md" "$EMSPath\evidence\organization\README.md" -Force
Copy-Item "$pkg\evidence\ems\README.md" "$EMSPath\evidence\ems\README.md" -Force

foreach($n in @(
    "Seed-HigherScopeEvidence.py",
    "Evaluate-HigherScopeControls.py",
    "Resolve-InheritedCompliance.py",
    "Validate-Inheritance.py",
    "Run-Wave2B1-Inheritance.ps1"
)){
    Copy-Item "$pkg\scripts\$n" "$EMSPath\scripts\$n" -Force
}

$py=Join-Path $EMSPath ".venv\Scripts\python.exe"
if(-not(Test-Path $py)){$py="python"}

foreach($p in @(
    "Seed-HigherScopeEvidence.py",
    "Evaluate-HigherScopeControls.py",
    "Resolve-InheritedCompliance.py",
    "Validate-Inheritance.py"
)){
    & $py -m py_compile "$EMSPath\scripts\$p"
    if($LASTEXITCODE-ne 0){throw "Syntax validation failed: $p"}
}

Write-Host "Wave 2B.1 EMS + Organization Inheritance tooling installed." -ForegroundColor Green
