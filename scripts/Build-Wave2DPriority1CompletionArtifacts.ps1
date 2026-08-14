[CmdletBinding()]
param([string]$HayesPath="C:\temp\standars\hayes-verify")
$ErrorActionPreference="Stop"

function Fail([string]$m){
    throw "WAVE2D PRIORITY1 COMPLETION ARTIFACT BUILD BLOCKED: $m"
}

$root=(Resolve-Path $HayesPath).Path
$py="$root\.venv\Scripts\python.exe"

& $py "$root\scripts\build_priority1_completion_artifacts.py" `
    --registry "$root\registry\wave2d_evaluator_registry_v1_4.json" `
    --source-certification "$root\generated\wave2d\evaluator-expansion\github_security_monitoring_registry_v1_4_certification.json" `
    --verification "$root\generated\wave2d\evaluator-expansion\github-security-monitoring-verification\verification_manifest.json" `
    --backlog-output "$root\generated\wave2d\evaluator-expansion\priority1_completion_backlog.json" `
    --completion-certification-output "$root\generated\wave2d\evaluator-expansion\priority1_completion_certification.json" `
    --completion-manifest-output "$root\generated\wave2d\evaluator-expansion\priority1_completion_manifest.json"

if($LASTEXITCODE){
    Fail "Priority-1 completion artifact generation failed"
}

Write-Host "PASS: Priority-1 completion artifacts generated." -ForegroundColor Green
