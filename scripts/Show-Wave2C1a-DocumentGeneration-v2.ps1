[CmdletBinding()]
param([string]$EMSPath="C:\temp\standars\ems")

$gen=Join-Path $EMSPath "generated\wave2c\ctrl072-generation"
$out=Join-Path $EMSPath "release\wave2c\controlled-documents"

Write-Host "Runtime preflight:" -ForegroundColor Cyan
if(Test-Path (Join-Path $gen "runtime_preflight.json")){
    Get-Content (Join-Path $gen "runtime_preflight.json")
}

Write-Host "`nGenerated output counts:" -ForegroundColor Cyan
[pscustomobject]@{
    DOCX = @(Get-ChildItem $out -File -Filter *.docx -ErrorAction SilentlyContinue).Count
    PDF  = @(Get-ChildItem $out -File -Filter *.pdf -ErrorAction SilentlyContinue).Count
} | Format-List

if(Test-Path (Join-Path $gen "generation_manifest.json")){
    Write-Host "Generation manifest:" -ForegroundColor Cyan
    Get-Content (Join-Path $gen "generation_manifest.json")
}

if(Test-Path (Join-Path $gen "output_validation.json")){
    Write-Host "`nOutput validation:" -ForegroundColor Cyan
    Get-Content (Join-Path $gen "output_validation.json")
}

if(Test-Path (Join-Path $gen "pipeline_failure.json")){
    Write-Host "`nPipeline failure:" -ForegroundColor Yellow
    Get-Content (Join-Path $gen "pipeline_failure.json")
}
