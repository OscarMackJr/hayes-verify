[CmdletBinding()]
param(
    [string]$EMSPath="C:\temp\standars\ems",
    [string]$Repo="OscarMackJr/ems"
)
$ErrorActionPreference="Stop"

& "$EMSPath\scripts\Run-Wave2DApplicabilityFreeze.ps1" -EMSPath $EMSPath
if(-not $?){throw "Freeze failed"}

& "$EMSPath\scripts\Stage-Wave2DDefinitionPackage.ps1" -EMSPath $EMSPath
if(-not $?){throw "Stage failed"}

& "$EMSPath\scripts\CommitPush-Wave2DDefinitionPackage.ps1" -EMSPath $EMSPath
if(-not $?){throw "Commit/push failed"}

& "$EMSPath\scripts\Create-Wave2DDefinitionPR.ps1" -EMSPath $EMSPath -Repo $Repo
if(-not $?){throw "PR creation failed"}

Write-Host "PASS: Wave 2D applicability freeze, stage, commit/push, and PR creation complete." -ForegroundColor Green
