[CmdletBinding()]
param(
    [string]$EMSPath="C:\temp\standars\ems",
    [switch]$Promote
)

$ErrorActionPreference="Stop"

Push-Location $EMSPath
try {
    Write-Host "=== Validate envelope-key hotfix ===" -ForegroundColor Cyan
    & ".\scripts\Test-Wave2B23a-CTRL075-EnvelopeKeyHotfix.ps1"
    if($LASTEXITCODE-ne 0){throw "Envelope-key hotfix validation failed."}

    Write-Host ""
    Write-Host "=== Rerun corrected CTRL-075 refinement ===" -ForegroundColor Cyan
    & ".\scripts\Run-Wave2B23a-CTRL075Refinement.ps1"
    if($LASTEXITCODE-ne 0){throw "CTRL-075 refinement failed."}

    Write-Host ""
    Write-Host "=== Show corrected CTRL-075 result ===" -ForegroundColor Cyan
    & ".\scripts\Show-Wave2B23a-CTRL075Refinement.ps1"

    if($Promote){
        Write-Host ""
        Write-Host "=== Promotion requested ===" -ForegroundColor Cyan
        & ".\scripts\Run-Wave2B23a-CTRL075Refinement.ps1" -Promote
        if($LASTEXITCODE-ne 0){throw "CTRL-075 promotion failed."}
    } else {
        Write-Host ""
        Write-Host "No promotion requested. Review corrected qualification first." -ForegroundColor Yellow
    }
}
finally {
    Pop-Location
}
