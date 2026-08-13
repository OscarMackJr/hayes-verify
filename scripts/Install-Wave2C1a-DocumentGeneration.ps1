[CmdletBinding()]
param([string]$EMSPath="C:\temp\standars\ems")
$ErrorActionPreference="Stop"
$here=Split-Path -Parent $MyInvocation.MyCommand.Path
$pkg=Split-Path -Parent $here

Copy-Item "$pkg\registry\wave2c1a_document_generation_spec.json" "$EMSPath\registry\wave2c1a_document_generation_spec.json" -Force
Copy-Item "$pkg\schemas\wave2c1a_generation_manifest.schema.json" "$EMSPath\schemas\wave2c1a_generation_manifest.schema.json" -Force

foreach($n in @(
 "Discover-ControlledDocumentSources.py",
 "Generate-ControlledDocuments.py",
 "Validate-ControlledDocumentOutputs.py",
 "Run-Wave2C1a-DocumentGeneration.ps1",
 "Show-Wave2C1a-DocumentGeneration.ps1"
)){
 Copy-Item (Join-Path $here $n) (Join-Path $EMSPath "scripts\$n") -Force
}

$py=Join-Path $EMSPath ".venv\Scripts\python.exe"
if(-not(Test-Path $py)){$py="python"}
foreach($n in @("Discover-ControlledDocumentSources.py","Generate-ControlledDocuments.py","Validate-ControlledDocumentOutputs.py")){
 & $py -m py_compile (Join-Path $EMSPath "scripts\$n")
 if($LASTEXITCODE-ne 0){throw "Python syntax validation failed: $n"}
}

Write-Host "Wave 2C.1a Controlled Document Generation tooling installed." -ForegroundColor Green
