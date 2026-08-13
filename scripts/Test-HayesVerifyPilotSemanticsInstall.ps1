[CmdletBinding()]
param([string]$HayesPath="C:\temp\standars\hayes-verify")
$ErrorActionPreference="Stop"

$expected=@(
  "src\hayes_verify\pilots\github_collectors.py",
  "src\hayes_verify\pilots\github_evaluators.py",
  "tests\test_pilot_semantics.py",
  "registry\hayes_verify_pilot_semantics_hotfix_spec.json",
  "schemas\hayes_verify_pilot_semantic_evidence.schema.json",
  "scripts\Test-HayesVerifyPilotSemanticsHotfix.ps1",
  "scripts\Test-HayesVerifyPilotSemanticsInstall.ps1"
)

$missing=@()
foreach($rel in $expected){
    $p=Join-Path $HayesPath $rel
    if(-not(Test-Path $p)){$missing += $rel}
}

if($missing.Count -gt 0){
    $missing|ForEach-Object{Write-Host "MISSING: $_" -ForegroundColor Red}
    throw "Semantic hotfix installation incomplete."
}

Write-Host "PASS: semantic hotfix installation verified." -ForegroundColor Green
