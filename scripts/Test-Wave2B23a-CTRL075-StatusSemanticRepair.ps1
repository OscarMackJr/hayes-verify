[CmdletBinding()]
param([string]$EMSPath="C:\temp\standars\ems")

$ErrorActionPreference="Stop"
$collector=Join-Path $EMSPath "scripts\collectors\higher-scope\Collect-HSContinuousCompliance.py"
$text=Get-Content $collector -Raw

$checks=[ordered]@{
    DefinesStatusFunction      = $text -match '(?m)^\s*def\s+status\s*\('
    UsesRowStatusLocal         = $text -match '\brow_status\b'
    ReadsCanonicalStatusField  = $text -match 'r\.get\("status"\)'
    CallsStatusFunction        = $text -match '\bst\s*=\s*status\s*\(\s*A\s*\)'
    SerializesCanonicalStatus  = $text -match '"status"\s*:\s*st'
    ReportReadsCanonicalStatus = $text -match 'e\["status"\]'
    NoCollectorStatusToken     = -not ($text -match '\bcollector_status\b')
}

$rows=$checks.GetEnumerator()|ForEach-Object{
    [pscustomobject]@{Check=$_.Key;Pass=[bool]$_.Value}
}
$rows|Format-Table -AutoSize

if(@($rows|Where-Object{-not $_.Pass}).Count -gt 0){
    throw "CTRL-075/076 semantic status validation failed."
}

$py=Join-Path $EMSPath ".venv\Scripts\python.exe"
if(-not(Test-Path $py)){$py="python"}

& $py -m py_compile $collector
if($LASTEXITCODE-ne 0){ throw "Collector Python compile failed." }

Write-Host "PASS: canonical status contract restored." -ForegroundColor Green
