[CmdletBinding()]
param([string]$HayesPath="C:\temp\standars\hayes-verify")
$ErrorActionPreference="Stop"

$root=(Resolve-Path $HayesPath).Path
$py=Join-Path $root ".venv\Scripts\python.exe"
$pytestTemp=Join-Path $root ".pytest-temp"

if(-not(Test-Path $py)){
    throw "Hayes Verify venv Python not found: $py"
}

if(Test-Path $pytestTemp){
    Remove-Item $pytestTemp -Recurse -Force -ErrorAction SilentlyContinue
}
New-Item -ItemType Directory -Force -Path $pytestTemp | Out-Null

Write-Host "=== Ruff full repository gate ===" -ForegroundColor Cyan
& $py -m ruff check "$root\src" "$root\tests"
if($LASTEXITCODE){
    throw "Ruff failed after v6 test-suite reconciliation."
}

Write-Host "`n=== Pytest deterministic repository-local gate ===" -ForegroundColor Cyan
& $py -m pytest --basetemp="$pytestTemp" -q "$root\tests"
if($LASTEXITCODE){
    throw "Pytest failed after v6 test-suite reconciliation."
}

Write-Host "PASS: v6 test-suite reconciliation validated." -ForegroundColor Green
