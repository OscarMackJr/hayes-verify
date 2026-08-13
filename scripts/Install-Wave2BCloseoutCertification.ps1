[CmdletBinding()]
param([string]$EMSPath="C:\temp\standars\ems")

$ErrorActionPreference="Stop"
$here=Split-Path -Parent $MyInvocation.MyCommand.Path

foreach($name in @(
    "Certify-Wave2B.py",
    "Freeze-Wave2BArtifacts.py",
    "Run-Wave2BCloseoutCertification.ps1",
    "Show-Wave2BCloseoutCertification.ps1",
    "Prepare-Wave2BBranch.ps1"
)){
    Copy-Item (Join-Path $here $name) (Join-Path $EMSPath "scripts\$name") -Force
}

$py=Join-Path $EMSPath ".venv\Scripts\python.exe"
if(-not(Test-Path $py)){$py="python"}

foreach($name in @("Certify-Wave2B.py","Freeze-Wave2BArtifacts.py")){
    & $py -m py_compile (Join-Path $EMSPath "scripts\$name")
    if($LASTEXITCODE-ne 0){throw "Python syntax validation failed: $name"}
}

foreach($name in @(
    "Run-Wave2BCloseoutCertification.ps1",
    "Show-Wave2BCloseoutCertification.ps1",
    "Prepare-Wave2BBranch.ps1"
)){
    $tokens=$null;$errors=$null
    [System.Management.Automation.Language.Parser]::ParseFile(
        (Join-Path $EMSPath "scripts\$name"),
        [ref]$tokens,
        [ref]$errors
    )|Out-Null
    if($errors.Count -gt 0){
        $errors|Format-List
        throw "PowerShell parser validation failed: $name"
    }
}

Write-Host "Wave 2B Closeout & Certification tooling installed." -ForegroundColor Green
