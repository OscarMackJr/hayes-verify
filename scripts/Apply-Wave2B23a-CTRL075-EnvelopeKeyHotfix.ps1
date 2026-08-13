[CmdletBinding()]
param([string]$EMSPath="C:\temp\standars\ems")

$ErrorActionPreference="Stop"
$collector=Join-Path $EMSPath "scripts\collectors\higher-scope\Collect-HSContinuousCompliance.py"

if(-not(Test-Path $collector)){
    throw "Collector not found: $collector"
}

$stamp=Get-Date -Format "yyyyMMdd-HHmmss"
$backup="$collector.pre-envelope-key-hotfix-$stamp.bak"
Copy-Item $collector $backup -Force

$text=Get-Content $collector -Raw

# Keep the local variable collector_status, but restore the serialized envelope key.
$replacements = @(
    @('"collector_status":collector_status', '"status":collector_status'),
    @("'collector_status':collector_status", "'status':collector_status"),
    @('"collector_status": collector_status', '"status": collector_status'),
    @("'collector_status': collector_status", "'status': collector_status")
)

$changed=$false
foreach($pair in $replacements){
    if($text.Contains($pair[0])){
        $text=$text.Replace($pair[0],$pair[1])
        $changed=$true
    }
}

# Also restore status key in any summary/status-count access accidentally renamed,
# while preserving the collector_status local variable itself.
$text = $text.Replace('e["collector_status"]','e["status"]')
$text = $text.Replace("e['collector_status']","e['status']")
$text = $text.Replace('r["collector_status"]','r["status"]')
$text = $text.Replace("r['collector_status']","r['status']")

if(-not $changed -and $text -notmatch '"status"\s*:\s*collector_status'){
    Copy-Item $backup $collector -Force
    throw "Expected envelope collector_status key not found; original restored."
}

Set-Content $collector $text -Encoding UTF8

$py=Join-Path $EMSPath ".venv\Scripts\python.exe"
if(-not(Test-Path $py)){$py="python"}

& $py -m py_compile $collector
if($LASTEXITCODE-ne 0){
    Copy-Item $backup $collector -Force
    throw "Collector compile failed; original restored."
}

Write-Host "PASS: evidence envelope status key restored." -ForegroundColor Green
Write-Host "Backup: $backup"
