[CmdletBinding()]
param([string]$EMSPath="C:\temp\standars\ems")
$ErrorActionPreference="Stop"
function Fail([string]$m){throw "WAVE 2D SCOPE STAGE BLOCKED: $m"}
$root=(Resolve-Path $EMSPath).Path
$allowed=@("registry/wave2d_scope_population_spec.json","schemas/wave2d_scope_population_summary.schema.json","registry/wave2d/control_scope_decisions.csv","registry/wave2d/evaluation_target_decisions.csv","registry/wave2d/scope.json","registry/wave2d/population.json","generated/wave2d/scope-definition/candidate_controls.csv","generated/wave2d/scope-definition/candidate_targets.csv","generated/wave2d/scope-definition/scope_population_summary.json","scripts/Discover-Wave2DScopeCandidates.py","scripts/Initialize-Wave2DDecisions.py","scripts/Build-Wave2DScopePopulation.py","scripts/Validate-Wave2DScopePopulation.py","scripts/Run-Wave2DScopePopulation.ps1","scripts/Show-Wave2DScopePopulation.ps1","scripts/Stage-Wave2DScopePopulation.ps1")
foreach($rel in $allowed){
    if(-not(Test-Path (Join-Path $root ($rel -replace '/','\')))){Fail "Missing expected artifact: $rel"}
    if($rel.StartsWith("generated/")){git -C $root add -f -- $rel}else{git -C $root add -- $rel}
    if($LASTEXITCODE){Fail "Failed to stage $rel"}
}
$staged=@(git -C $root diff --cached --name-only)
$bad=@($staged|Where-Object{$_ -notin $allowed})
if($bad.Count -gt 0){$bad|ForEach-Object{Write-Host $_};Fail "Out-of-scope staged path detected"}
git -C $root diff --cached --name-status
Write-Host "PASS: Wave 2D scope/population artifacts staged." -ForegroundColor Green
