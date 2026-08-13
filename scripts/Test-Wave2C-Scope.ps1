[CmdletBinding()]
param([string]$EMSPath="C:\temp\standars\ems")
$ErrorActionPreference="Stop"

Write-Host "=== Wave 2C scope validation ===" -ForegroundColor Cyan
& (Join-Path $EMSPath "scripts\Prepare-Wave2CPostCloseoutRelease.ps1") -EMSPath $EMSPath
if(-not $?){throw "Wave 2C scope/release preparation failed."}

$scope=Join-Path $EMSPath "release\wave2c\post-closeout\scope_validation.json"
if(-not(Test-Path $scope)){throw "Scope validation artifact missing."}
$s=Get-Content $scope -Raw | ConvertFrom-Json
if($s.status -ne "PASS"){throw "Wave 2C scope validation is not PASS."}

Write-Host "PASS: Wave 2C scope validation passed." -ForegroundColor Green
