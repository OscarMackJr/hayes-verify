[CmdletBinding()]param([string]$EMSPath="C:\temp\standars\ems")
$c=Join-Path $EMSPath "generated\wave2\higher-scope-collectors\continuous-compliance"
$q=Join-Path $EMSPath "generated\wave2\higher-scope-collectors\continuous-compliance-qualified"
Write-Host "Collector report:" -ForegroundColor Cyan
Get-Content (Join-Path $c "collector_report.json")
Write-Host "`nAssertions:" -ForegroundColor Cyan
Import-Csv (Join-Path $c "assertions.csv")|Select-Object control_id,assertion,result,detail|Format-Table -Wrap -AutoSize
Write-Host "`nQualification summary:" -ForegroundColor Cyan
Get-Content (Join-Path $q "qualification_summary.json")
Write-Host "`nQualified controls:" -ForegroundColor Cyan
Import-Csv (Join-Path $q "qualified_continuous_compliance.csv")|Select-Object control_id,control_name,status,sufficiency,promotion_eligible|Format-Table -AutoSize
Write-Host "`nGaps:" -ForegroundColor Cyan
Import-Csv (Join-Path $q "continuous_compliance_gaps.csv")|Format-Table -AutoSize
Write-Host "`nCTRL-072 remediation:" -ForegroundColor Cyan
Import-Csv (Join-Path $EMSPath "generated\wave2\higher-scope-remediation.csv")|Where-Object control_id -eq "EMS-CTRL-072"|Format-List
