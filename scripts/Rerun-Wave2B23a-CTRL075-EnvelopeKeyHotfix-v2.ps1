[CmdletBinding()]
param([string]$EMSPath="C:\temp\standars\ems",[switch]$Promote)

$ErrorActionPreference="Stop"
Push-Location $EMSPath
try {
    & ".\scripts\Test-Wave2B23a-CTRL075-EnvelopeKeyHotfix-v2.ps1"
    if($LASTEXITCODE-ne 0){throw "Status-contract validation failed."}

    & ".\scripts\Run-Wave2B23a-CTRL075Refinement.ps1"
    if($LASTEXITCODE-ne 0){throw "CTRL-075 refinement failed."}

    & ".\scripts\Show-Wave2B23a-CTRL075Refinement.ps1"

    if($Promote){
        & ".\scripts\Run-Wave2B23a-CTRL075Refinement.ps1" -Promote
        if($LASTEXITCODE-ne 0){throw "CTRL-075 promotion failed."}
    } else {
        Write-Host "No promotion requested. Review corrected CTRL-075 result first." -ForegroundColor Yellow
    }
}
finally { Pop-Location }
