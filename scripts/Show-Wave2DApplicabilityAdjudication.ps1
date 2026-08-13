[CmdletBinding()]
param([string]$EMSPath="C:\temp\standars\ems")
$root=(Resolve-Path $EMSPath).Path

Write-Host "Applicability summary:" -ForegroundColor Cyan
Get-Content "$root\generated\wave2d\evaluation-matrix\applicability_adjudication_summary.json"

Write-Host "`nValidation:" -ForegroundColor Cyan
Get-Content "$root\generated\wave2d\evaluation-matrix\applicability_adjudication_validation.json"

Write-Host "`nREVIEW_REQUIRED rows:" -ForegroundColor Cyan
Import-Csv "$root\registry\wave2d\applicability_decisions.csv" |
    Where-Object {$_.decision -eq "REVIEW_REQUIRED"} |
    Select-Object control_id,control_name,target_id,repository_name,decision,rationale,decision_owner,decision_source |
    Format-Table -Wrap -AutoSize

Write-Host "`nDecision counts:" -ForegroundColor Cyan
Import-Csv "$root\registry\wave2d\applicability_decisions.csv" |
    Group-Object decision |
    Select-Object Name,Count |
    Format-Table -AutoSize
