[CmdletBinding()]
param([string]$EMSPath="C:\temp\standars\ems")
$out=Join-Path $EMSPath "release\wave2c\post-merge"

foreach($name in @(
    "post_merge_certification.json",
    "release_summary.json",
    "wave2c_post_merge_manifest.json"
)){
    $p=Join-Path $out $name
    Write-Host "`n$name" -ForegroundColor Cyan
    if(Test-Path $p){Get-Content $p}else{Write-Host "NOT YET GENERATED" -ForegroundColor Yellow}
}

Write-Host "`nGit state" -ForegroundColor Cyan
git -C $EMSPath status --short
git -C $EMSPath log -5 --oneline
git -C $EMSPath tag --list "ems-v0.6.0-wave2c"
