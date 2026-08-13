[CmdletBinding()]
param([string]$EMSPath="C:\temp\standars\ems")
$ErrorActionPreference="Stop"

$root=(Resolve-Path $EMSPath).Path
$py = if($env:VIRTUAL_ENV -and (Test-Path (Join-Path $env:VIRTUAL_ENV "Scripts\python.exe"))){
    Join-Path $env:VIRTUAL_ENV "Scripts\python.exe"
}elseif(Test-Path (Join-Path $root ".venv\Scripts\python.exe")){
    Join-Path $root ".venv\Scripts\python.exe"
}else{(Get-Command python).Source}

$out=Join-Path $root "generated\wave2c\data-governance"
New-Item -ItemType Directory -Force -Path $out|Out-Null

Write-Host "=== Wave 2C.3 initialize data-governance registers ==="
& $py (Join-Path $root "scripts\Initialize-Wave2C3DataGovernanceRegisters.py") --root $root
if($LASTEXITCODE){throw "Register initialization failed."}

Write-Host "`n=== Validate data-governance registers ==="
& $py (Join-Path $root "scripts\Validate-Wave2C3DataGovernanceRegisters.py") `
    --root $root `
    --report (Join-Path $out "register_validation.json")
if($LASTEXITCODE){throw "Data-governance register validation failed."}

Write-Host "`n=== Qualify data-governance controls ==="
& $py (Join-Path $root "scripts\Qualify-Wave2C3DataGovernance.py") --root $root
if($LASTEXITCODE){throw "Data-governance qualification failed."}

Write-Host "`nPASS: Wave 2C.3 complete. No evidence promoted."
