[CmdletBinding()]
param([string]$EMSPath = "C:\temp\standars\ems")

$ErrorActionPreference = "Stop"
$here = Split-Path -Parent $MyInvocation.MyCommand.Path

Copy-Item `
    (Join-Path $here "Publish-Wave2BPostMergeRelease.ps1") `
    (Join-Path $EMSPath "scripts\Publish-Wave2BPostMergeRelease.ps1") `
    -Force

$tokens=$null
$errors=$null

[System.Management.Automation.Language.Parser]::ParseFile(
    (Join-Path $EMSPath "scripts\Publish-Wave2BPostMergeRelease.ps1"),
    [ref]$tokens,
    [ref]$errors
) | Out-Null

if($errors.Count -gt 0){
    $errors | Format-List
    throw "Publish-Wave2BPostMergeRelease.ps1 parser validation failed."
}

Write-Host "Wave 2B Post-Merge Release Certification tooling installed." -ForegroundColor Green
