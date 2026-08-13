[CmdletBinding()]
param([string]$Destination = "C:\temp\t4\scripts")

$ErrorActionPreference = "Stop"
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
New-Item -ItemType Directory -Path $Destination -Force | Out-Null

Copy-Item `
    (Join-Path $here "Bootstrap-Wave2C.ps1") `
    (Join-Path $Destination "Bootstrap-Wave2C.ps1") `
    -Force

$tokens=$null
$errors=$null
[System.Management.Automation.Language.Parser]::ParseFile(
    (Join-Path $Destination "Bootstrap-Wave2C.ps1"),
    [ref]$tokens,
    [ref]$errors
) | Out-Null

if($errors.Count -gt 0){
    $errors | Format-List
    throw "Bootstrap-Wave2C.ps1 parser validation failed."
}

Write-Host "PASS: Wave 2C bootstrap fix installed to $Destination" -ForegroundColor Green
