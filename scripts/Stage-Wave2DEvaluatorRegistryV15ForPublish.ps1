[CmdletBinding()]
param([string]$HayesPath="C:\temp\standars\hayes-verify")
$ErrorActionPreference="Stop"

function Fail([string]$m){
    throw "WAVE2D REGISTRY V1.5 STAGE BLOCKED: $m"
}

$root=(Resolve-Path $HayesPath).Path
Set-Location $root

$normal=@(
    "registry/wave2d_evaluator_registry_v1_5.json",
    "registry/wave2d_evaluator_registry_v1_5_publication_spec.json",
    "scripts/build_priority2_remaining_backlog.py",
    "scripts/Build-Wave2DPriority2RemainingBacklog.ps1",
    "scripts/Test-Wave2DEvaluatorRegistryV15PublicationPreflight.ps1",
    "scripts/Stage-Wave2DEvaluatorRegistryV15ForPublish.ps1",
    "scripts/Publish-Wave2DEvaluatorRegistryV15.ps1"
)

$forced=@(
    "generated/wave2d/evaluator-expansion/dependency_supply_chain_registry_v1_5_certification.json",
    "generated/wave2d/evaluator-expansion/dependency-supply-chain-verification/verification_manifest.json",
    "generated/wave2d/evaluator-expansion/priority2_remaining_implementation_backlog.json",
    "generated/wave2d/evaluator-expansion/priority2_remaining_family_plan.json",
    "generated/wave2d/evaluator-expansion/priority2_remaining_summary.json"
)

$expected=@($normal+$forced)

foreach($p in $expected){
    if(-not(Test-Path $p)){
        Fail "missing publish artifact: $p"
    }
}

git reset
if($LASTEXITCODE){Fail "git reset failed"}

foreach($p in $normal){
    git add -- $p
    if($LASTEXITCODE){Fail "failed to stage $p"}
}

foreach($p in $forced){
    git add -f -- $p
    if($LASTEXITCODE){Fail "failed to force-stage $p"}
}

$cached=@(git diff --cached --name-only)
$unexpected=@($cached | Where-Object {$_ -notin $expected})
if($unexpected.Count){
    Fail "unexpected staged files: $($unexpected -join ', ')"
}

$missing=@($expected | Where-Object {$_ -notin $cached})
if($missing.Count){
    Fail "expected staged files missing: $($missing -join ', ')"
}

Write-Host "PASS: evaluator registry v1.5 publication set staged." -ForegroundColor Green
