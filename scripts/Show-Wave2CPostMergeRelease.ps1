[CmdletBinding()]
param([string]$EMSPath="C:\temp\standars\ems")

$out=Join-Path $EMSPath "release\wave2c\post-merge"

Write-Host "Post-merge certification:" -ForegroundColor Cyan
Get-Content (Join-Path $out "post_merge_certification.json")

Write-Host "`nRelease summary:" -ForegroundColor Cyan
Get-Content (Join-Path $out "release_summary.json")

Write-Host "`nManifest:" -ForegroundColor Cyan
Get-Content (Join-Path $out "wave2c_post_merge_manifest.json")

Write-Host "`nGit state:" -ForegroundColor Cyan
git -C $EMSPath status --short
git -C $EMSPath log -5 --oneline
git -C $EMSPath tag --list "ems-v0.6.0-wave2c"
