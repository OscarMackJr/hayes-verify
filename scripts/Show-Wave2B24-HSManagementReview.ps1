[CmdletBinding()]param([string]$EMSPath="C:\temp\standars\ems")
$c=Join-Path $EMSPath "generated\wave2\higher-scope-collectors\management-review"
$q=Join-Path $EMSPath "generated\wave2\higher-scope-collectors\management-review-qualified"

Write-Host "Collector report:" -ForegroundColor Cyan
Get-Content (Join-Path $c "collector_report.json")

Write-Host "`nAssertions:" -ForegroundColor Cyan
Import-Csv (Join-Path $c "assertions.csv")|Select-Object control_id,scope,assertion,result,detail|Format-Table -Wrap -AutoSize

Write-Host "`nQualification summary:" -ForegroundColor Cyan
Get-Content (Join-Path $q "qualification_summary.json")

Write-Host "`nQualified controls:" -ForegroundColor Cyan
Import-Csv (Join-Path $q "qualified_management_review.csv")|Select-Object control_id,control_name,scope,status,sufficiency,promotion_eligible|Format-Table -AutoSize

Write-Host "`nGaps:" -ForegroundColor Cyan
Import-Csv (Join-Path $q "management_review_gaps.csv")|Format-Table -AutoSize
