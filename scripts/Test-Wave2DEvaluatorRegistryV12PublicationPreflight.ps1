[CmdletBinding()]
param([string]$HayesPath="C:\temp\standars\hayes-verify")
$ErrorActionPreference="Stop"

function Fail([string]$m){
    throw "WAVE2D REGISTRY V1.2 PUBLICATION PREFLIGHT BLOCKED: $m"
}

$root=(Resolve-Path $HayesPath).Path
$registry=Join-Path $root "registry\wave2d_evaluator_registry_v1_2.json"
$cert=Join-Path $root "generated\wave2d\evaluator-expansion\github_workflow_ci_registry_v1_2_certification.json"
$verification=Join-Path $root "generated\wave2d\evaluator-expansion\github-workflow-ci-verification\verification_manifest.json"
$py=Join-Path $root ".venv\Scripts\python.exe"

foreach($p in @($registry,$cert,$verification)){
    if(-not(Test-Path $p)){
        Fail "missing required artifact: $p"
    }
}

$r=Get-Content $registry -Raw | ConvertFrom-Json
$c=Get-Content $cert -Raw | ConvertFrom-Json
$v=Get-Content $verification -Raw | ConvertFrom-Json

if($r.registry_version -ne "1.2"){Fail "registry_version mismatch"}
if($r.status -ne "CANDIDATE_FROZEN"){Fail "registry state mismatch"}

$controlCount=@($r.controls.PSObject.Properties).Count
if($controlCount -ne 80){Fail "registry control count is not 80; actual=$controlCount"}

if($c.status -ne "PASS"){Fail "certification not PASS"}
if($c.registry_version -ne "1.2"){Fail "certification registry_version mismatch"}
if($c.registry_state -ne "CANDIDATE_FROZEN"){Fail "certification registry_state mismatch"}
if($c.verification_batch_id -ne "BATCH-20260814T151718.053583Z"){Fail "verification batch mismatch"}
if([int]$c.promoted_control_count -ne 6){Fail "promoted_control_count is not 6"}

$registryHash=(Get-FileHash $registry -Algorithm SHA256).Hash.ToLower()
$verificationHash=(Get-FileHash $verification -Algorithm SHA256).Hash.ToLower()

if($registryHash -ne "0940e2a7293b47afcda0c10998357f8510819f22db7958fca4cd2e46093118f5"){Fail "registry SHA mismatch: $registryHash"}
if($verificationHash -ne "d6226324b8790fdaf0c1e10806931f58b267ed50aa8a703f978abf1393b9987c"){Fail "verification SHA mismatch: $verificationHash"}
if($c.registry_sha256.ToLower() -ne $registryHash){Fail "certification registry SHA mismatch"}
if($c.verification_sha256.ToLower() -ne $verificationHash){Fail "certification verification SHA mismatch"}

& $py -m ruff check "$root\scripts\build_priority1_final_remaining_backlog.py"
if($LASTEXITCODE){Fail "Ruff failed"}

Write-Host "PASS: evaluator registry v1.2 publication preflight verified." -ForegroundColor Green
Write-Host "registry_sha256=$registryHash"
Write-Host "verification_sha256=$verificationHash"
