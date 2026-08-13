[CmdletBinding()]
param([string]$EMSPath="C:\temp\standars\ems")

$ErrorActionPreference="Stop"
$here=Split-Path -Parent $MyInvocation.MyCommand.Path
$pkg=Split-Path -Parent $here

Copy-Item `
    "$pkg\registry\wave2c1b_ctrl072_reconciliation_spec.json" `
    "$EMSPath\registry\wave2c1b_ctrl072_reconciliation_spec.json" `
    -Force

Copy-Item `
    "$pkg\schemas\wave2c1b_ctrl072_reconciliation.schema.json" `
    "$EMSPath\schemas\wave2c1b_ctrl072_reconciliation.schema.json" `
    -Force

foreach($n in @(
    "Reconcile-Wave2C1b-CTRL072.py",
    "Validate-Wave2C1b-CTRL072.py",
    "Update-Wave2C1b-QualifiedQueue.py",
    "Run-Wave2C1b-CTRL072.ps1",
    "Show-Wave2C1b-CTRL072.ps1"
)){
    Copy-Item (Join-Path $here $n) (Join-Path $EMSPath "scripts\$n") -Force
}

$py=$null
if($env:VIRTUAL_ENV){
    $candidate=Join-Path $env:VIRTUAL_ENV "Scripts\python.exe"
    if(Test-Path $candidate){$py=$candidate}
}
if(-not $py){
    $cmd=Get-Command python -ErrorAction SilentlyContinue
    if($cmd){$py=$cmd.Source}
}
if(-not $py){throw "No usable Python interpreter found for syntax validation."}

foreach($n in @(
    "Reconcile-Wave2C1b-CTRL072.py",
    "Validate-Wave2C1b-CTRL072.py",
    "Update-Wave2C1b-QualifiedQueue.py"
)){
    & $py -m py_compile (Join-Path $EMSPath "scripts\$n")
    if($LASTEXITCODE-ne 0){ throw "Python syntax validation failed: $n" }
}

foreach($n in @(
    "Run-Wave2C1b-CTRL072.ps1",
    "Show-Wave2C1b-CTRL072.ps1"
)){
    $tokens=$null
    $errors=$null
    [System.Management.Automation.Language.Parser]::ParseFile(
        (Join-Path $EMSPath "scripts\$n"),
        [ref]$tokens,
        [ref]$errors
    ) | Out-Null

    if($errors.Count -gt 0){
        $errors | Format-List
        throw "PowerShell parser validation failed: $n"
    }
}

Write-Host "Wave 2C.1b CTRL-072 reconciliation tooling installed." -ForegroundColor Green
