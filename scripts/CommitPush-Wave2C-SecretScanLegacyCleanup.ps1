[CmdletBinding()]
param(
    [string]$EMSPath="C:\temp\standars\ems",
    [string]$CommitMessage="remove obsolete secret-scan maintenance sources"
)

$ErrorActionPreference="Stop"

Write-Host "=== Validate staged cleanup ===" -ForegroundColor Cyan
& (Join-Path $EMSPath "scripts\Test-Wave2C-SecretScanLegacyCleanup.ps1") -EMSPath $EMSPath
if(-not $?){throw "Cleanup validation failed."}

$staged=@(git -C $EMSPath diff --cached --name-only)
if($staged.Count -eq 0){throw "No staged cleanup changes."}

Write-Host "`n=== Commit cleanup ===" -ForegroundColor Cyan
git -C $EMSPath commit -m $CommitMessage
if($LASTEXITCODE){throw "git commit failed."}

Write-Host "`n=== Push Wave 2C branch ===" -ForegroundColor Cyan
git -C $EMSPath push origin feature/wave2c-remediation
if($LASTEXITCODE){throw "git push failed."}

Write-Host "`nPASS: secret-scan cleanup committed and pushed." -ForegroundColor Green
