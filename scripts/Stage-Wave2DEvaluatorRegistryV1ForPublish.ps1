[CmdletBinding()]
param([string]$HayesPath="C:\temp\standars\hayes-verify")
$ErrorActionPreference="Stop"
function Fail([string]$m){throw "WAVE2D REGISTRY V1 STAGE BLOCKED: $m"}

$root=(Resolve-Path $HayesPath).Path
Set-Location $root

$normal=@(
 "registry/wave2d_evaluator_registry_v1.json",
 "registry/wave2d_evaluator_registry_v1_publication_spec.json",
 "scripts/build_priority1_backlog.py",
 "scripts/Build-Wave2DPriority1ImplementationBacklog.ps1",
 "scripts/Test-Wave2DEvaluatorRegistryV1PublicationPreflight.ps1",
 "scripts/Stage-Wave2DEvaluatorRegistryV1ForPublish.ps1",
 "scripts/Publish-Wave2DEvaluatorRegistryV1.ps1"
)

$forced=@(
 "generated/wave2d/evaluator-expansion/evaluator_registry_v1_certification.json",
 "generated/wave2d/evaluator-expansion/priority1_implementation_backlog.json",
 "generated/wave2d/evaluator-expansion/priority1_family_plan.json"
)

$expected=@($normal+$forced)
foreach($p in $expected){
    if(-not(Test-Path $p)){Fail "missing publish artifact: $p"}
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
    $unexpected | ForEach-Object {Write-Host "UNEXPECTED: $_" -ForegroundColor Red}
    Fail "unexpected staged files"
}

$missing=@($expected | Where-Object {$_ -notin $cached})
if($missing.Count){
    $missing | ForEach-Object {Write-Host "MISSING: $_" -ForegroundColor Red}
    Fail "expected files not staged"
}

Write-Host "PASS: evaluator registry v1 publication set staged." -ForegroundColor Green
