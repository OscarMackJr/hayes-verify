[CmdletBinding()]
param([string]$EMSPath = "C:\temp\standars\ems")

$ErrorActionPreference = "Stop"
$here = Split-Path -Parent $MyInvocation.MyCommand.Path

foreach($name in @(
    "Close-Wave2BBranch.ps1",
    "Patch-FinalizeWave2B-BranchStaging.ps1"
)){
    Copy-Item (Join-Path $here $name) (Join-Path $EMSPath "scripts\$name") -Force
}

foreach($name in @(
    "Close-Wave2BBranch.ps1",
    "Patch-FinalizeWave2B-BranchStaging.ps1"
)){
    $tokens=$null
    $errors=$null
    [System.Management.Automation.Language.Parser]::ParseFile(
        (Join-Path $EMSPath "scripts\$name"),
        [ref]$tokens,
        [ref]$errors
    ) | Out-Null

    if($errors.Count -gt 0){
        $errors | Format-List
        throw "PowerShell parser validation failed: $name"
    }
}

Write-Host "Wave2B Branch Closeout Patch installed." -ForegroundColor Green
