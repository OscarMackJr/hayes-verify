[CmdletBinding()]
param([string]$EMSPath="C:\temp\standars\ems")

$ErrorActionPreference="Stop"
$pkg=Split-Path -Parent $PSScriptRoot

Copy-Item "$pkg\registry\authoritative_scope_overrides.json" `
    "$EMSPath\registry\authoritative_scope_overrides.json" -Force

foreach($n in @(
    "Apply-AuthoritativeScopeOverrides.py",
    "Run-AuthoritativeScopeOverrides.ps1",
    "Show-AuthoritativeScopeOverrides.ps1"
)){
    Copy-Item "$pkg\scripts\$n" "$EMSPath\scripts\$n" -Force
}

$py=Join-Path $EMSPath ".venv\Scripts\python.exe"
if(-not(Test-Path $py)){$py="python"}

& $py -m py_compile "$EMSPath\scripts\Apply-AuthoritativeScopeOverrides.py"
if($LASTEXITCODE-ne 0){
    throw "Authoritative scope override script syntax validation failed."
}

Write-Host "Wave 2A.1 Authoritative Scope Override tooling installed." -ForegroundColor Green
