[CmdletBinding()]
param([string]$EMSPath="C:\temp\standars\ems")

$runner=Join-Path $EMSPath "scripts\Run-Wave2B1-Inheritance.ps1"
if(-not(Test-Path $runner)){ throw "Runner not found: $runner" }

$text=Get-Content $runner -Raw

$checks=[ordered]@{
    HasMaterializedInputPath = $text.Contains('releases\wave1-input')
    SearchesBaselineZip      = $text.Contains('*Wave1*Baseline*.zip')
    SearchesPass45Fallback   = $text.Contains('$Pass45')
    PrintsSelectedBaseline   = $text.Contains('Using Wave 1 compliance baseline:')
}

$rows=$checks.GetEnumerator()|ForEach-Object{
    [pscustomobject]@{Check=$_.Key;Pass=[bool]$_.Value}
}
$rows|Format-Table -AutoSize

if(@($rows|Where-Object{-not $_.Pass}).Count -gt 0){
    throw "Wave 2B.1 baseline discovery patch validation failed."
}

Write-Host "PASS: Wave 2B.1 baseline discovery patch installed." -ForegroundColor Green
