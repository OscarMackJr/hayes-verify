[CmdletBinding()]
param([string]$EMSPath="C:\temp\standars\ems")
$ErrorActionPreference="Stop"
function Fail([string]$m){throw "WAVE 2C.1 BLOCKED: $m"}

$branch=(git -C $EMSPath branch --show-current).Trim()
if($branch-ne"feature/wave2c-remediation"){Fail "Expected feature/wave2c-remediation; current=$branch"}

$py=Join-Path $EMSPath ".venv\Scripts\python.exe"
if(-not(Test-Path $py)){$py="python"}

$out=Join-Path $EMSPath "generated\wave2c\ctrl072"
New-Item -ItemType Directory -Path $out -Force|Out-Null
$queue=Join-Path $EMSPath "generated\wave2c\remediation_queue.csv"
if(-not(Test-Path $queue)){Fail "Wave 2C remediation queue not found."}

Write-Host "=== Wave 2C.1 CTRL-072 collection ===" -ForegroundColor Cyan
& $py (Join-Path $EMSPath "scripts\Collect-Wave2C1-CTRL072.py") --ems-root $EMSPath --outdir $out
if($LASTEXITCODE-ne 0){Fail "CTRL-072 evidence collection failed."}

Write-Host "`n=== Validate CTRL-072 evidence ===" -ForegroundColor Cyan
& $py (Join-Path $EMSPath "scripts\Validate-Wave2C1-CTRL072.py") --evidence (Join-Path $out "ctrl072_evidence.json") --report (Join-Path $out "validation_report.json")
if($LASTEXITCODE-ne 0){Fail "CTRL-072 validation failed."}

Write-Host "`n=== Qualify Wave 2C queue ===" -ForegroundColor Cyan
& $py (Join-Path $EMSPath "scripts\Qualify-Wave2C1-CTRL072.py") --ems-root $EMSPath --wave2c-queue $queue --evidence (Join-Path $out "ctrl072_evidence.json") --out (Join-Path $out "remediation_queue.qualified.csv")
if($LASTEXITCODE-ne 0){Fail "CTRL-072 qualification failed."}

Write-Host "`nWave 2C.1 complete. No evidence promoted." -ForegroundColor Green
