[CmdletBinding()]
param([string]$HayesPath="C:\temp\standars\hayes-verify")
$ErrorActionPreference="Stop"

$expected=@(
  "src\hayes_verify\pilots\github_evaluators.py",
  "tests\test_branch_rationale_consistency.py",
  "registry\hayes_verify_branch_rationale_hotfix_spec.json",
  "scripts\Test-HayesVerifyBranchRationaleConsistency.ps1"
)

$missing=@()
foreach($rel in $expected){
    if(-not(Test-Path (Join-Path $HayesPath $rel))){
        $missing += $rel
    }
}

if($missing.Count -gt 0){
    $missing | ForEach-Object { Write-Host "MISSING: $_" -ForegroundColor Red }
    throw "Evaluated-branch rationale hotfix installation incomplete."
}

Write-Host "PASS: evaluated-branch rationale hotfix installation verified." -ForegroundColor Green
