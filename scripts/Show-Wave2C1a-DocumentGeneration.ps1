[CmdletBinding()]
param([string]$EMSPath="C:\temp\standars\ems")
$gen=Join-Path $EMSPath "generated\wave2c\ctrl072-generation"
Write-Host "Source inventory:" -ForegroundColor Cyan
Import-Csv (Join-Path $gen "source_inventory.csv")|Format-Table -Wrap -AutoSize
Write-Host "`nGeneration manifest:" -ForegroundColor Cyan
Get-Content (Join-Path $gen "generation_manifest.json")
Write-Host "`nOutput validation:" -ForegroundColor Cyan
Get-Content (Join-Path $gen "output_validation.json")
Write-Host "`nProvenance:" -ForegroundColor Cyan
Import-Csv (Join-Path $gen "provenance.csv")|Format-Table -Wrap -AutoSize
