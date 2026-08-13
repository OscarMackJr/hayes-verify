[CmdletBinding()]
param(
    [string]$EMSPath = "C:\temp\standars\ems"
)

$ErrorActionPreference = "Stop"

$runner = Join-Path $EMSPath "scripts\Run-Wave2B1-Inheritance.ps1"

if(-not(Test-Path $runner)){
    throw "Wave 2B.1 runner not found: $runner"
}

Copy-Item $runner "$runner.pre-pass45-param-fix.bak" -Force

$text = Get-Content $runner -Raw

# Patch only the runner's top-level param block.
$old = @'
[CmdletBinding()]
param(
    [string]$EMSPath="C:\temp\standars\ems"
)
'@

$oldSpaced = @'
[CmdletBinding()]
param(
    [string]$EMSPath = "C:\temp\standars\ems"
)
'@

$new = @'
[CmdletBinding()]
param(
    [string]$EMSPath = "C:\temp\standars\ems",
    [string]$Pass45 = "C:\temp\standars\Pass4_5"
)
'@

if($text.Contains($old)){
    $text = $text.Replace($old,$new)
}
elseif($text.Contains($oldSpaced)){
    $text = $text.Replace($oldSpaced,$new)
}
elseif($text -match '\$Pass45\s*='){
    Write-Host "Pass45 parameter already present; no param-block change required." -ForegroundColor Yellow
}
else {
    throw "Expected Wave 2B.1 param block not found. No changes applied."
}

Set-Content $runner $text -Encoding UTF8

Write-Host "Wave 2B.1 Pass45 parameter fix installed." -ForegroundColor Green
Write-Host "Backup:"
Write-Host "  $runner.pre-pass45-param-fix.bak"
