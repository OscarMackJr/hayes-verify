[CmdletBinding()]
param([string]$HayesPath="C:\temp\standars\hayes-verify")
$ErrorActionPreference="Stop"
function Fail([string]$m){throw "HAYES CTRL-010 CERTIFICATION BLOCKED: $m"}
$root=(Resolve-Path $HayesPath).Path
$py=Join-Path $root ".venv\Scripts\python.exe"
$spec=Join-Path $root "registry\ctrl010_pilot_spec.json"
$schema=Join-Path $root "schemas\ctrl010_ems_return_envelope.schema.json"
$pytestTemp=Join-Path $root ".pytest-temp"
& $py -m ruff check "$root\src" "$root\tests"
if($LASTEXITCODE){Fail "Ruff failed"}
if(Test-Path $pytestTemp){Remove-Item $pytestTemp -Recurse -Force -ErrorAction SilentlyContinue}
New-Item -ItemType Directory -Force -Path $pytestTemp|Out-Null
& $py -m pytest --basetemp="$pytestTemp" -q "$root\tests"
if($LASTEXITCODE){Fail "pytest failed"}
& $py "$root\scripts\certify_ctrl010_live.py" --root $root --spec $spec
if($LASTEXITCODE){Fail "certification failed"}
& $py "$root\scripts\build_ctrl010_return_envelope.py" --root $root --spec $spec --schema $schema
if($LASTEXITCODE){Fail "envelope build failed"}
& $py "$root\scripts\validate_ctrl010_return_envelope.py" --root $root --spec $spec --schema $schema
if($LASTEXITCODE){Fail "envelope validation failed"}
Write-Host "PASS: CTRL-010 live evaluation certified and EMS return envelope generated." -ForegroundColor Green
