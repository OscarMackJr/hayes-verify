[CmdletBinding()]
param([string]$EMSPath="C:\temp\standars\ems")

$higher=Join-Path $EMSPath "generated\wave2\inheritance\higher_scope_results.json"
$impact=Join-Path $EMSPath "generated\wave2\inheritance\inheritance_impact_report.json"

Write-Host "Higher-scope results:" -ForegroundColor Cyan
Get-Content $higher

Write-Host "`nInheritance impact:" -ForegroundColor Cyan
Get-Content $impact
