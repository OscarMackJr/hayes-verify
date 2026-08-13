[CmdletBinding()]
param([string]$HayesPath="C:\temp\standars\hayes-verify")
$ErrorActionPreference="Stop"
$root=(Resolve-Path $HayesPath).Path

Write-Host "=== Verify GitHub API invocation hotfix ===" -ForegroundColor Cyan

python -m ruff check "$root\src" "$root\tests"
if($LASTEXITCODE){throw "Ruff failed after GitHub API invocation hotfix."}

python -m pytest -q
if($LASTEXITCODE){throw "Pytest failed after GitHub API invocation hotfix."}

Write-Host "PASS: gh api invocation hotfix validated; --repo is not appended." -ForegroundColor Green
