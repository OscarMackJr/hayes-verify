[CmdletBinding()]
param(
    [string]$EMSPath="C:\temp\standars\ems",
    [switch]$InstallDependencies
)

$ErrorActionPreference="Stop"

function Fail([string]$m){ throw "WAVE 2C.1a PREFLIGHT BLOCKED: $m" }

Write-Host "=== Wave 2C.1a dependency/runtime preflight ===" -ForegroundColor Cyan

# Prefer the active virtual environment, then PATH python, then EMS-local venv.
$python = $null

if($env:VIRTUAL_ENV){
    $candidate = Join-Path $env:VIRTUAL_ENV "Scripts\python.exe"
    if(Test-Path $candidate){ $python = $candidate }
}

if(-not $python){
    $cmd = Get-Command python -ErrorAction SilentlyContinue
    if($cmd){ $python = $cmd.Source }
}

if(-not $python){
    $candidate = Join-Path $EMSPath ".venv\Scripts\python.exe"
    if(Test-Path $candidate){ $python = $candidate }
}

if(-not $python){ Fail "No usable Python interpreter found." }

Write-Host "Python: $python"
& $python -c "import sys; print(sys.executable)"
if($LASTEXITCODE-ne 0){ Fail "Python interpreter cannot execute." }

& $python -c "import docx" 2>$null
$hasDocx = ($LASTEXITCODE -eq 0)

if(-not $hasDocx -and $InstallDependencies){
    Write-Host "Installing python-docx into active interpreter..." -ForegroundColor Yellow
    & $python -m pip install python-docx
    if($LASTEXITCODE-ne 0){ Fail "python-docx installation failed." }

    & $python -c "import docx"
    $hasDocx = ($LASTEXITCODE -eq 0)
}

$soffice = $null
foreach($name in @("soffice","libreoffice")){
    $cmd = Get-Command $name -ErrorAction SilentlyContinue
    if($cmd){ $soffice=$cmd.Source; break }
}

# Common Windows LibreOffice locations.
if(-not $soffice){
    foreach($candidate in @(
        "C:\Program Files\LibreOffice\program\soffice.exe",
        "C:\Program Files (x86)\LibreOffice\program\soffice.exe"
    )){
        if(Test-Path $candidate){ $soffice=$candidate; break }
    }
}

$report = [ordered]@{
    python               = $python
    python_docx_available = $hasDocx
    libreoffice          = $soffice
    libreoffice_available = [bool]$soffice
    status               = if($hasDocx -and $soffice){"PASS"}else{"FAIL"}
}

$report | ConvertTo-Json | Write-Host

$runtimeDir = Join-Path $EMSPath "generated\wave2c\ctrl072-generation"
New-Item -ItemType Directory -Path $runtimeDir -Force | Out-Null
$report | ConvertTo-Json | Set-Content (Join-Path $runtimeDir "runtime_preflight.json") -Encoding UTF8

if(-not $hasDocx){
    Fail "python-docx is unavailable. Re-run with -InstallDependencies."
}
if(-not $soffice){
    Fail "LibreOffice/soffice is unavailable. Install LibreOffice or add soffice.exe to PATH."
}

Write-Host "PASS: Wave 2C.1a runtime preflight succeeded." -ForegroundColor Green

[pscustomobject]@{
    Python=$python
    Soffice=$soffice
}
