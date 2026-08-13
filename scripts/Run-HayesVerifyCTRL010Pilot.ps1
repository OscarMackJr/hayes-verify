[CmdletBinding()]
param(
 [string]$HayesPath="C:\temp\standars\hayes-verify",
 [string]$RepositoryPath="C:\work\bluto\Enterprise_Starter_Kit_v2.0_Baselined",
 [string]$GitHubRepo="OscarMackJr/bluto"
)
$root=(Resolve-Path $HayesPath).Path
& "$root\scripts\Run-HayesVerifyPilot.ps1" `
 -ControlId EMS-CTRL-010 `
 -TargetId REPO-001 `
 -RepositoryPath $RepositoryPath `
 -GitHubRepo $GitHubRepo
if(-not $?){throw "CTRL-010 Hayes Verify pilot failed."}
