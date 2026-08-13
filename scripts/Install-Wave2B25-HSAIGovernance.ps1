param(
    [string]$EMSPath = "C:\temp\standars\ems"
)
$ErrorActionPreference="Stop"
$Pkg=(Resolve-Path (Join-Path $PSScriptRoot "..")).Path
if(-not (Test-Path $EMSPath)){ throw "EMS path not found: $EMSPath" }
New-Item -ItemType Directory -Force -Path (Join-Path $EMSPath "scripts\collectors\higher-scope") | Out-Null
Copy-Item (Join-Path $Pkg "scripts\Run-Wave2B25-HSAIGovernance.ps1") (Join-Path $EMSPath "scripts") -Force
Copy-Item (Join-Path $Pkg "scripts\Show-Wave2B25-HSAIGovernance.ps1") (Join-Path $EMSPath "scripts") -Force
Copy-Item (Join-Path $Pkg "scripts\Validate-HSAIGovernance.py") (Join-Path $EMSPath "scripts") -Force
Copy-Item (Join-Path $Pkg "scripts\Qualify-HSAIGovernance.py") (Join-Path $EMSPath "scripts") -Force
Copy-Item (Join-Path $Pkg "scripts\Promote-HSAIGovernance.py") (Join-Path $EMSPath "scripts") -Force
Copy-Item (Join-Path $Pkg "scripts\collectors\higher-scope\Collect-HSAIGovernance.py") (Join-Path $EMSPath "scripts\collectors\higher-scope") -Force
Write-Host "Wave 2B.2.5 HS-AI-GOVERNANCE tooling installed."
Write-Host "Next:"
Write-Host "  cd $EMSPath"
Write-Host "  .\scripts\Run-Wave2B25-HSAIGovernance.ps1"
Write-Host "  .\scripts\Show-Wave2B25-HSAIGovernance.ps1"
Write-Host "  # only after review:"
Write-Host "  .\scripts\Run-Wave2B25-HSAIGovernance.ps1 -Promote"
