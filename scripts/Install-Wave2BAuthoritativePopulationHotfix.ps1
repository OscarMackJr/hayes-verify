[CmdletBinding()]
param([string]$EMSPath="C:\temp\standars\ems")

$ErrorActionPreference="Stop"
$here=Split-Path -Parent $MyInvocation.MyCommand.Path
$dest=Join-Path $EMSPath "scripts\Certify-Wave2B.py"

if(Test-Path $dest){
    Copy-Item $dest "$dest.pre-authoritative-population-hotfix.bak" -Force
}

Copy-Item (Join-Path $here "Certify-Wave2B.py") $dest -Force
Copy-Item (Join-Path $here "Test-Wave2BAuthoritativePopulationHotfix.ps1") `
    (Join-Path $EMSPath "scripts\Test-Wave2BAuthoritativePopulationHotfix.ps1") -Force

& (Join-Path $EMSPath "scripts\Test-Wave2BAuthoritativePopulationHotfix.ps1") -EMSPath $EMSPath
if($LASTEXITCODE-ne 0){throw "Authoritative-population hotfix install validation failed."}

Write-Host "Wave 2B Closeout Authoritative-Population Hotfix installed." -ForegroundColor Green
