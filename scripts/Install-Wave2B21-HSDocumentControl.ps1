[CmdletBinding()]
param([string]$EMSPath="C:\temp\standars\ems")

$ErrorActionPreference="Stop"
$pkg=Split-Path -Parent $PSScriptRoot

New-Item -ItemType Directory -Path "$EMSPath\scripts\collectors\higher-scope" -Force | Out-Null
New-Item -ItemType Directory -Path "$EMSPath\schemas" -Force | Out-Null

Copy-Item "$pkg\registry\hs_document_control_spec.json" "$EMSPath\registry\hs_document_control_spec.json" -Force
Copy-Item "$pkg\schemas\hs_document_control_evidence_envelope.schema.json" "$EMSPath\schemas\hs_document_control_evidence_envelope.schema.json" -Force

foreach($n in @(
 "Validate-HSDocumentControlEvidence.py",
 "Qualify-HSDocumentControlEvidence.py",
 "Promote-HSDocumentControlEvidence.py",
 "Run-Wave2B21-HSDocumentControl.ps1",
 "Show-Wave2B21-HSDocumentControl.ps1"
)){
 Copy-Item "$pkg\scripts\$n" "$EMSPath\scripts\$n" -Force
}

Copy-Item "$pkg\scripts\collectors\higher-scope\Collect-HSDocumentControl.py" `
  "$EMSPath\scripts\collectors\higher-scope\Collect-HSDocumentControl.py" -Force

$py=Join-Path $EMSPath ".venv\Scripts\python.exe"
if(-not(Test-Path $py)){$py="python"}

foreach($p in @(
 "scripts\collectors\higher-scope\Collect-HSDocumentControl.py",
 "scripts\Validate-HSDocumentControlEvidence.py",
 "scripts\Qualify-HSDocumentControlEvidence.py",
 "scripts\Promote-HSDocumentControlEvidence.py"
)){
 & $py -m py_compile "$EMSPath\$p"
 if($LASTEXITCODE-ne 0){throw "Syntax validation failed: $p"}
}

Write-Host "Wave 2B.2.1 HS-DOCUMENT-CONTROL tooling installed." -ForegroundColor Green
