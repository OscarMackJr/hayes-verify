
[CmdletBinding()]
param(
    [string]$EMSPath="C:\temp\standars\ems",
    [switch]$Promote
)

$ErrorActionPreference="Stop"

& (Join-Path $EMSPath "scripts\Run-Wave2B21-HSDocumentControl.ps1") -EMSPath $EMSPath
if($LASTEXITCODE-ne 0){
    throw "Corrected HS-DOCUMENT-CONTROL run failed."
}

$qPath=Join-Path $EMSPath "generated\wave2\higher-scope-collectors\document-control-qualified\qualified_document_control.csv"
$q=Import-Csv $qPath

Write-Host ""
Write-Host "Corrected CTRL-002 result:" -ForegroundColor Cyan
$q |
    Where-Object control_id -eq "EMS-CTRL-002" |
    Select-Object control_id,control_name,status,sufficiency,promotion_eligible |
    Format-Table -AutoSize

if($Promote){
    $ineligible=@($q | Where-Object { $_.promotion_eligible -ne "True" })

    if($ineligible.Count -gt 0){
        Write-Host ""
        Write-Host "Promotion blocked; ineligible controls remain:" -ForegroundColor Yellow
        $ineligible |
            Select-Object control_id,control_name,status,sufficiency,promotion_eligible |
            Format-Table -AutoSize
        throw "All seven document-control controls must be eligible before reference-family promotion."
    }

    Write-Host ""
    Write-Host "All seven controls eligible; promoting and rerunning inheritance..." -ForegroundColor Green

    & (Join-Path $EMSPath "scripts\Run-Wave2B21-HSDocumentControl.ps1") -EMSPath $EMSPath -Promote
    if($LASTEXITCODE-ne 0){
        throw "Promotion/inheritance rerun failed."
    }
}
else {
    Write-Host ""
    Write-Host "No promotion performed. Review corrected assertions first." -ForegroundColor Yellow
}
