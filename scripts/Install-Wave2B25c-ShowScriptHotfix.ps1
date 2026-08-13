[CmdletBinding()]
param([string]$EMSPath="C:\temp\standars\ems")

$ErrorActionPreference="Stop"
$here=Split-Path -Parent $MyInvocation.MyCommand.Path

$src=Join-Path $here "Show-Wave2B25c-AIGovernanceOperatingRegisters.ps1"
$dest=Join-Path $EMSPath "scripts\Show-Wave2B25c-AIGovernanceOperatingRegisters.ps1"

if(Test-Path $dest){
    Copy-Item $dest "$dest.pre-show-hotfix.bak" -Force
}

Copy-Item $src $dest -Force

# PowerShell parser validation without executing the script.
$tokens=$null
$errors=$null
[System.Management.Automation.Language.Parser]::ParseFile(
    $dest,
    [ref]$tokens,
    [ref]$errors
) | Out-Null

if($errors.Count -gt 0){
    $errors | Format-List
    throw "Patched Show script failed PowerShell parser validation."
}

Write-Host "PASS: Wave 2B.2.5c Show script hotfix installed." -ForegroundColor Green
