[CmdletBinding()]
param([string]$EMSPath="C:\temp\standars\ems")

$ErrorActionPreference="Stop"
$collector=Join-Path $EMSPath "scripts\collectors\higher-scope\Collect-HSContinuousCompliance.py"
if(-not(Test-Path $collector)){ throw "Collector not found: $collector" }

$stamp=Get-Date -Format "yyyyMMdd-HHmmss"
$backup="$collector.pre-envelope-key-hotfix-v2-$stamp.bak"
Copy-Item $collector $backup -Force

$text=Get-Content $collector -Raw
$before=$text

$text=[regex]::Replace($text, '(["''])(collector_status)\1\s*:', '"status":')
$text=$text.Replace('["collector_status"]','["status"]')
$text=$text.Replace("['collector_status']","['status']")

if($text -notmatch '(?m)^\s*collector_status\s*=\s*status\s*\(\s*A\s*\)'){
    Copy-Item $backup $collector -Force
    throw "Expected collector_status = status(A) assignment not found; original restored."
}

if($text -eq $before){
    if(-not ($text -match '(["''])status\1\s*:\s*collector_status')){
        Copy-Item $backup $collector -Force
        throw "No repair made and correct status envelope key not found; original restored."
    }
}

Set-Content $collector $text -Encoding UTF8

$py=Join-Path $EMSPath ".venv\Scripts\python.exe"
if(-not(Test-Path $py)){$py="python"}
& $py -m py_compile $collector
if($LASTEXITCODE-ne 0){
    Copy-Item $backup $collector -Force
    throw "Collector compile failed; original restored."
}

$verify=Get-Content $collector -Raw
$checks=[ordered]@{
    DefinesStatusFunction        = $verify -match '(?m)^\s*def\s+status\s*\('
    UsesCollectorStatusVariable  = $verify -match '(?m)^\s*collector_status\s*=\s*status\s*\(\s*A\s*\)'
    SerializesStatusKey          = $verify -match '(["''])status\1\s*:\s*collector_status'
    NoCollectorStatusKey         = -not ($verify -match '(["''])collector_status\1\s*:')
    NoStatusAssignmentShadow     = -not ($verify -match '(?m)^\s*status\s*=(?!=)')
}
$failed=@($checks.GetEnumerator()|Where-Object{-not $_.Value})
if($failed.Count -gt 0){
    Copy-Item $backup $collector -Force
    $checks.GetEnumerator()|ForEach-Object{[pscustomobject]@{Check=$_.Key;Pass=[bool]$_.Value}}|Format-Table -AutoSize
    throw "Envelope-key v2 validation failed; original restored."
}

Write-Host "PASS: CTRL-075 envelope key repaired." -ForegroundColor Green
Write-Host "Backup: $backup"
