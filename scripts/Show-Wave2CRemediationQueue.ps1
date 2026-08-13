[CmdletBinding()]
param([string]$EMSPath="C:\temp\standars\ems")
$out=Join-Path $EMSPath "generated\wave2c"
Write-Host "Wave 2C initialization:" -ForegroundColor Cyan;Get-Content (Join-Path $out "wave2c_initialization.json")
Write-Host "`nRemediation summary:" -ForegroundColor Cyan;Get-Content (Join-Path $out "remediation_summary.json")
Write-Host "`nRemediation queue:" -ForegroundColor Cyan
Import-Csv (Join-Path $out "remediation_queue.csv")|Select control_id,control_name,scope,intake_classification,owner_role,current_status,remediation_state,promotion_eligible|Format-Table -Wrap -AutoSize
Write-Host "`nEvidence requirements:" -ForegroundColor Cyan
Import-Csv (Join-Path $out "evidence_requirements.csv")|Select control_id,control_name,intake_classification,required_evidence,promotion_mode|Format-Table -Wrap -AutoSize
Write-Host "`nValidation:" -ForegroundColor Cyan;Get-Content (Join-Path $out "validation_report.json")
