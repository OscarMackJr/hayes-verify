[CmdletBinding()]
param([string]$EMSPath="C:\temp\standars\ems")

$registration=Join-Path $EMSPath "registry\release_baselines\wave2c_baseline_registration.json"

Write-Host "Wave 2C baseline registration:" -ForegroundColor Cyan
if(Test-Path $registration){
    Get-Content $registration
}else{
    Write-Host "NOT YET REGISTERED" -ForegroundColor Yellow
}

Write-Host "`nTag:" -ForegroundColor Cyan
git -C $EMSPath show-ref --tags ems-v0.6.0-wave2c

Write-Host "`nMain:" -ForegroundColor Cyan
git -C $EMSPath log -3 --oneline

Write-Host "`nGit status:" -ForegroundColor Cyan
git -C $EMSPath status --short
