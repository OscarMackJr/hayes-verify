[CmdletBinding()]
param([string]$HayesPath="C:\temp\standars\hayes-verify")
$ErrorActionPreference="Stop"
function Fail([string]$m){throw "HAYES VERIFY SCAFFOLD CERTIFICATION BLOCKED: $m"}

$root=(Resolve-Path $HayesPath).Path
$spec="$root\registry\hayes_verify_scaffold_certification_spec.json"

Write-Host "=== Configure deterministic Windows pytest temp ===" -ForegroundColor Cyan
python "$root\scripts\Configure-HayesVerifyPytestBasetemp.py"
if($LASTEXITCODE){Fail "pytest basetemp configuration failed"}

New-Item -ItemType Directory -Force -Path "$root\.pytest-temp" | Out-Null

Write-Host "`n=== Certify Hayes Verify scaffold ===" -ForegroundColor Cyan
python "$root\scripts\Certify-HayesVerifyScaffold.py" --root $root --spec $spec
if($LASTEXITCODE){Fail "scaffold certification failed"}

Write-Host "`n=== Validate certification hashes ===" -ForegroundColor Cyan
python "$root\scripts\Validate-HayesVerifyScaffoldCertification.py" --root $root --spec $spec
if($LASTEXITCODE){Fail "scaffold certification validation failed"}

Write-Host "PASS: Hayes Verify Windows test determinism and scaffold certification complete." -ForegroundColor Green
