[CmdletBinding()]
param(
    [string]$Repo="OscarMackJr/hayes-verify",
    [string]$HayesPath="C:\temp\standars\hayes-verify",
    [string]$Branch="feature/wave2d-evaluator-registry-v1-5"
)
$ErrorActionPreference="Stop"

function Fail([string]$m){
    throw "WAVE2D REGISTRY V1.5 PUBLISH BLOCKED: $m"
}

$root=(Resolve-Path $HayesPath).Path
Set-Location $root

& "$root\scripts\Test-Wave2DEvaluatorRegistryV15PublicationPreflight.ps1" `
    -HayesPath $root
if(-not $?){Fail "preflight failed"}

& "$root\scripts\Build-Wave2DPriority2RemainingBacklog.ps1" `
    -HayesPath $root
if(-not $?){Fail "Priority-2 backlog refresh failed"}

$summary=Get-Content `
    "$root\generated\wave2d\evaluator-expansion\priority2_remaining_summary.json" `
    -Raw | ConvertFrom-Json

if([int]$summary.remaining_priority2_control_count -ne 17){
    Fail "expected 17 remaining Priority-2 controls"
}
if($summary.family_counts.dependency_supply_chain){
    Fail "dependency_supply_chain unexpectedly remains in backlog"
}

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

& "$root\scripts\Stage-Wave2DEvaluatorRegistryV15ForPublish.ps1" `
    -HayesPath $root
if(-not $?){Fail "stage failed"}

git commit -m "publish Wave 2D evaluator registry v1.5 and refresh Priority-2 backlog"
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
    $bodyFile=Join-Path $env:TEMP "wave2d-registry-v1-5-pr.md"

    @'
Publishes Wave 2D evaluator registry v1.5 after successful Priority-2 dependency_supply_chain batch verification.

Promoted Priority-2 controls: 4.

Priority-2 remaining backlog:
- test_quality: 4
- release_integrity: 6
- documentation_governance: 7
- total remaining: 17

The dependency_supply_chain family is removed from the refreshed backlog.
'@ | Set-Content $bodyFile -Encoding UTF8

    gh pr create `
        --repo $Repo `
        --base main `
        --head $Branch `
        --draft `
        --title "Publish Wave 2D evaluator registry v1.5 and refresh Priority-2 backlog" `
        --body-file $bodyFile

    $rc=$LASTEXITCODE
    Remove-Item $bodyFile -Force -ErrorAction SilentlyContinue

    if($rc){Fail "draft PR creation failed"}
}
else{
    Write-Host "Open PR already exists: #$existing"
}

Write-Host "PASS: evaluator registry v1.5 published and Priority-2 backlog refreshed." -ForegroundColor Green
