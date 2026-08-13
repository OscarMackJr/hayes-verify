[CmdletBinding()]
param([string]$EMSPath="C:\temp\standars\ems")
$dir=Join-Path $EMSPath "generated\wave2\control-definition-recovery"

Write-Host "Recovery summary:" -ForegroundColor Cyan
Get-Content (Join-Path $dir "recovery_summary.json")

Write-Host ""
Write-Host "Recovered definitions:" -ForegroundColor Cyan
Import-Csv (Join-Path $dir "recovered_control_definitions.csv") |
 Select-Object control_id,recovered_name,confidence,auto_apply,source_file |
 Format-Table -Wrap -AutoSize

Write-Host ""
Write-Host "Unresolved definitions:" -ForegroundColor Cyan
Import-Csv (Join-Path $dir "unresolved_control_definitions.csv") |
 Format-Table -Wrap -AutoSize
