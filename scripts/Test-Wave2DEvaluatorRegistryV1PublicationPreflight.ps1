[CmdletBinding()]
param([string]$HayesPath="C:\temp\standars\hayes-verify")
$ErrorActionPreference="Stop"
function Fail([string]$m){throw "WAVE2D REGISTRY V1 PUBLICATION PREFLIGHT BLOCKED: $m"}

$root=(Resolve-Path $HayesPath).Path
$registry=Join-Path $root "registry\wave2d_evaluator_registry_v1.json"
$cert=Join-Path $root "generated\wave2d\evaluator-expansion\evaluator_registry_v1_certification.json"
$py=Join-Path $root ".venv\Scripts\python.exe"

foreach($p in @($registry,$cert)){
    if(-not(Test-Path $p)){Fail "missing required artifact: $p"}
}

$registryObj=Get-Content $registry -Raw | ConvertFrom-Json
$certObj=Get-Content $cert -Raw | ConvertFrom-Json

if($registryObj.status -ne "FROZEN"){Fail "registry status is not FROZEN"}
if([int]$registryObj.control_count -ne 80){Fail "registry control_count is not 80"}
if($certObj.status -ne "PASS"){Fail "certification status is not PASS"}
if($certObj.registry_state -ne "FROZEN"){Fail "certification registry_state is not FROZEN"}
if([int]$certObj.control_count -ne 80){Fail "certification control_count is not 80"}

$actual=(Get-FileHash $registry -Algorithm SHA256).Hash.ToLower()
if($actual -ne $certObj.registry_sha256.ToLower()){
    Fail "registry SHA-256 does not match certification"
}

& $py -m ruff check "$root\scripts\build_priority1_backlog.py"
if($LASTEXITCODE){Fail "Ruff failed"}

Write-Host "PASS: evaluator registry v1 publication preflight verified." -ForegroundColor Green
Write-Host "registry_sha256=$actual"
