[CmdletBinding()]
param([string]$HayesPath="C:\temp\standars\hayes-verify")
$ErrorActionPreference="Stop"

function Fail([string]$m){
    throw "WAVE2D REGISTRY V1.5 PUBLICATION PREFLIGHT BLOCKED: $m"
}

$root=(Resolve-Path $HayesPath).Path
$registry="$root\registry\wave2d_evaluator_registry_v1_5.json"
$cert="$root\generated\wave2d\evaluator-expansion\dependency_supply_chain_registry_v1_5_certification.json"
$verification="$root\generated\wave2d\evaluator-expansion\dependency-supply-chain-verification\verification_manifest.json"
$plan="$root\generated\wave2d\evaluator-expansion\priority2_family_expansion_plan.json"
$py="$root\.venv\Scripts\python.exe"

foreach($p in @($registry,$cert,$verification,$plan)){
    if(-not(Test-Path $p)){Fail "missing required artifact: $p"}
}

$r=Get-Content $registry -Raw | ConvertFrom-Json
$c=Get-Content $cert -Raw | ConvertFrom-Json

if($r.registry_version -ne "1.5"){Fail "registry_version mismatch"}
if($r.status -ne "CANDIDATE_FROZEN"){Fail "registry state mismatch"}

$controlCount=@($r.controls.PSObject.Properties).Count
if($controlCount -ne 80){Fail "registry control count is not 80; actual=$controlCount"}

if($c.status -ne "PASS"){Fail "certification not PASS"}
if($c.registry_version -ne "1.5"){Fail "certification registry_version mismatch"}
if($c.registry_state -ne "CANDIDATE_FROZEN"){Fail "certification registry_state mismatch"}
if($c.verification_batch_id -ne "BATCH-20260814T170133.101265Z"){Fail "verification batch mismatch"}
if([int]$c.promoted_control_count -ne 4){Fail "promoted_control_count is not 4"}

$registryHash=(Get-FileHash $registry -Algorithm SHA256).Hash.ToLower()
$verificationHash=(Get-FileHash $verification -Algorithm SHA256).Hash.ToLower()

if($registryHash -ne "a36ba9820d80ee9206bf3cdc74f710e1311e0f848dfedfb00276550095c23e73"){Fail "registry SHA mismatch: $registryHash"}
if($verificationHash -ne "34ced6eb7ce6cefe134642914be62fcbce86a888885feb95d0926247825051b2"){Fail "verification SHA mismatch: $verificationHash"}
if($c.registry_sha256.ToLower() -ne $registryHash){Fail "certification registry SHA mismatch"}
if($c.verification_sha256.ToLower() -ne $verificationHash){Fail "certification verification SHA mismatch"}

& $py -m ruff check "$root\scripts\build_priority2_remaining_backlog.py"
if($LASTEXITCODE){Fail "Ruff failed"}

Write-Host "PASS: evaluator registry v1.5 publication preflight verified." -ForegroundColor Green
Write-Host "registry_sha256=$registryHash"
Write-Host "verification_sha256=$verificationHash"
