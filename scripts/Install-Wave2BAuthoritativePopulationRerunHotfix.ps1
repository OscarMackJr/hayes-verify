[CmdletBinding()]
param([string]$EMSPath="C:\temp\standars\ems")

$ErrorActionPreference="Stop"
$here=Split-Path -Parent $MyInvocation.MyCommand.Path

$src=Join-Path $here "Rerun-Wave2BAuthoritativePopulationHotfix.ps1"
$dest=Join-Path $EMSPath "scripts\Rerun-Wave2BAuthoritativePopulationHotfix.ps1"

Copy-Item $src $dest -Force

$tokens=$null
$errors=$null
[System.Management.Automation.Language.Parser]::ParseFile(
    $dest,
    [ref]$tokens,
    [ref]$errors
) | Out-Null

if($errors.Count -gt 0){
    $errors | Format-List
    throw "PowerShell parser validation failed for authoritative-population rerun wrapper."
}

Write-Host "PASS: Missing Wave 2B authoritative-population rerun script installed." -ForegroundColor Green
