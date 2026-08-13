[CmdletBinding()]
param(
    [string]$EMSPath="C:\temp\standars\ems",
    [switch]$Freeze
)

$ErrorActionPreference="Stop"

Write-Host "=== Validate semantic-reconciliation hotfix ===" -ForegroundColor Cyan
& (Join-Path $EMSPath "scripts\Test-Wave2BCloseoutSemanticReconciliation.ps1") -EMSPath $EMSPath
if($LASTEXITCODE-ne 0){throw "Semantic-reconciliation validation failed."}

Write-Host ""
Write-Host "=== Re-run Wave 2B closeout certification ===" -ForegroundColor Cyan
& (Join-Path $EMSPath "scripts\Run-Wave2BCloseoutCertification.ps1") -EMSPath $EMSPath
if($LASTEXITCODE-ne 0){throw "Wave 2B closeout certification still failed."}

Write-Host ""
& (Join-Path $EMSPath "scripts\Show-Wave2BCloseoutCertification.ps1") -EMSPath $EMSPath

if($Freeze){
    Write-Host ""
    Write-Host "=== Certification passed; freezing Wave 2B baseline ===" -ForegroundColor Cyan
    & (Join-Path $EMSPath "scripts\Run-Wave2BCloseoutCertification.ps1") -EMSPath $EMSPath -Freeze
    if($LASTEXITCODE-ne 0){throw "Wave 2B freeze failed."}
}
else{
    Write-Host ""
    Write-Host "No freeze requested. Review corrected certification first." -ForegroundColor Yellow
}
