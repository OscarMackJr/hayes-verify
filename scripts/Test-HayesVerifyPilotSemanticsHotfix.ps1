[CmdletBinding()]
param([string]$HayesPath="C:\temp\standars\hayes-verify")
$ErrorActionPreference="Stop"
$root=(Resolve-Path $HayesPath).Path

Write-Host "=== Ruff semantic hotfix ===" -ForegroundColor Cyan
python -m ruff check "$root\src" "$root\tests"
if($LASTEXITCODE){throw "Ruff failed after semantic hotfix."}

Write-Host "`n=== Pytest semantic hotfix ===" -ForegroundColor Cyan
python -m pytest -q
if($LASTEXITCODE){throw "Pytest failed after semantic hotfix."}

Write-Host "PASS: semantic hotfix validated. API failures cannot yield PASS." -ForegroundColor Green
