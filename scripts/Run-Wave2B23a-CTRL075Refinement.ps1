[CmdletBinding()]
param(
    [string]$EMSPath="C:\temp\standars\ems",
    [switch]$Promote
)

$ErrorActionPreference="Stop"

Write-Host "Running corrected Wave 2B.2.3 collector..." -ForegroundColor Cyan

& (Join-Path $EMSPath "scripts\Run-Wave2B23-HSContinuousCompliance.ps1") -EMSPath $EMSPath
if($LASTEXITCODE-ne 0){
    throw "Corrected Wave 2B.2.3 run failed."
}

$q=Import-Csv (Join-Path $EMSPath "generated\wave2\higher-scope-collectors\continuous-compliance-qualified\qualified_continuous_compliance.csv")

Write-Host ""
Write-Host "Corrected CTRL-075 result:" -ForegroundColor Cyan
$q |
    Where-Object control_id -eq "EMS-CTRL-075" |
    Select-Object control_id,control_name,status,sufficiency,promotion_eligible |
    Format-Table -AutoSize

if($Promote){
    $ctrl075=$q|Where-Object control_id -eq "EMS-CTRL-075"

    if(-not $ctrl075 -or $ctrl075.promotion_eligible -ne "True"){
        throw "CTRL-075 is not promotion eligible after refinement."
    }

    Write-Host ""
    Write-Host "CTRL-075 eligible; promoting eligible continuous-compliance evidence..." -ForegroundColor Green

    & (Join-Path $EMSPath "scripts\Run-Wave2B23-HSContinuousCompliance.ps1") -EMSPath $EMSPath -Promote
    if($LASTEXITCODE-ne 0){
        throw "Promotion/inheritance rerun failed."
    }
}
else {
    Write-Host ""
    Write-Host "No promotion performed. Review corrected CTRL-075 assertions first." -ForegroundColor Yellow
}
