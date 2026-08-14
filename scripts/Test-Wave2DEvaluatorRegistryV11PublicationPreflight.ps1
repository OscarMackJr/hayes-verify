[CmdletBinding()]
param([string]$HayesPath="C:\temp\standars\hayes-verify")
$ErrorActionPreference="Stop"
function Fail([string]$m){throw "WAVE2D REGISTRY V1.1 PUBLICATION PREFLIGHT BLOCKED: $m"}

$root=(Resolve-Path $HayesPath).Path
$registry=Join-Path $root "registry\wave2d_evaluator_registry_v1_1.json"
$cert=Join-Path $root "generated\wave2d\evaluator-expansion\repository_filesystem_registry_v1_1_certification.json"
$verification=Join-Path $root "generated\wave2d\evaluator-expansion\repository-filesystem-verification\verification_manifest.json"
$py=Join-Path $root ".venv\Scripts\python.exe"

foreach($p in @($registry,$cert,$verification)){
  if(-not(Test-Path $p)){Fail "missing required artifact: $p"}
}

$r=Get-Content $registry -Raw|ConvertFrom-Json
$c=Get-Content $cert -Raw|ConvertFrom-Json
$v=Get-Content $verification -Raw|ConvertFrom-Json

if($r.registry_version -ne "1.1"){Fail "registry_version mismatch"}
if($r.status -ne "CANDIDATE_FROZEN"){Fail "registry state mismatch"}
$cc=@($r.controls.PSObject.Properties).Count
if($cc -ne 80){Fail "registry control count is not 80; actual=$cc"}
if($c.status -ne "PASS"){Fail "certification not PASS"}
if($c.verification_batch_id -ne "BATCH-20260814T143950.926644Z"){Fail "verification batch mismatch"}
if([int]$c.promoted_control_count -ne 8){Fail "promoted_control_count is not 8"}

$rh=(Get-FileHash $registry -Algorithm SHA256).Hash.ToLower()
$vh=(Get-FileHash $verification -Algorithm SHA256).Hash.ToLower()
if($rh -ne "bb1c80f03c10627e351743a5947a9d18ac5e123ed451c9e0e02e95947be9a429"){Fail "registry SHA mismatch: $rh"}
if($vh -ne "b7d0e87fa707c086c393400bd37e2fe603818020d18a1ad0490b1ae83a9c6394"){Fail "verification SHA mismatch: $vh"}

& $py -m ruff check "$root\scripts\build_priority1_remaining_backlog.py"
if($LASTEXITCODE){Fail "Ruff failed"}

Write-Host "PASS: evaluator registry v1.1 publication preflight verified." -ForegroundColor Green
