[CmdletBinding()]
param([string]$HayesPath="C:\temp\standars\hayes-verify")
$ErrorActionPreference="Stop"

$root=(Resolve-Path $HayesPath).Path
$py=Join-Path $root ".venv\Scripts\python.exe"
$testFile=Join-Path $root "tests\test_github_api_invocation.py"

if(-not(Test-Path $py)){
    throw "Hayes Verify venv Python not found: $py"
}

if(-not(Test-Path $testFile)){
    throw "Reconciled GitHub API regression test missing: $testFile"
}

Write-Host "PASS: v6 test-suite reconciliation installation verified." -ForegroundColor Green
