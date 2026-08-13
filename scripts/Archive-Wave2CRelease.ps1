[CmdletBinding()]
param(
    [string]$EMSPath="C:\temp\standars\ems",
    [string]$ArchiveRoot="C:\temp\standars\ems-local-archive\releases"
)

$ErrorActionPreference="Stop"
function Fail([string]$m){throw "WAVE 2C ARCHIVE BLOCKED: $m"}

$root=(Resolve-Path $EMSPath).Path
$source=Join-Path $root "release\wave2c\post-merge"
$registration=Join-Path $root "registry\release_baselines\wave2c_baseline_registration.json"

if(-not(Test-Path $source)){Fail "Post-merge release root missing: $source"}
if(-not(Test-Path $registration)){Fail "Baseline registration missing: $registration"}

$r=Get-Content $registration -Raw | ConvertFrom-Json
if($r.status -ne "PASS"){Fail "Baseline registration is not PASS."}

$dest=Join-Path $ArchiveRoot "ems-v0.6.0-wave2c"
New-Item -ItemType Directory -Force -Path $dest|Out-Null

Copy-Item (Join-Path $source "*") $dest -Recurse -Force
Copy-Item $registration (Join-Path $dest "wave2c_baseline_registration.json") -Force

$zip=Join-Path $dest "ems-v0.6.0-wave2c.zip"
if(-not(Test-Path $zip)){Fail "Archived release ZIP missing after copy."}

$hash=(Get-FileHash -Algorithm SHA256 $zip).Hash.ToLowerInvariant()
if($hash -ne ([string]$r.release_zip_sha256).ToLowerInvariant()){
    Fail "Archived release ZIP SHA-256 mismatch."
}

Write-Host "PASS: Wave 2C release archived externally." -ForegroundColor Green
Write-Host "Archive: $dest"
Write-Host "ZIP SHA-256: $hash"
