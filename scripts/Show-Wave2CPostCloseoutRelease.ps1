[CmdletBinding()]
param([string]$EMSPath="C:\temp\standars\ems")

$out=Join-Path $EMSPath "release\wave2c\post-closeout"

Write-Host "Branch certification:" -ForegroundColor Cyan
Get-Content (Join-Path $out "branch_certification.json")

Write-Host "`nScope validation:" -ForegroundColor Cyan
Get-Content (Join-Path $out "scope_validation.json")

Write-Host "`nRelease package summary:" -ForegroundColor Cyan
Get-Content (Join-Path $out "release_package_summary.json")

Write-Host "`nFrozen artifact manifest:" -ForegroundColor Cyan
Import-Csv (Join-Path $out "wave2c_frozen_artifact_manifest.csv") |
    Format-Table -Wrap -AutoSize

Write-Host "`nGit status:" -ForegroundColor Cyan
git -C $EMSPath status --short
