[CmdletBinding()]
param(
    [string]$Repo="OscarMackJr/hayes-verify",
    [string]$HayesPath="C:\temp\standars\hayes-verify",
    [string]$Branch="feature/wave2d-evaluator-registry-v1"
)
$ErrorActionPreference="Stop"
function Fail([string]$m){throw "WAVE2D REGISTRY V1 PUBLISH BLOCKED: $m"}

$root=(Resolve-Path $HayesPath).Path
Set-Location $root

& "$root\scripts\Test-Wave2DEvaluatorRegistryV1PublicationPreflight.ps1" -HayesPath $root
if(-not $?){Fail "preflight failed"}

& "$root\scripts\Build-Wave2DPriority1ImplementationBacklog.ps1" -HayesPath $root
if(-not $?){Fail "backlog generation failed"}

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

& "$root\scripts\Stage-Wave2DEvaluatorRegistryV1ForPublish.ps1" -HayesPath $root
if(-not $?){Fail "stage failed"}

git commit -m "publish Wave 2D evaluator registry v1 and priority-1 backlog"
if($LASTEXITCODE){Fail "commit failed"}

git push -u origin $Branch
if($LASTEXITCODE){Fail "push failed"}

$existing=gh pr list --repo $Repo --head $Branch --state open --json number --jq '.[0].number'
if($LASTEXITCODE){Fail "PR lookup failed"}

if(-not $existing){
    $bodyFile=Join-Path $env:TEMP "wave2d-registry-v1-pr.md"
    @"
Publishes the frozen and certified Wave 2D evaluator registry v1 for all 80 EMS controls.

Also publishes the generated Priority-1 implementation backlog derived directly from the frozen registry.

The registry remains planning authority only:
- IMPLEMENTED controls are already proven.
- PLANNED_AUTOMATED / PLANNED_HYBRID controls are not executable until implemented and tested.
- HUMAN_EVIDENCE_REQUIRED controls remain outside automatic evaluation.
"@ | Set-Content $bodyFile -Encoding UTF8

    gh pr create `
      --repo $Repo `
      --base main `
      --head $Branch `
      --draft `
      --title "Publish Wave 2D evaluator registry v1" `
      --body-file $bodyFile
    $rc=$LASTEXITCODE
    Remove-Item $bodyFile -Force -ErrorAction SilentlyContinue
    if($rc){Fail "draft PR creation failed"}
}
else{
    Write-Host "Open PR already exists: #$existing"
}

Write-Host "PASS: evaluator registry v1 published and Priority-1 backlog baselined." -ForegroundColor Green
