[CmdletBinding()]
param([string]$EMSPath="C:\temp\standars\ems")
$ErrorActionPreference="Stop"
$here=Split-Path -Parent $MyInvocation.MyCommand.Path

Copy-Item (Join-Path $here "Assess-Wave2DRepositoryContent-v2.py") `
          (Join-Path $EMSPath "scripts\Assess-Wave2DRepositoryContent-v2.py") -Force

Copy-Item (Join-Path $here "Run-Wave2DRepositoryContentAssessment-v2.ps1") `
          (Join-Path $EMSPath "scripts\Run-Wave2DRepositoryContentAssessment-v2.ps1") -Force

Write-Host "Wave 2D Repository Content Assessment Performance & Progress Hotfix installed." -ForegroundColor Green
