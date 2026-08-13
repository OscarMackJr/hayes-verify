[CmdletBinding()]
param([string]$EMSPath="C:\temp\standars\ems")

$c=Join-Path $EMSPath "generated\wave2\higher-scope-collectors\document-control"
$q=Join-Path $EMSPath "generated\wave2\higher-scope-collectors\document-control-qualified"

Write-Host "Collector report:" -ForegroundColor Cyan
Get-Content (Join-Path $c "collector_report.json")

Write-Host ""
Write-Host "Assertions:" -ForegroundColor Cyan
Import-Csv (Join-Path $c "assertions.csv") |
  Select-Object control_id,assertion,result,detail |
  Format-Table -Wrap -AutoSize

Write-Host ""
Write-Host "Qualification summary:" -ForegroundColor Cyan
Get-Content (Join-Path $q "qualification_summary.json")

Write-Host ""
Write-Host "Qualified controls:" -ForegroundColor Cyan
Import-Csv (Join-Path $q "qualified_document_control.csv") |
  Format-Table -Wrap -AutoSize

Write-Host ""
Write-Host "Gaps:" -ForegroundColor Cyan
Import-Csv (Join-Path $q "document_control_gaps.csv") |
  Format-Table -AutoSize
