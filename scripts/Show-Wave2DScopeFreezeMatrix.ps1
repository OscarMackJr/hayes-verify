[CmdletBinding()]
param([string]$EMSPath="C:\temp\standars\ems")
$root=(Resolve-Path $EMSPath).Path

Write-Host "Scope freeze:" -ForegroundColor Cyan
Get-Content "$root\generated\wave2d\scope-freeze\scope_freeze.json"

Write-Host "`nPopulation freeze:" -ForegroundColor Cyan
Get-Content "$root\generated\wave2d\scope-freeze\population_freeze.json"

Write-Host "`nEvaluation matrix summary:" -ForegroundColor Cyan
Get-Content "$root\generated\wave2d\evaluation-matrix\evaluation_matrix_summary.json"

Write-Host "`nMatrix validation:" -ForegroundColor Cyan
Get-Content "$root\generated\wave2d\evaluation-matrix\evaluation_matrix_validation.json"

Write-Host "`nApplicability-state counts:" -ForegroundColor Cyan
Import-Csv "$root\generated\wave2d\evaluation-matrix\evaluation_matrix.csv" |
    Group-Object applicability_state |
    Select-Object Name,Count |
    Format-Table -AutoSize

Write-Host "`nSample matrix rows:" -ForegroundColor Cyan
Import-Csv "$root\generated\wave2d\evaluation-matrix\evaluation_matrix.csv" |
    Select-Object -First 20 control_id,control_name,target_id,repository_name,applicability_state,evaluation_state,result_state |
    Format-Table -Wrap -AutoSize
