[CmdletBinding()]
param(
    [string]$EMSPath="C:\temp\standars\ems",
    [string]$Repo="OscarMackJr/ems",
    [switch]$CommitPush,
    [switch]$CreatePR
)
$ErrorActionPreference="Stop"

Write-Host "=== 1. Scope PASS ===" -ForegroundColor Cyan
& (Join-Path $EMSPath "scripts\Test-Wave2C-Scope.ps1") -EMSPath $EMSPath
if(-not $?){throw "Scope gate failed."}

Write-Host "`n=== 2. Stage ===" -ForegroundColor Cyan
& (Join-Path $EMSPath "scripts\Stage-Wave2C.ps1") -EMSPath $EMSPath
if(-not $?){throw "Staging failed."}

Write-Host "`n=== 3. Inspect staged files ===" -ForegroundColor Cyan
& (Join-Path $EMSPath "scripts\Inspect-Wave2CStagedFiles.ps1") -EMSPath $EMSPath
if(-not $?){throw "Staged-file inspection failed."}

Write-Host "`n=== 4. PR readiness ===" -ForegroundColor Cyan
& (Join-Path $EMSPath "scripts\Test-Wave2C-PRReadiness.ps1") -EMSPath $EMSPath
if(-not $?){throw "PR readiness failed."}

if($CommitPush){
    Write-Host "`n=== 5. Commit / Push ===" -ForegroundColor Cyan
    & (Join-Path $EMSPath "scripts\CommitPush-Wave2C.ps1") -EMSPath $EMSPath -Push
    if(-not $?){throw "Commit/push failed."}
}

if($CreatePR){
    Write-Host "`n=== 6. Prepare PR ===" -ForegroundColor Cyan
    & (Join-Path $EMSPath "scripts\Create-Wave2CPR.ps1") -EMSPath $EMSPath -Repo $Repo
    if(-not $?){throw "PR creation failed."}
}

Write-Host "`nPASS: Wave 2C finalization pipeline completed through requested checkpoint." -ForegroundColor Green
