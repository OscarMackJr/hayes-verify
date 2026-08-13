[CmdletBinding()]
param([string]$EMSPath = "C:\temp\standars\ems")

$ErrorActionPreference = "Stop"
$here = Split-Path -Parent $MyInvocation.MyCommand.Path

$src = Join-Path $here "Finalize-Wave2B.ps1"
$dest = Join-Path $EMSPath "scripts\Finalize-Wave2B.ps1"

Copy-Item $src $dest -Force

$tokens = $null
$errors = $null
[System.Management.Automation.Language.Parser]::ParseFile(
    $dest,
    [ref]$tokens,
    [ref]$errors
) | Out-Null

if($errors.Count -gt 0){
    $errors | Format-List
    throw "Finalize-Wave2B.ps1 failed PowerShell parser validation."
}

Write-Host "PASS: Wave 2B finalization script installed." -ForegroundColor Green
