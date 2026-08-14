[CmdletBinding()]
param(
 [string]$Repo="OscarMackJr/hayes-verify",
 [string]$HayesPath="C:\temp\standars\hayes-verify",
 [string]$Branch="feature/wave2d-evaluator-registry-v1-1"
)
$ErrorActionPreference="Stop"
function Fail([string]$m){throw "WAVE2D REGISTRY V1.1 PUBLISH BLOCKED: $m"}
$root=(Resolve-Path $HayesPath).Path
Set-Location $root

& "$root\scripts\Test-Wave2DEvaluatorRegistryV11PublicationPreflight.ps1" -HayesPath $root
if(-not $?){Fail "preflight failed"}

& "$root\scripts\Build-Wave2DPriority1RemainingBacklog.ps1" -HayesPath $root
if(-not $?){Fail "backlog refresh failed"}

git fetch origin main
if($LASTEXITCODE){Fail "fetch failed"}

$current=(git branch --show-current).Trim()
if($current -eq "main"){
 git switch -c $Branch
 if($LASTEXITCODE){Fail "branch creation failed"}
}elseif($current -ne $Branch){
 Fail "expected main or $Branch; current=$current"
}

& "$root\scripts\Stage-Wave2DEvaluatorRegistryV11ForPublish.ps1" -HayesPath $root
if(-not $?){Fail "stage failed"}

git commit -m "publish Wave 2D evaluator registry v1.1 and remaining Priority-1 backlog"
if($LASTEXITCODE){Fail "commit failed"}

git push -u origin $Branch
if($LASTEXITCODE){Fail "push failed"}

$existing=gh pr list --repo $Repo --head $Branch --state open --json number --jq '.[0].number'
if($LASTEXITCODE){Fail "PR lookup failed"}

if(-not $existing){
 $body=Join-Path $env:TEMP "wave2d-registry-v1-1-pr.md"
 @'
Publishes Wave 2D evaluator registry v1.1 after successful repository-filesystem family batch verification.

Promoted repository-filesystem controls: 8.
Remaining Priority-1 backlog is regenerated directly from registry v1.1.
'@ | Set-Content $body -Encoding UTF8

 gh pr create --repo $Repo --base main --head $Branch --draft `
   --title "Publish Wave 2D evaluator registry v1.1" --body-file $body
 $rc=$LASTEXITCODE
 Remove-Item $body -Force -ErrorAction SilentlyContinue
 if($rc){Fail "draft PR creation failed"}
}else{
 Write-Host "Open PR already exists: #$existing"
}

Write-Host "PASS: evaluator registry v1.1 published and remaining Priority-1 backlog refreshed." -ForegroundColor Green
