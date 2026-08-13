[CmdletBinding()]
param([string]$HayesPath="C:\temp\standars\hayes-verify")
$ErrorActionPreference="Stop"
function Fail([string]$m){throw "HAYES VERIFY INITIAL BASELINE BLOCKED: $m"}

$root=(Resolve-Path $HayesPath).Path
$py=Join-Path $root ".venv\Scripts\python.exe"
$spec=Join-Path $root "registry\hayes_verify_repository_bootstrap_spec.json"
$schema=Join-Path $root "schemas\hayes_verify_initial_baseline.schema.json"
$pytestTemp=Join-Path $root ".pytest-temp"

if(-not(Test-Path $py)){Fail "Hayes Verify venv Python missing: $py"}

Write-Host "=== Repository hygiene / secret preflight ===" -ForegroundColor Cyan
& $py "$root\scripts\preflight_hayes_verify_repository.py" --root $root
if($LASTEXITCODE){Fail "repository hygiene preflight failed"}

Write-Host "`n=== Frozen EMS contract validation ===" -ForegroundColor Cyan
& $py "$root\scripts\validate_contract_bundle.py" --root $root
if($LASTEXITCODE){Fail "contract bundle validation failed"}

Write-Host "`n=== Ruff ===" -ForegroundColor Cyan
& $py -m ruff check "$root\src" "$root\tests" `
    "$root\scripts\validate_contract_bundle.py" `
    "$root\scripts\preflight_hayes_verify_repository.py" `
    "$root\scripts\certify_hayes_verify_initial_baseline.py" `
    "$root\scripts\validate_hayes_verify_initial_baseline.py"
if($LASTEXITCODE){Fail "Ruff failed"}

if(Test-Path $pytestTemp){
    Remove-Item $pytestTemp -Recurse -Force -ErrorAction SilentlyContinue
}
New-Item -ItemType Directory -Force -Path $pytestTemp | Out-Null

Write-Host "`n=== Deterministic pytest ===" -ForegroundColor Cyan
& $py -m pytest --basetemp="$pytestTemp" -q "$root\tests"
if($LASTEXITCODE){Fail "pytest failed"}

Write-Host "`nPASS: Hayes Verify pre-publication certification gates passed." -ForegroundColor Green
