[CmdletBinding()]
param([string]$HayesPath="C:\temp\standars\hayes-verify")
$ErrorActionPreference="Stop"

function Fail([string]$m){
    throw "WAVE2D REGISTRY V1.4 PUBLICATION PREFLIGHT BLOCKED: $m"
}

$root=(Resolve-Path $HayesPath).Path
$registry="$root\registry\wave2d_evaluator_registry_v1_4.json"
$cert="$root\generated\wave2d\evaluator-expansion\github_security_monitoring_registry_v1_4_certification.json"
$verification="$root\generated\wave2d\evaluator-expansion\github-security-monitoring-verification\verification_manifest.json"
$py="$root\.venv\Scripts\python.exe"

foreach($p in @($registry,$cert,$verification)){
    if(-not(Test-Path $p)){Fail "missing required artifact: $p"}
}

$r=Get-Content $registry -Raw | ConvertFrom-Json
$c=Get-Content $cert -Raw | ConvertFrom-Json
$v=Get-Content $verification -Raw | ConvertFrom-Json

if($r.registry_version -ne "1.4"){Fail "registry_version mismatch"}
if($r.status -ne "CANDIDATE_FROZEN"){Fail "registry state mismatch"}

$controlCount=@($r.controls.PSObject.Properties).Count
if($controlCount -ne 80){Fail "registry control count is not 80; actual=$controlCount"}

if($c.status -ne "PASS"){Fail "source certification not PASS"}
if($c.registry_version -ne "1.4"){Fail "certification registry_version mismatch"}
if($c.priority1_completion_state -ne "COMPLETE"){Fail "source priority1 completion state mismatch"}
if($c.verification_batch_id -ne "BATCH-20260814T163543.574829Z"){Fail "verification batch mismatch"}
if([int]$c.promoted_control_count -ne 1){Fail "promoted_control_count is not 1"}

$registryHash=(Get-FileHash $registry -Algorithm SHA256).Hash.ToLower()
$verificationHash=(Get-FileHash $verification -Algorithm SHA256).Hash.ToLower()

if($registryHash -ne "3b29cfde6959fd23f6552fc1b78b52140cecde45508d31a02598cf36291d451a"){Fail "registry SHA mismatch: $registryHash"}
if($verificationHash -ne "4686bbbcc16b8bb3cfb704f42ae66147fd5fddb417ea6726227d87ccf95195be"){Fail "verification SHA mismatch: $verificationHash"}
if($c.registry_sha256.ToLower() -ne $registryHash){Fail "certification registry SHA mismatch"}
if($c.verification_sha256.ToLower() -ne $verificationHash){Fail "certification verification SHA mismatch"}

& $py -m ruff check "$root\scripts\build_priority1_completion_artifacts.py"
if($LASTEXITCODE){Fail "Ruff failed"}

Write-Host "PASS: evaluator registry v1.4 publication preflight verified." -ForegroundColor Green
Write-Host "registry_sha256=$registryHash"
Write-Host "verification_sha256=$verificationHash"
