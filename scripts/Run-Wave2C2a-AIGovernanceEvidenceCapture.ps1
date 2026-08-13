[CmdletBinding()]
param([string]$EMSPath="C:\temp\standars\ems")
$ErrorActionPreference="Stop"
$root=(Resolve-Path $EMSPath).Path
$python = if($env:VIRTUAL_ENV -and (Test-Path (Join-Path $env:VIRTUAL_ENV "Scripts\python.exe"))){
    Join-Path $env:VIRTUAL_ENV "Scripts\python.exe"
}elseif(Test-Path (Join-Path $root ".venv\Scripts\python.exe")){
    Join-Path $root ".venv\Scripts\python.exe"
}else{(Get-Command python).Source}

$out=Join-Path $root "generated\wave2c\ai-governance"
New-Item -ItemType Directory -Force -Path $out | Out-Null

Write-Host "=== Wave 2C.2a validate AI governance operating registers ==="
& $python (Join-Path $root "scripts\Validate-Wave2C2a-AIGovernanceRegisters.py") `
    --root $root `
    --report (Join-Path $out "register_validation.json")
if($LASTEXITCODE){throw "AI governance register validation failed."}

Write-Host "`n=== Re-run Wave 2C.2 AI governance qualification ==="
& (Join-Path $root "scripts\Run-Wave2C2-AIGovernance.ps1")
if($LASTEXITCODE){throw "Wave 2C.2 requalification failed."}

Write-Host "`nPASS: Wave 2C.2a evidence capture/requalification complete. No evidence promoted."
