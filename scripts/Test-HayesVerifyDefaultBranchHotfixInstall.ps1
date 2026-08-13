[CmdletBinding()]
param([string]$HayesPath="C:\temp\standars\hayes-verify")
$ErrorActionPreference="Stop"

$root=(Resolve-Path $HayesPath).Path
$py=Join-Path $root ".venv\Scripts\python.exe"
$runner=Join-Path $root "scripts\Test-HayesVerifyDefaultBranchHotfix.ps1"

if(-not(Test-Path $py)){
    throw "Hayes Verify venv Python not found: $py"
}

if(-not(Test-Path $runner)){
    throw "Default-branch validation runner missing: $runner"
}

Write-Host "PASS: deterministic pytest runner installation verified." -ForegroundColor Green
Write-Host "Venv Python: $py"
Write-Host "Pytest basetemp: $(Join-Path $root '.pytest-temp')"
