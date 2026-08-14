[CmdletBinding()]
param(
    [string]$Repo="OscarMackJr/hayes-verify",
    [string]$HayesPath="C:\temp\standars\hayes-verify",
    [string]$Branch="feature/wave2d-evaluator-registry-v1-2"
)
$ErrorActionPreference="Stop"

function Fail([string]$m){
    throw "WAVE2D REGISTRY V1.2 PUBLISH BLOCKED: $m"
}

$root=(Resolve-Path $HayesPath).Path
Set-Location $root

& "$root\scripts\Test-Wave2DEvaluatorRegistryV12PublicationPreflight.ps1" `
    -HayesPath $root
if(-not $?){Fail "preflight failed"}

& "$root\scripts\Build-Wave2DPriority1FinalRemainingBacklog.ps1" `
    -HayesPath $root
if(-not $?){Fail "backlog refresh failed"}

git fetch origin main
if($LASTEXITCODE){Fail "fetch failed"}

$current=(git branch --show-current).Trim()

if($current -eq "main"){
    git switch -c $Branch
    if($LASTEXITCODE){Fail "branch creation failed"}
}
elseif($current -ne $Branch){
    Fail "expected main or $Branch; current=$current"
}

& "$root\scripts\Stage-Wave2DEvaluatorRegistryV12ForPublish.ps1" `
    -HayesPath $root
if(-not $?){Fail "stage failed"}

git commit -m "publish Wave 2D evaluator registry v1.2 and final Priority-1 backlog"
if($LASTEXITCODE){Fail "commit failed"}

git push -u origin $Branch
if($LASTEXITCODE){Fail "push failed"}

$existing=gh pr list `
    --repo $Repo `
    --head $Branch `
    --state open `
    --json number `
    --jq '.[0].number'

if($LASTEXITCODE){Fail "PR lookup failed"}

if(-not $existing){
    $bodyFile=Join-Path $env:TEMP "wave2d-registry-v1-2-pr.md"

    @'
Publishes Wave 2D evaluator registry v1.2 after successful github_workflow_ci family batch verification.

Promoted github_workflow_ci controls: 6.

This publication also refreshes the final Priority-1 backlog directly from registry v1.2.

Expected remaining Priority-1 work:
- github_branch_policy: 2
- github_security_monitoring: 1
- total: 3
'@ | Set-Content $bodyFile -Encoding UTF8

    gh pr create `
        --repo $Repo `
        --base main `
        --head $Branch `
        --draft `
        --title "Publish Wave 2D evaluator registry v1.2" `
        --body-file $bodyFile

    $rc=$LASTEXITCODE
    Remove-Item $bodyFile -Force -ErrorAction SilentlyContinue

    if($rc){
        Fail "draft PR creation failed"
    }
}
else{
    Write-Host "Open PR already exists: #$existing"
}

Write-Host "PASS: evaluator registry v1.2 published and final Priority-1 backlog refreshed." -ForegroundColor Green
