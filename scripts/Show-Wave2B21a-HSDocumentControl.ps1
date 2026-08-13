
[CmdletBinding()]
param([string]$EMSPath="C:\temp\standars\ems")

$c=Join-Path $EMSPath "generated\wave2\higher-scope-collectors\document-control"
$q=Join-Path $EMSPath "generated\wave2\higher-scope-collectors\document-control-qualified"

Write-Host "CTRL-002 assertions:" -ForegroundColor Cyan
Import-Csv (Join-Path $c "assertions.csv") |
    Where-Object control_id -eq "EMS-CTRL-002" |
    Format-Table -Wrap -AutoSize

Write-Host ""
Write-Host "Qualification summary:" -ForegroundColor Cyan
Get-Content (Join-Path $q "qualification_summary.json")

Write-Host ""
Write-Host "All seven qualification rows:" -ForegroundColor Cyan
Import-Csv (Join-Path $q "qualified_document_control.csv") |
    Select-Object control_id,control_name,status,sufficiency,promotion_eligible |
    Format-Table -AutoSize
