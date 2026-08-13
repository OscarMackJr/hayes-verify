[CmdletBinding()]
param([string]$EMSPath="C:\temp\standars\ems")

$ErrorActionPreference="Stop"
$here=Split-Path -Parent $MyInvocation.MyCommand.Path

foreach($n in @(
    "Reconcile-Wave2CCloseoutInheritanceStatus.ps1",
    "Test-Wave2CCloseoutInheritanceStatusReconciliation.ps1"
)){
    Copy-Item (Join-Path $here $n) (Join-Path $EMSPath "scripts\$n") -Force
}

Write-Host "Wave 2C Closeout Certification Inheritance-Status Reconciliation tooling installed." -ForegroundColor Green
