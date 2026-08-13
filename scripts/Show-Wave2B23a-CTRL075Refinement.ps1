[CmdletBinding()]
param([string]$EMSPath="C:\temp\standars\ems")

$c=Join-Path $EMSPath "generated\wave2\higher-scope-collectors\continuous-compliance"
$q=Join-Path $EMSPath "generated\wave2\higher-scope-collectors\continuous-compliance-qualified"

Write-Host "CTRL-075 assertions:" -ForegroundColor Cyan
Import-Csv (Join-Path $c "assertions.csv") |
    Where-Object control_id -eq "EMS-CTRL-075" |
    Format-Table -Wrap -AutoSize

Write-Host ""
Write-Host "CTRL-075 qualification:" -ForegroundColor Cyan
Import-Csv (Join-Path $q "qualified_continuous_compliance.csv") |
    Where-Object control_id -eq "EMS-CTRL-075" |
    Select-Object control_id,control_name,status,sufficiency,promotion_eligible |
    Format-Table -AutoSize

Write-Host ""
Write-Host "Current inheritance impact:" -ForegroundColor Cyan
$impact=Join-Path $EMSPath "generated\wave2\inheritance\inheritance_impact_report.json"
if(Test-Path $impact){Get-Content $impact}
