[CmdletBinding()]
param([string]$HayesPath="C:\temp\standars\hayes-verify")
$ErrorActionPreference="Stop"

$root=(Resolve-Path $HayesPath).Path
$py=Join-Path $root ".venv\Scripts\python.exe"

& $py "$root\scripts\build_priority1_final_remaining_backlog.py" `
    --registry "$root\registry\wave2d_evaluator_registry_v1_2.json" `
    --backlog-output "$root\generated\wave2d\evaluator-expansion\priority1_final_remaining_implementation_backlog.json" `
    --plan-output "$root\generated\wave2d\evaluator-expansion\priority1_final_remaining_family_plan.json"

if($LASTEXITCODE){
    throw "Priority-1 final remaining backlog generation failed"
}

Write-Host "PASS: Priority-1 final remaining backlog refreshed." -ForegroundColor Green
