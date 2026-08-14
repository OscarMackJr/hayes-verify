[CmdletBinding()]
param([string]$HayesPath="C:\temp\standars\hayes-verify")
$ErrorActionPreference="Stop"
function Fail([string]$m){throw "WAVE2D PRIORITY1 BACKLOG BLOCKED: $m"}

$root=(Resolve-Path $HayesPath).Path
$py=Join-Path $root ".venv\Scripts\python.exe"
$registry=Join-Path $root "registry\wave2d_evaluator_registry_v1.json"
$backlog=Join-Path $root "generated\wave2d\evaluator-expansion\priority1_implementation_backlog.json"
$plan=Join-Path $root "generated\wave2d\evaluator-expansion\priority1_family_plan.json"

& $py "$root\scripts\build_priority1_backlog.py" `
  --registry $registry `
  --backlog-output $backlog `
  --plan-output $plan
if($LASTEXITCODE){Fail "priority-1 backlog generation failed"}

Write-Host "PASS: Priority-1 implementation backlog generated." -ForegroundColor Green
Write-Host "Backlog: $backlog"
Write-Host "Plan:    $plan"
