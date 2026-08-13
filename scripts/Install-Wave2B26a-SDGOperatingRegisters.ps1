[CmdletBinding()]
param([string]$EMSPath="C:\temp\standars\ems")

$ErrorActionPreference="Stop"
$pkg=Split-Path -Parent $PSScriptRoot

New-Item -ItemType Directory -Path "$EMSPath\registers\security-data-governance" -Force|Out-Null
New-Item -ItemType Directory -Path "$EMSPath\schemas" -Force|Out-Null

foreach($f in @(
 "data_classification_register.schema.json",
 "data_retention_register.schema.json",
 "production_data_protection_register.schema.json"
)){
 Copy-Item "$pkg\schemas\$f" "$EMSPath\schemas\$f" -Force
}

foreach($f in @(
 "data_classification_register.json",
 "data_retention_register.json",
 "production_data_protection_register.json"
)){
 $dest="$EMSPath\registers\security-data-governance\$f"
 if(-not(Test-Path $dest)){
   Copy-Item "$pkg\registers\security-data-governance\$f" $dest
 }
}

foreach($f in @(
 "Validate-SDGRegister.py",
 "Capture-SDGRegisterEvidence.py",
 "Requalify-HSSecurityDataGovernance.py",
 "Promote-HSSecurityDataGovernance-Requalified.py",
 "Run-Wave2B26a-SDGOperatingRegisters.ps1",
 "Show-Wave2B26a-SDGOperatingRegisters.ps1"
)){
 Copy-Item "$pkg\scripts\$f" "$EMSPath\scripts\$f" -Force
}

$py=Join-Path $EMSPath ".venv\Scripts\python.exe"
if(-not(Test-Path $py)){$py="python"}

foreach($p in @(
 "Validate-SDGRegister.py",
 "Capture-SDGRegisterEvidence.py",
 "Requalify-HSSecurityDataGovernance.py",
 "Promote-HSSecurityDataGovernance-Requalified.py"
)){
 & $py -m py_compile "$EMSPath\scripts\$p"
 if($LASTEXITCODE-ne 0){throw "Syntax validation failed: $p"}
}

Write-Host "Wave 2B.2.6a Security & Data Governance operating-register tooling installed." -ForegroundColor Green
