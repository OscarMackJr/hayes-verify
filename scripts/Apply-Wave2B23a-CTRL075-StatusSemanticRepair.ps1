[CmdletBinding()]
param([string]$EMSPath="C:\temp\standars\ems")

$ErrorActionPreference="Stop"
$collector=Join-Path $EMSPath "scripts\collectors\higher-scope\Collect-HSContinuousCompliance.py"

if(-not(Test-Path $collector)){ throw "Collector not found: $collector" }

$stamp=Get-Date -Format "yyyyMMdd-HHmmss"
$backup="$collector.pre-status-semantic-repair-$stamp.bak"
Copy-Item $collector $backup -Force

$text=Get-Content $collector -Raw

# 1. Repair the CSV-local status variable only.
$text=$text.Replace(
    'collector_status =(r.get("compliance_status") or r.get("effective_status") or r.get("collector_status") or "").strip()',
    'row_status=(r.get("compliance_status") or r.get("effective_status") or r.get("status") or "").strip()'
)
$text=$text.Replace(
    'if collector_status and collector_status != "NOT_APPLICABLE":',
    'if row_status and row_status != "NOT_APPLICABLE":'
)

# 2. Restore semantic field names / messages changed by the broad hotfix.
$text=$text.Replace('"reviewer_decision","collector_status","owner"', '"reviewer_decision","status","owner"')
$text=$text.Replace(
    '"Tracking structure includes collector_status/disposition/remediation semantics."',
    '"Tracking structure includes status/disposition/remediation semantics."'
)
$text=$text.Replace(
    '"notes":"Open findings do not fail CTRL-076 when ownership/collector_status/history remain controlled and traceable."',
    '"notes":"Open findings do not fail CTRL-076 when ownership/status/history remain controlled and traceable."'
)

# 3. Restore the evidence-envelope contract.
$text=$text.Replace('"collector_status":st', '"status":st')

# 4. Restore report aggregation to the canonical envelope key.
$text=$text.Replace(
    'report["status_counts"][e["collector_status"]]=report["status_counts"].get(e["collector_status"],0)+1',
    'report["status_counts"][e["status"]]=report["status_counts"].get(e["status"],0)+1'
)

Set-Content $collector $text -Encoding UTF8

$py=Join-Path $EMSPath ".venv\Scripts\python.exe"
if(-not(Test-Path $py)){$py="python"}

& $py -m py_compile $collector
if($LASTEXITCODE-ne 0){
    Copy-Item $backup $collector -Force
    throw "Python compile failed; original restored."
}

$verify=Get-Content $collector -Raw

$checks=[ordered]@{
    DefinesStatusFunction      = $verify -match '(?m)^\s*def\s+status\s*\('
    UsesRowStatusLocal         = $verify -match '\brow_status\b'
    ReadsCanonicalStatusField  = $verify -match 'r\.get\("status"\)'
    CallsStatusFunction        = $verify -match '\bst\s*=\s*status\s*\(\s*A\s*\)'
    SerializesCanonicalStatus  = $verify -match '"status"\s*:\s*st'
    ReportReadsCanonicalStatus = $verify -match 'e\["status"\]'
    NoCollectorStatusToken     = -not ($verify -match '\bcollector_status\b')
}

$rows=$checks.GetEnumerator()|ForEach-Object{
    [pscustomobject]@{Check=$_.Key;Pass=[bool]$_.Value}
}
$rows|Format-Table -AutoSize

if(@($rows|Where-Object{-not $_.Pass}).Count -gt 0){
    Copy-Item $backup $collector -Force
    throw "Status semantic repair validation failed; original restored."
}

Write-Host "PASS: CTRL-075/076 status semantics repaired." -ForegroundColor Green
Write-Host "Backup: $backup"
