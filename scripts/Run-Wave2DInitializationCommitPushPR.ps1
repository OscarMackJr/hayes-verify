[CmdletBinding()]
param(
    [string]$EMSPath="C:\temp\standars\ems",
    [string]$Repo="OscarMackJr/ems",
    [string]$CommitMessage="initialize Wave 2D from authoritative Wave 2C baseline"
)

$ErrorActionPreference="Stop"

Write-Host "=== Wave 2D initialization commit/push/PR pipeline ===" -ForegroundColor Cyan

& (Join-Path $EMSPath "scripts\CommitPush-Wave2DInitialization.ps1") `
    -EMSPath $EMSPath `
    -CommitMessage $CommitMessage
if(-not $?){throw "Wave 2D commit/push failed."}

& (Join-Path $EMSPath "scripts\Create-Wave2DInitializationPR.ps1") `
    -EMSPath $EMSPath `
    -Repo $Repo
if(-not $?){throw "Wave 2D PR creation failed."}

Write-Host "PASS: Wave 2D initialization branch committed, pushed, and PR prepared." -ForegroundColor Green
