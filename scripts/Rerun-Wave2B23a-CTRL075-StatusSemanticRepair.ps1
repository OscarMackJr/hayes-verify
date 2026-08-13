[CmdletBinding()]
param(
    [string]$EMSPath="C:\temp\standars\ems",
    [switch]$Promote
)

$ErrorActionPreference="Stop"
Push-Location $EMSPath
try {
    Write-Host "=== Validate semantic status repair ===" -ForegroundColor Cyan
    & ".\scripts\Test-Wave2B23a-CTRL075-StatusSemanticRepair.ps1"
    if($LASTEXITCODE-ne 0){throw "Status semantic validation failed."}

    Write-Host ""
    Write-Host "=== Rerun CTRL-075 refinement ===" -ForegroundColor Cyan
    & ".\scripts\Run-Wave2B23a-CTRL075Refinement.ps1"
    if($LASTEXITCODE-ne 0){throw "CTRL-075 refinement failed."}

    Write-Host ""
    Write-Host "=== Show CTRL-075 corrected result ===" -ForegroundColor Cyan
    & ".\scripts\Show-Wave2B23a-CTRL075Refinement.ps1"

    if($Promote){
        Write-Host ""
        Write-Host "=== Promotion requested ===" -ForegroundColor Cyan
        & ".\scripts\Run-Wave2B23a-CTRL075Refinement.ps1" -Promote
        if($LASTEXITCODE-ne 0){throw "CTRL-075 promotion failed."}
    }
    else {
        Write-Host ""
        Write-Host "No promotion requested. Review CTRL-075 qualification first." -ForegroundColor Yellow
    }
}
finally {
    Pop-Location
}
