[CmdletBinding()]
param([string]$EMSPath="C:\temp\standars\ems")

$ErrorActionPreference="Stop"
$here=Split-Path -Parent $MyInvocation.MyCommand.Path

foreach($name in @(
    "Run-Wave2B26b-SDGFamilyCloseout.ps1",
    "Show-Wave2B26b-SDGFamilyCloseout.ps1"
)){
    Copy-Item (Join-Path $here $name) (Join-Path $EMSPath "scripts\$name") -Force
}

foreach($name in @(
    "Run-Wave2B26b-SDGFamilyCloseout.ps1",
    "Show-Wave2B26b-SDGFamilyCloseout.ps1"
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

Write-Host "Wave 2B.2.6b Security & Data Governance family-closeout tooling installed." -ForegroundColor Green
