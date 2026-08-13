[CmdletBinding()]
param([string]$EMSPath="C:\temp\standars\ems")
$ErrorActionPreference="Stop"

Write-Host "=== Inspect staged Wave 2C changes ===" -ForegroundColor Cyan

$spec=Get-Content (Join-Path $EMSPath "registry\wave2c_branch_finalization_spec.json") -Raw | ConvertFrom-Json
$allowed=@($spec.allowed_roots)

$paths=@(git -C $EMSPath diff --cached --name-only)
if($paths.Count -eq 0){throw "No staged paths to inspect."}

$bad=@()
foreach($p in $paths){
    $norm=$p.Replace("\","/")
    $ok=$false
    foreach($root in $allowed){
        if($norm.StartsWith($root)){ $ok=$true; break }
    }
    if(-not $ok){$bad += $norm}
}

Write-Host "`nStaged diff stat:" -ForegroundColor Cyan
git -C $EMSPath diff --cached --stat

Write-Host "`nStaged name-status:" -ForegroundColor Cyan
git -C $EMSPath diff --cached --name-status

if($bad.Count -gt 0){
    Write-Host "`nOut-of-scope staged paths:" -ForegroundColor Red
    $bad | ForEach-Object { Write-Host $_ }
    throw "Staged scope validation failed."
}

Write-Host "`nPASS: staged Wave 2C scope is valid." -ForegroundColor Green
