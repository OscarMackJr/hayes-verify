[CmdletBinding()]
param([string]$EMSPath="C:\temp\standars\ems")

$ErrorActionPreference="Stop"
$here=Split-Path -Parent $MyInvocation.MyCommand.Path

foreach($name in @(
    "Rerun-Wave2BCloseoutSemanticReconciliation.ps1"
)){
    Copy-Item (Join-Path $here $name) (Join-Path $EMSPath "scripts\$name") -Force
}

$tokens=$null
$errors=$null
[System.Management.Automation.Language.Parser]::ParseFile(
    (Join-Path $EMSPath "scripts\Rerun-Wave2BCloseoutSemanticReconciliation.ps1"),
    [ref]$tokens,
    [ref]$errors
) | Out-Null

if($errors.Count -gt 0){
    $errors | Format-List
    throw "PowerShell parser validation failed for rerun script."
}

Write-Host "PASS: Missing Wave 2B semantic-reconciliation rerun script installed." -ForegroundColor Green
