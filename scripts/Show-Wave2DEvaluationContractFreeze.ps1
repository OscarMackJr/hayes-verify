[CmdletBinding()]
param([string]$EMSPath="C:\temp\standars\ems")
$root=(Resolve-Path $EMSPath).Path
Write-Host "Contract freeze:" -ForegroundColor Cyan
Get-Content "$root\generated\wave2d\evaluation-contract\contract_freeze.json"
Write-Host "`nValidation:" -ForegroundColor Cyan
Get-Content "$root\generated\wave2d\evaluation-contract\contract_freeze_validation.json"
Write-Host "`nStatus vocabulary:" -ForegroundColor Cyan
Get-Content "$root\registry\wave2d\evaluation_status_vocabulary.json"
