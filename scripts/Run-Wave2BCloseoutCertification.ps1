[CmdletBinding()]
param(
    [string]$EMSPath="C:\temp\standars\ems",
    [switch]$Freeze
)

$ErrorActionPreference="Stop"
$py=Join-Path $EMSPath ".venv\Scripts\python.exe"
if(-not(Test-Path $py)){$py="python"}

$out=Join-Path $EMSPath "generated\wave2\closeout-certification"
New-Item -ItemType Directory -Path $out -Force|Out-Null

Write-Host "=== Wave 2B scope / higher-scope certification ===" -ForegroundColor Cyan
& $py (Join-Path $EMSPath "scripts\Certify-Wave2B.py") `
  --ems-root $EMSPath `
  --outdir $out
if($LASTEXITCODE-ne 0){
    throw "Wave 2B certification failed. Review generated\wave2\closeout-certification."
}

Write-Host ""
Write-Host "Certification passed." -ForegroundColor Green

if($Freeze){
    Write-Host ""
    Write-Host "=== Freeze Wave 2B branch-ready baseline ===" -ForegroundColor Cyan
    $freezeOut=Join-Path $EMSPath "release\wave2b-closeout"
    New-Item -ItemType Directory -Path $freezeOut -Force|Out-Null

    & $py (Join-Path $EMSPath "scripts\Freeze-Wave2BArtifacts.py") `
      --ems-root $EMSPath `
      --certdir $out `
      --outdir $freezeOut

    if($LASTEXITCODE-ne 0){throw "Wave 2B freeze failed."}
}
else{
    Write-Host ""
    Write-Host "Freeze not requested. Review certification before using -Freeze." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Wave 2B Closeout & Certification complete." -ForegroundColor Green
