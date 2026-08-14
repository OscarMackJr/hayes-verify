[CmdletBinding()]
param([string]$HayesPath="C:\temp\standars\hayes-verify")
$ErrorActionPreference="Stop"
function Fail([string]$m){throw "WAVE2D REGISTRY V1.1 STAGE BLOCKED: $m"}
$root=(Resolve-Path $HayesPath).Path
Set-Location $root
$normal=@(
 "registry/wave2d_evaluator_registry_v1_1.json",
 "registry/wave2d_evaluator_registry_v1_1_publication_spec.json",
 "scripts/build_priority1_remaining_backlog.py",
 "scripts/Build-Wave2DPriority1RemainingBacklog.ps1",
 "scripts/Test-Wave2DEvaluatorRegistryV11PublicationPreflight.ps1",
 "scripts/Stage-Wave2DEvaluatorRegistryV11ForPublish.ps1",
 "scripts/Publish-Wave2DEvaluatorRegistryV11.ps1"
)
$forced=@(
 "generated/wave2d/evaluator-expansion/repository_filesystem_registry_v1_1_certification.json",
 "generated/wave2d/evaluator-expansion/repository-filesystem-verification/verification_manifest.json",
 "generated/wave2d/evaluator-expansion/priority1_remaining_implementation_backlog.json",
 "generated/wave2d/evaluator-expansion/priority1_remaining_family_plan.json"
)
$expected=@($normal+$forced)
git reset
foreach($p in $normal){git add -- $p;if($LASTEXITCODE){Fail "failed to stage $p"}}
foreach($p in $forced){git add -f -- $p;if($LASTEXITCODE){Fail "failed to force-stage $p"}}
$cached=@(git diff --cached --name-only)
$unexpected=@($cached|Where-Object{$_ -notin $expected})
if($unexpected.Count){Fail "unexpected staged files: $($unexpected -join ', ')"}
Write-Host "PASS: evaluator registry v1.1 publication set staged." -ForegroundColor Green
