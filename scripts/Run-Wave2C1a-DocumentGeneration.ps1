[CmdletBinding()]
param([string]$EMSPath="C:\temp\standars\ems")
$ErrorActionPreference="Stop"
function Fail([string]$m){throw "WAVE 2C.1a BLOCKED: $m"}

$branch=(git -C $EMSPath branch --show-current).Trim()
if($branch-ne"feature/wave2c-remediation"){Fail "Expected feature/wave2c-remediation; current=$branch"}

$py=Join-Path $EMSPath ".venv\Scripts\python.exe"
if(-not(Test-Path $py)){$py="python"}

$spec=Join-Path $EMSPath "registry\wave2c1a_document_generation_spec.json"
$gen=Join-Path $EMSPath "generated\wave2c\ctrl072-generation"
$out=Join-Path $EMSPath "release\wave2c\controlled-documents"
New-Item -ItemType Directory -Path $gen -Force|Out-Null
New-Item -ItemType Directory -Path $out -Force|Out-Null

Write-Host "=== Discover controlled document sources ===" -ForegroundColor Cyan
& $py (Join-Path $EMSPath "scripts\Discover-ControlledDocumentSources.py") --ems-root $EMSPath --spec $spec --out (Join-Path $gen "source_inventory.csv")
if($LASTEXITCODE-ne 0){Fail "Controlled source discovery failed."}

Write-Host "`n=== Generate DOCX/PDF outputs ===" -ForegroundColor Cyan
& $py (Join-Path $EMSPath "scripts\Generate-ControlledDocuments.py") --ems-root $EMSPath --inventory (Join-Path $gen "source_inventory.csv") --outdir $out --manifest (Join-Path $gen "generation_manifest.json")
$generationExit=$LASTEXITCODE

Write-Host "`n=== Validate generated outputs ===" -ForegroundColor Cyan
& $py (Join-Path $EMSPath "scripts\Validate-ControlledDocumentOutputs.py") --ems-root $EMSPath --manifest (Join-Path $gen "generation_manifest.json") --report (Join-Path $gen "output_validation.json") --provenance (Join-Path $gen "provenance.csv")
$validationExit=$LASTEXITCODE

if($generationExit-ne 0 -or $validationExit-ne 0){
    Write-Host "`nGeneration pipeline remains incomplete. CTRL-072 will not be promoted." -ForegroundColor Yellow
}else{
    Write-Host "`nGeneration pipeline passed. Re-running Wave 2C.1 qualification..." -ForegroundColor Cyan
    & (Join-Path $EMSPath "scripts\Run-Wave2C1-CTRL072.ps1") -EMSPath $EMSPath
    if($LASTEXITCODE-ne 0){Fail "Wave 2C.1 requalification failed."}
}

Write-Host "`nWave 2C.1a complete. No automatic promotion performed." -ForegroundColor Green
