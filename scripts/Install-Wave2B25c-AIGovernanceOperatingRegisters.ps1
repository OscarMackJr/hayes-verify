[CmdletBinding()]
param([string]$EMSPath="C:\temp\standars\ems")

$ErrorActionPreference="Stop"
$pkg=Split-Path -Parent $PSScriptRoot

New-Item -ItemType Directory -Path "$EMSPath\registers\ai-governance" -Force|Out-Null
New-Item -ItemType Directory -Path "$EMSPath\schemas" -Force|Out-Null

foreach($f in @(
 "ai_platform_register.schema.json",
 "ai_data_handling_assessment.schema.json",
 "ai_security_review_register.schema.json"
)){
    Copy-Item "$pkg\schemas\$f" "$EMSPath\schemas\$f" -Force
}

foreach($f in @(
 "ai_platform_register.json",
 "ai_data_handling_assessment.json",
 "ai_security_review_register.json"
)){
    $dest="$EMSPath\registers\ai-governance\$f"
    if(-not(Test-Path $dest)){
        Copy-Item "$pkg\registers\ai-governance\$f" $dest
    }
}

foreach($f in @(
 "Validate-AIGovernanceRegister.py",
 "Capture-AIGovernanceOperatingEvidence.py",
 "Promote-AIGovernanceOperatingRegisterEvidence.py",
 "Run-Wave2B25c-AIGovernanceOperatingRegisters.ps1",
 "Show-Wave2B25c-AIGovernanceOperatingRegisters.ps1"
)){
    Copy-Item "$pkg\scripts\$f" "$EMSPath\scripts\$f" -Force
}

$py=Join-Path $EMSPath ".venv\Scripts\python.exe"
if(-not(Test-Path $py)){$py="python"}
foreach($p in @(
 "Validate-AIGovernanceRegister.py",
 "Capture-AIGovernanceOperatingEvidence.py",
 "Promote-AIGovernanceOperatingRegisterEvidence.py"
)){
    & $py -m py_compile "$EMSPath\scripts\$p"
    if($LASTEXITCODE-ne 0){throw "Syntax validation failed: $p"}
}

Write-Host "Wave 2B.2.5c AI governance operating-register tooling installed." -ForegroundColor Green
