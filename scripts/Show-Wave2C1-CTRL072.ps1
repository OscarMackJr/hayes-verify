[CmdletBinding()]
param([string]$EMSPath="C:\temp\standars\ems")
$out=Join-Path $EMSPath "generated\wave2c\ctrl072"
Write-Host "Qualification summary:" -ForegroundColor Cyan
Get-Content (Join-Path $out "qualification_summary.json")
Write-Host "`nAssertions:" -ForegroundColor Cyan
Import-Csv (Join-Path $out "assertions.csv")|Format-Table -Wrap -AutoSize
Write-Host "`nQualified queue row:" -ForegroundColor Cyan
Import-Csv (Join-Path $out "remediation_queue.qualified.csv")|Where-Object control_id -eq "EMS-CTRL-072"|Format-List
Write-Host "`nValidation:" -ForegroundColor Cyan
Get-Content (Join-Path $out "validation_report.json")
