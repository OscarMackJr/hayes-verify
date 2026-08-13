[CmdletBinding()]
param([string]$EMSPath="C:\temp\standars\ems")
$ErrorActionPreference="Stop"
function Fail([string]$m){throw "WAVE 2D SCOPE/POPULATION BLOCKED: $m"}
$root=(Resolve-Path $EMSPath).Path
$spec="$root\registry\wave2d_scope_population_spec.json"
if((git -C $root branch --show-current).Trim() -ne "feature/wave2d-scope-population"){Fail "Wrong branch"}
$py=if($env:VIRTUAL_ENV -and (Test-Path "$env:VIRTUAL_ENV\Scripts\python.exe")){"$env:VIRTUAL_ENV\Scripts\python.exe"}else{(Get-Command python).Source}
& $py "$root\scripts\Discover-Wave2DScopeCandidates.py" --root $root --spec $spec
if($LASTEXITCODE){Fail "Candidate discovery failed"}
& $py "$root\scripts\Initialize-Wave2DDecisions.py" --root $root --spec $spec
if($LASTEXITCODE){Fail "Decision initialization failed"}
& $py "$root\scripts\Build-Wave2DScopePopulation.py" --root $root --spec $spec
if($LASTEXITCODE){Fail "Scope/population build failed"}
& $py "$root\scripts\Validate-Wave2DScopePopulation.py" --root $root --spec $spec
if($LASTEXITCODE){Fail "Scope/population validation failed"}
Write-Host "PASS: Wave 2D scope/population complete. No evaluation or promotion performed." -ForegroundColor Green
