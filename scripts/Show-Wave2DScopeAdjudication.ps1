[CmdletBinding()]
param([string]$EMSPath="C:\temp\standars\ems")
$root=(Resolve-Path $EMSPath).Path

Write-Host "Adjudication report:" -ForegroundColor Cyan
Get-Content "$root\generated\wave2d\scope-definition\adjudication_report.json"

Write-Host "`nControls requiring review:" -ForegroundColor Cyan
Import-Csv "$root\registry\wave2d\control_scope_decisions.csv" |
  Where-Object {$_.decision -in @("REVIEW_REQUIRED","UNDECIDED")} |
  Select-Object control_id,control_name,catalog_scope,decision,rationale,decision_owner |
  Format-Table -Wrap -AutoSize

Write-Host "`nTargets requiring review:" -ForegroundColor Cyan
Import-Csv "$root\registry\wave2d\evaluation_target_decisions.csv" |
  Where-Object {$_.decision -in @("REVIEW_REQUIRED","UNDECIDED")} |
  Select-Object target_id,repository_name,decision,rationale,decision_owner |
  Format-Table -Wrap -AutoSize

Write-Host "`nDecision counts:" -ForegroundColor Cyan
Import-Csv "$root\registry\wave2d\control_scope_decisions.csv" | Group-Object decision | Select Name,Count | Format-Table -AutoSize
Import-Csv "$root\registry\wave2d\evaluation_target_decisions.csv" | Group-Object decision | Select Name,Count | Format-Table -AutoSize
