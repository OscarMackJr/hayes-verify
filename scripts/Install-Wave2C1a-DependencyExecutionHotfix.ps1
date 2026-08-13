[CmdletBinding()]
param([string]$EMSPath="C:\temp\standars\ems")

$ErrorActionPreference="Stop"
$here=Split-Path -Parent $MyInvocation.MyCommand.Path

foreach($n in @(
    "Test-Wave2C1a-Runtime.ps1",
    "Patch-Wave2C1a-GeneratorRuntime.ps1",
    "Run-Wave2C1a-DocumentGeneration-v2.ps1",
    "Show-Wave2C1a-DocumentGeneration-v2.ps1"
)){
    Copy-Item (Join-Path $here $n) (Join-Path $EMSPath "scripts\$n") -Force
}

foreach($n in @(
    "Test-Wave2C1a-Runtime.ps1",
    "Patch-Wave2C1a-GeneratorRuntime.ps1",
    "Run-Wave2C1a-DocumentGeneration-v2.ps1",
    "Show-Wave2C1a-DocumentGeneration-v2.ps1"
)){
    $t=$null;$e=$null
    [System.Management.Automation.Language.Parser]::ParseFile(
        (Join-Path $EMSPath "scripts\$n"),
        [ref]$t,[ref]$e
    )|Out-Null
    if($e.Count-gt 0){$e|Format-List;throw "PowerShell parser validation failed: $n"}
}

Write-Host "Wave 2C.1a dependency/execution hotfix installed." -ForegroundColor Green
