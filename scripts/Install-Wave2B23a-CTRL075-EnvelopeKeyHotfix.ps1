[CmdletBinding()]
param([string]$EMSPath="C:\temp\standars\ems")

$ErrorActionPreference="Stop"
$here=Split-Path -Parent $MyInvocation.MyCommand.Path
$dest=Join-Path $EMSPath "scripts"

foreach($name in @(
    "Apply-Wave2B23a-CTRL075-EnvelopeKeyHotfix.ps1",
    "Test-Wave2B23a-CTRL075-EnvelopeKeyHotfix.ps1",
    "Rerun-Wave2B23a-CTRL075-EnvelopeKeyHotfix.ps1"
)){
    Copy-Item (Join-Path $here $name) (Join-Path $dest $name) -Force
}

Write-Host "CTRL-075 envelope-key hotfix installed." -ForegroundColor Green
