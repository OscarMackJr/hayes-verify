[CmdletBinding()]
param([string]$EMSPath="C:\temp\standars\ems")
$root=(Resolve-Path $EMSPath).Path
Write-Host "Scope/population summary:" -ForegroundColor Cyan
Get-Content "$root\generated\wave2d\scope-definition\scope_population_summary.json"
Write-Host "`nControl decisions:" -ForegroundColor Cyan
Import-Csv "$root\registry\wave2d\control_scope_decisions.csv"|Select control_id,control_name,decision,rationale,decision_owner|Format-Table -Wrap -AutoSize
Write-Host "`nTarget decisions:" -ForegroundColor Cyan
Import-Csv "$root\registry\wave2d\evaluation_target_decisions.csv"|Select target_id,repository_name,decision,rationale,decision_owner|Format-Table -Wrap -AutoSize
