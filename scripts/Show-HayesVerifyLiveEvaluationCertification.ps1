[CmdletBinding()]
param([string]$HayesPath="C:\temp\standars\hayes-verify")
$root=(Resolve-Path $HayesPath).Path
$out="$root\generated\pilot-live-certification\EMS-CTRL-009\REPO-001"
Write-Host "Live certification:" -ForegroundColor Cyan
Get-Content "$out\live_evaluation_certification.json"
Write-Host "`nEMS return envelope:" -ForegroundColor Cyan
Get-Content "$out\ems_return_envelope.json"
Write-Host "`nEnvelope validation:" -ForegroundColor Cyan
Get-Content "$out\ems_return_envelope_validation.json"
