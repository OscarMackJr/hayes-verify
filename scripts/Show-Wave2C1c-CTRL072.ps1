[CmdletBinding()]
param([string]$EMSPath="C:\temp\standars\ems")

$out=Join-Path $EMSPath "generated\wave2c\ctrl072-promotion"
$queue=Join-Path $EMSPath "generated\wave2c\remediation_queue.csv"

Write-Host "Promotion summary:" -ForegroundColor Cyan
Get-Content (Join-Path $out "promotion_summary.json")

Write-Host "`nPromotion record:" -ForegroundColor Cyan
Get-Content (Join-Path $out "promotion_record.json")

Write-Host "`nCTRL-072 queue row:" -ForegroundColor Cyan
Import-Csv $queue |
    Where-Object control_id -eq "EMS-CTRL-072" |
    Format-List

Write-Host "`nRemaining Wave 2C remediation controls:" -ForegroundColor Cyan
Import-Csv $queue |
    Where-Object remediation_state -eq "OPEN" |
    Select-Object control_id,control_name,scope,intake_classification,current_status,remediation_state,promotion_status |
    Format-Table -Wrap -AutoSize

Write-Host "`nValidation:" -ForegroundColor Cyan
Get-Content (Join-Path $out "validation_report.json")
