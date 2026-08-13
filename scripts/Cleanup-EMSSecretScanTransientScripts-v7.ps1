[CmdletBinding()]
param(
    [string]$EMSPath = "C:\temp\standars\ems"
)

$ErrorActionPreference = "Stop"

$scriptRoot = Join-Path $EMSPath "scripts"
if(-not(Test-Path $scriptRoot)){
    throw "Scripts directory not found: $scriptRoot"
}

Write-Host "=== Remove transient secret-scan maintenance scripts ===" -ForegroundColor Cyan

$patterns = @(
    "Patch-EMSValidateSecretScan*.ps1",
    "Test-EMSValidateSecretScanSelfMatch*.ps1",
    "Test-EMSValidateSecretScanFalsePositives*.ps1",
    "Install-EMSValidateSecretScan*.ps1"
)

$remove = @()
foreach($pattern in $patterns){
    $remove += Get-ChildItem $scriptRoot -File -Filter $pattern -ErrorAction SilentlyContinue
}

$remove = @($remove | Sort-Object FullName -Unique)

if($remove.Count -eq 0){
    Write-Host "No transient secret-scan maintenance scripts found."
}
else{
    foreach($file in $remove){
        Write-Host "Removing $($file.Name)"
        Remove-Item $file.FullName -Force
    }
}

# Also remove untracked/local backup files created by earlier repair attempts.
Get-ChildItem $scriptRoot -File -Filter "*.pre-secret-*.bak" -ErrorAction SilentlyContinue |
    Remove-Item -Force -ErrorAction SilentlyContinue

Get-ChildItem $scriptRoot -File -Filter "*.pre-secret-scan-*.bak" -ErrorAction SilentlyContinue |
    Remove-Item -Force -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "PASS: transient secret-scan maintenance scripts removed." -ForegroundColor Green
