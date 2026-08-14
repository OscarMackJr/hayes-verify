[CmdletBinding()]
param(
    [string]$Repo="OscarMackJr/hayes-verify",
    [string]$HayesPath="C:\temp\standars\hayes-verify",
    [string]$Branch="feature/wave2d-evaluator-registry-v1-4-priority1-complete"
)
$ErrorActionPreference="Stop"

function Fail([string]$m){
    throw "WAVE2D REGISTRY V1.4 PUBLISH BLOCKED: $m"
}

$root=(Resolve-Path $HayesPath).Path
Set-Location $root

& "$root\scripts\Test-Wave2DEvaluatorRegistryV14PublicationPreflight.ps1" `
    -HayesPath $root
if(-not $?){Fail "preflight failed"}

& "$root\scripts\Build-Wave2DPriority1CompletionArtifacts.ps1" `
    -HayesPath $root
if(-not $?){Fail "completion artifact build failed"}

$completion=Get-Content `
    "$root\generated\wave2d\evaluator-expansion\priority1_completion_certification.json" `
    -Raw | ConvertFrom-Json

if($completion.completion_state -ne "COMPLETE"){
    Fail "Priority-1 completion certification is not COMPLETE"
}
if([int]$completion.remaining_priority1_control_count -ne 0){
    Fail "Priority-1 remaining control count is not zero"
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

& "$root\scripts\Stage-Wave2DEvaluatorRegistryV14ForPublish.ps1" `
    -HayesPath $root
if(-not $?){Fail "stage failed"}

git commit -m "publish Wave 2D evaluator registry v1.4 and certify Priority-1 completion"
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
    $bodyFile=Join-Path $env:TEMP "wave2d-registry-v1-4-priority1-complete.md"

    @'
Publishes Wave 2D evaluator registry v1.4 and certifies Priority-1 evaluator completion.

Priority-1 completion:
- remaining controls: 0
- completion state: COMPLETE
- final promoted control: EMS-CTRL-022
- candidate registry version: 1.4

This publication includes the final verification manifest, source promotion certification,
zero-row Priority-1 backlog, Priority-1 completion certification, and completion manifest.
'@ | Set-Content $bodyFile -Encoding UTF8

    gh pr create `
        --repo $Repo `
        --base main `
        --head $Branch `
        --draft `
        --title "Publish Wave 2D evaluator registry v1.4 and certify Priority-1 completion" `
        --body-file $bodyFile

    $rc=$LASTEXITCODE
    Remove-Item $bodyFile -Force -ErrorAction SilentlyContinue

    if($rc){Fail "draft PR creation failed"}
}
else{
    Write-Host "Open PR already exists: #$existing"
}

Write-Host "PASS: evaluator registry v1.4 published." -ForegroundColor Green
Write-Host "PASS: Wave 2D Priority-1 completion certification published." -ForegroundColor Green
