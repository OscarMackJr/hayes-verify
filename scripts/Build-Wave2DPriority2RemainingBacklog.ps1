[CmdletBinding()]
param([string]$HayesPath="C:\temp\standars\hayes-verify")
$ErrorActionPreference="Stop"

$root=(Resolve-Path $HayesPath).Path
$py="$root\.venv\Scripts\python.exe"

& $py "$root\scripts\build_priority2_remaining_backlog.py" `
    --registry "$root\registry\wave2d_evaluator_registry_v1_7.json" `
    --source-plan "$root\generated\wave2d\evaluator-expansion\priority2_family_expansion_plan.json" `
    --backlog-output "$root\generated\wave2d\evaluator-expansion\priority2_remaining_implementation_backlog.json" `
    --plan-output "$root\generated\wave2d\evaluator-expansion\priority2_remaining_family_plan.json" `
    --summary-output "$root\generated\wave2d\evaluator-expansion\priority2_remaining_summary.json"

if($LASTEXITCODE){
    throw "Priority-2 remaining backlog generation failed"
}

Write-Host "PASS: Priority-2 remaining backlog refreshed." -ForegroundColor Green
