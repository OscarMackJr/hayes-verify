[CmdletBinding()]
param([string]$EMSPath="C:\temp\standars\ems")
$ErrorActionPreference="Stop"
function Fail([string]$m){throw "MAIN CLEANUP BLOCKED: $m"}

$root=(Resolve-Path $EMSPath).Path
git -C $root switch main
if($LASTEXITCODE){Fail "Failed to switch to main"}

git -C $root pull --ff-only origin main
if($LASTEXITCODE){Fail "Failed to update main"}

$status=@(git -C $root status --porcelain)
if($status.Count -gt 0){
    $status|ForEach-Object{Write-Host $_}
    Fail "main is not clean"
}

Write-Host "PASS: local main is clean and synchronized after baseline persistence." -ForegroundColor Green
git -C $root log -3 --oneline
