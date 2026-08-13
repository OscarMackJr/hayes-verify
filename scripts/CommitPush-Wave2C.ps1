[CmdletBinding()]
param(
    [string]$EMSPath="C:\temp\standars\ems",
    [string]$CommitMessage="close Wave 2C remediation and certification",
    [switch]$Push
)
$ErrorActionPreference="Stop"

Write-Host "=== Final PR readiness check ===" -ForegroundColor Cyan
& (Join-Path $EMSPath "scripts\Test-Wave2C-PRReadiness.ps1") -EMSPath $EMSPath
if(-not $?){throw "Wave 2C PR readiness failed."}

Write-Host "`n=== Commit Wave 2C closeout ===" -ForegroundColor Cyan
git -C $EMSPath commit -m $CommitMessage
if($LASTEXITCODE){throw "git commit failed."}

if($Push){
    Write-Host "`n=== Push Wave 2C branch ===" -ForegroundColor Cyan
    git -C $EMSPath push -u origin feature/wave2c-remediation
    if($LASTEXITCODE){throw "git push failed."}
}

Write-Host "`nPASS: Wave 2C commit completed$(if($Push){' and pushed'})." -ForegroundColor Green
