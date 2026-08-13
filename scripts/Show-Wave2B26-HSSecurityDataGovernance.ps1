[CmdletBinding()]
param([string]$EMSPath="C:\temp\standars\ems")

$out=Join-Path $EMSPath "generated\wave2\higher-scope-collectors\security-data-governance"

Write-Host "Collector report:" -ForegroundColor Cyan
Get-Content (Join-Path $out "collector_report.json")

Write-Host ""
Write-Host "Qualification summary:" -ForegroundColor Cyan
Get-Content (Join-Path $out "qualification_summary.json")

Write-Host ""
Write-Host "Qualified controls:" -ForegroundColor Cyan
Import-Csv (Join-Path $out "qualified_security_data_governance.csv") |
  Format-Table -AutoSize

Write-Host ""
Write-Host "Assertion/evidence matrix:" -ForegroundColor Cyan
Import-Csv (Join-Path $out "assertion_evidence_matrix.csv") |
  Select-Object control_id,assertion,source_count,operating_evidence_count,rejected_source_count,operating_evidence_sufficient |
  Format-Table -Wrap -AutoSize

Write-Host ""
Write-Host "Evidence source classes:" -ForegroundColor Cyan
Import-Csv (Join-Path $out "evidence_source_classification.csv") |
  Group-Object source_class |
  Select-Object Name,Count |
  Format-Table -AutoSize

Write-Host ""
Write-Host "Open remediation items:" -ForegroundColor Cyan
$r=Import-Csv (Join-Path $out "remediation_queue.csv")
if($r){$r|Format-Table -Wrap -AutoSize}else{Write-Host "None."}
