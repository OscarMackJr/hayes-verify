[CmdletBinding()]
param([string]$HayesPath="C:\temp\standars\hayes-verify")
$root=(Resolve-Path $HayesPath).Path
Write-Host "Scaffold certification:" -ForegroundColor Cyan
Get-Content "$root\generated\scaffold-certification\scaffold_certification.json"
Write-Host "`nCertification validation:" -ForegroundColor Cyan
Get-Content "$root\generated\scaffold-certification\scaffold_certification_validation.json"
