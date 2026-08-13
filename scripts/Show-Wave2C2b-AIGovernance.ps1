[CmdletBinding()]
param([string]$EMSPath="C:\temp\standars\ems")

$out=Join-Path $EMSPath "generated\wave2c\ai-governance-promotion"
$queue=Join-Path $EMSPath "generated\wave2c\remediation_queue.csv"

Write-Host "Review record:" -ForegroundColor Cyan
Get-Content (Join-Path $out "review_record.json")

if(Test-Path (Join-Path $out "promotion_summary.json")){
    Write-Host "`nPromotion summary:" -ForegroundColor Cyan
    Get-Content (Join-Path $out "promotion_summary.json")
}

Write-Host "`nAI Governance queue rows:" -ForegroundColor Cyan
Import-Csv $queue |
    Where-Object control_id -in @("EMS-CTRL-049","EMS-CTRL-050","EMS-CTRL-053") |
    Select-Object control_id,control_name,current_status,evidence_sufficiency,promotion_status,remediation_state,next_action |
    Format-Table -Wrap -AutoSize

Write-Host "`nRemaining Wave 2C remediation controls:" -ForegroundColor Cyan
Import-Csv $queue |
    Where-Object remediation_state -eq "OPEN" |
    Select-Object control_id,control_name,scope,intake_classification,current_status,remediation_state,promotion_status |
    Format-Table -Wrap -AutoSize

if(Test-Path (Join-Path $out "validation_report.json")){
    Write-Host "`nValidation:" -ForegroundColor Cyan
    Get-Content (Join-Path $out "validation_report.json")
}
