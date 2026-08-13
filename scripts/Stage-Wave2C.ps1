[CmdletBinding()]
param([string]$EMSPath="C:\temp\standars\ems")
$ErrorActionPreference="Stop"

Write-Host "=== Stage Wave 2C durable paths ===" -ForegroundColor Cyan
& (Join-Path $EMSPath "scripts\Prepare-Wave2CPostCloseoutRelease.ps1") -EMSPath $EMSPath -Stage
if(-not $?){throw "Wave 2C staging failed."}

$staged=@(git -C $EMSPath diff --cached --name-only)
if($staged.Count -eq 0){throw "No files staged."}

Write-Host "PASS: Wave 2C durable paths staged." -ForegroundColor Green
