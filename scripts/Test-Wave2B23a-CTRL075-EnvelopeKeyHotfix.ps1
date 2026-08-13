[CmdletBinding()]
param([string]$EMSPath="C:\temp\standars\ems")

$ErrorActionPreference="Stop"
$collector=Join-Path $EMSPath "scripts\collectors\higher-scope\Collect-HSContinuousCompliance.py"
$text=Get-Content $collector -Raw

$checks=[ordered]@{
    DefinesStatusFunction       = $text -match '(?m)^\s*def\s+status\s*\('
    NoStatusAssignmentShadow    = -not ($text -match '(?m)^\s*status\s*=(?!=)')
    UsesCollectorStatusVariable = $text -match '\bcollector_status\b'
    SerializesStatusKey         = $text -match '"status"\s*:\s*collector_status'
    NoCollectorStatusKey        = -not ($text -match '["'']collector_status["'']\s*:')
}

$rows=$checks.GetEnumerator()|ForEach-Object{
    [pscustomobject]@{Check=$_.Key;Pass=[bool]$_.Value}
}
$rows|Format-Table -AutoSize

if(@($rows|Where-Object{-not $_.Pass}).Count -gt 0){
    throw "Envelope-key hotfix validation failed."
}

$py=Join-Path $EMSPath ".venv\Scripts\python.exe"
if(-not(Test-Path $py)){$py="python"}
& $py -m py_compile $collector
if($LASTEXITCODE-ne 0){throw "Collector Python compile failed."}

Write-Host "PASS: CTRL-075 collector preserves status() function, collector_status local variable, and status envelope key." -ForegroundColor Green
