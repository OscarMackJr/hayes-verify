[CmdletBinding()]
param(
    [string]$EMSPath="C:\temp\standars\ems",
    [switch]$InstallDependencies
)

$ErrorActionPreference="Stop"
function Fail([string]$m){throw "WAVE 2C.1a BLOCKED: $m"}

$branch=(git -C $EMSPath branch --show-current).Trim()
if($branch-ne"feature/wave2c-remediation"){Fail "Expected feature/wave2c-remediation; current=$branch"}

# Runtime preflight returns selected Python and soffice.
$runtime = & (Join-Path $EMSPath "scripts\Test-Wave2C1a-Runtime.ps1") `
    -EMSPath $EMSPath `
    -InstallDependencies:$InstallDependencies

if($LASTEXITCODE-ne 0){ Fail "Runtime/dependency preflight failed." }

# Re-resolve explicitly to avoid pipeline/host output ambiguity.
$python=$null
if($env:VIRTUAL_ENV){
    $candidate=Join-Path $env:VIRTUAL_ENV "Scripts\python.exe"
    if(Test-Path $candidate){$python=$candidate}
}
if(-not $python){
    $cmd=Get-Command python -ErrorAction SilentlyContinue
    if($cmd){$python=$cmd.Source}
}
if(-not $python){Fail "Python disappeared after preflight."}

$soffice=$null
foreach($name in @("soffice","libreoffice")){
    $cmd=Get-Command $name -ErrorAction SilentlyContinue
    if($cmd){$soffice=$cmd.Source;break}
}
if(-not $soffice){
    foreach($candidate in @(
        "C:\Program Files\LibreOffice\program\soffice.exe",
        "C:\Program Files (x86)\LibreOffice\program\soffice.exe"
    )){
        if(Test-Path $candidate){$soffice=$candidate;break}
    }
}
if(-not $soffice){Fail "LibreOffice/soffice not found after preflight."}

$env:EMS_SOFFICE=$soffice

$spec=Join-Path $EMSPath "registry\wave2c1a_document_generation_spec.json"
$gen=Join-Path $EMSPath "generated\wave2c\ctrl072-generation"
$out=Join-Path $EMSPath "release\wave2c\controlled-documents"
New-Item -ItemType Directory -Path $gen -Force|Out-Null
New-Item -ItemType Directory -Path $out -Force|Out-Null

# Clean only prior generated CTRL-072 output files so counts reflect this run.
Get-ChildItem $out -File -ErrorAction SilentlyContinue |
    Where-Object {$_.Extension -in @(".docx",".pdf")} |
    Remove-Item -Force

Write-Host "=== Discover controlled document sources ===" -ForegroundColor Cyan
& $python (Join-Path $EMSPath "scripts\Discover-ControlledDocumentSources.py") `
    --ems-root $EMSPath `
    --spec $spec `
    --out (Join-Path $gen "source_inventory.csv")
if($LASTEXITCODE-ne 0){Fail "Controlled source discovery failed."}

Write-Host "`n=== Generate DOCX/PDF outputs ===" -ForegroundColor Cyan
& $python (Join-Path $EMSPath "scripts\Generate-ControlledDocuments.py") `
    --ems-root $EMSPath `
    --inventory (Join-Path $gen "source_inventory.csv") `
    --outdir $out `
    --manifest (Join-Path $gen "generation_manifest.json")

$generationExit=$LASTEXITCODE

if($generationExit-ne 0){
    Write-Host "`nGeneration failed. Validation/requalification will not run." -ForegroundColor Yellow

    $failure=[ordered]@{
        wave="2C.1a"
        control_id="EMS-CTRL-072"
        status="FAIL"
        generation_exit_code=$generationExit
        manifest_exists=Test-Path (Join-Path $gen "generation_manifest.json")
        promotion_performed=$false
    }
    $failure | ConvertTo-Json | Set-Content (Join-Path $gen "pipeline_failure.json") -Encoding UTF8

    Write-Host "CTRL-072 remains OPEN / NOT_PROMOTED." -ForegroundColor Yellow
    exit 0
}

$manifest=Join-Path $gen "generation_manifest.json"
if(-not(Test-Path $manifest)){Fail "Generator returned success but no generation_manifest.json exists."}

Write-Host "`n=== Validate generated outputs ===" -ForegroundColor Cyan
& $python (Join-Path $EMSPath "scripts\Validate-ControlledDocumentOutputs.py") `
    --ems-root $EMSPath `
    --manifest $manifest `
    --report (Join-Path $gen "output_validation.json") `
    --provenance (Join-Path $gen "provenance.csv")
if($LASTEXITCODE-ne 0){
    Write-Host "Output validation failed. CTRL-072 remains unqualified." -ForegroundColor Yellow
    exit 0
}

Write-Host "`n=== Re-run Wave 2C.1 CTRL-072 qualification ===" -ForegroundColor Cyan
& (Join-Path $EMSPath "scripts\Run-Wave2C1-CTRL072.ps1") -EMSPath $EMSPath
if($LASTEXITCODE-ne 0){Fail "Wave 2C.1 requalification failed."}

Write-Host "`nWave 2C.1a complete. No automatic promotion performed." -ForegroundColor Green
