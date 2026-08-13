[CmdletBinding()]
param([string]$HayesPath="C:\temp\standars\hayes-verify")
$ErrorActionPreference="Stop"
function Fail([string]$m){throw "HAYES VERIFY LIVE CERTIFICATION BLOCKED: $m"}

$root=(Resolve-Path $HayesPath).Path
$py=Join-Path $root ".venv\Scripts\python.exe"
$spec=Join-Path $root "registry\hayes_verify_live_evaluation_certification_spec.json"
$schema=Join-Path $root "schemas\hayes_verify_ems_return_envelope.schema.json"
$pytestTemp=Join-Path $root ".pytest-temp"

if(-not(Test-Path $py)){Fail "venv Python missing: $py"}

Write-Host "=== Ruff preflight ===" -ForegroundColor Cyan
& $py -m ruff check "$root\src" "$root\tests"
if($LASTEXITCODE){Fail "Ruff failed"}

if(Test-Path $pytestTemp){Remove-Item $pytestTemp -Recurse -Force -ErrorAction SilentlyContinue}
New-Item -ItemType Directory -Force -Path $pytestTemp|Out-Null
Write-Host "`n=== Deterministic pytest preflight ===" -ForegroundColor Cyan
& $py -m pytest --basetemp="$pytestTemp" -q "$root\tests"
if($LASTEXITCODE){Fail "Pytest failed"}

Write-Host "`n=== Certify live evaluation ===" -ForegroundColor Cyan
& $py "$root\scripts\Certify-HayesVerifyLiveEvaluation.py" --root $root --spec $spec
if($LASTEXITCODE){Fail "Live certification failed"}

Write-Host "`n=== Build EMS return envelope ===" -ForegroundColor Cyan
& $py "$root\scripts\Build-HayesVerifyEMSReturnEnvelope.py" --root $root --spec $spec --schema $schema
if($LASTEXITCODE){Fail "Envelope build failed"}

Write-Host "`n=== Validate EMS return envelope ===" -ForegroundColor Cyan
& $py "$root\scripts\Validate-HayesVerifyEMSReturnEnvelope.py" --root $root --spec $spec --schema $schema
if($LASTEXITCODE){Fail "Envelope validation failed"}

Write-Host "PASS: live evaluation certified and EMS return envelope generated." -ForegroundColor Green
Write-Host "acceptance_state = PENDING_EMS_ACCEPTANCE"
Write-Host "promotion_state = NOT_PROMOTED"
