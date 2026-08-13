[CmdletBinding()]
param([string]$EMSPath="C:\temp\standars\ems")

$ErrorActionPreference="Stop"
function Fail([string]$m){ throw "WAVE 2C.1b BLOCKED: $m" }

$branch=(git -C $EMSPath branch --show-current).Trim()
if($branch-ne"feature/wave2c-remediation"){
    Fail "Expected feature/wave2c-remediation; current=$branch"
}

$py=$null
if($env:VIRTUAL_ENV){
    $candidate=Join-Path $env:VIRTUAL_ENV "Scripts\python.exe"
    if(Test-Path $candidate){$py=$candidate}
}
if(-not $py){
    $cmd=Get-Command python -ErrorAction SilentlyContinue
    if($cmd){$py=$cmd.Source}
}
if(-not $py){ Fail "No usable Python interpreter found." }

$spec=Join-Path $EMSPath "registry\wave2c1b_ctrl072_reconciliation_spec.json"
$out=Join-Path $EMSPath "generated\wave2c\ctrl072-reconciliation"
$queue=Join-Path $EMSPath "generated\wave2c\remediation_queue.csv"

New-Item -ItemType Directory -Path $out -Force|Out-Null

if(-not(Test-Path $queue)){ Fail "Wave 2C remediation queue not found." }

Write-Host "=== Wave 2C.1b provenance reconciliation ===" -ForegroundColor Cyan

& $py (Join-Path $EMSPath "scripts\Reconcile-Wave2C1b-CTRL072.py") `
    --ems-root $EMSPath `
    --spec $spec `
    --outdir $out

if($LASTEXITCODE-ne 0){ Fail "CTRL-072 provenance reconciliation failed." }

Write-Host "`n=== Validate reconciled evidence ===" -ForegroundColor Cyan

& $py (Join-Path $EMSPath "scripts\Validate-Wave2C1b-CTRL072.py") `
    --evidence (Join-Path $out "ctrl072_reconciliation_evidence.json") `
    --report (Join-Path $out "validation_report.json")

if($LASTEXITCODE-ne 0){ Fail "CTRL-072 reconciliation validation failed." }

Write-Host "`n=== Update Wave 2C qualified queue ===" -ForegroundColor Cyan

& $py (Join-Path $EMSPath "scripts\Update-Wave2C1b-QualifiedQueue.py") `
    --queue $queue `
    --evidence (Join-Path $out "ctrl072_reconciliation_evidence.json") `
    --out (Join-Path $out "remediation_queue.qualified.csv")

if($LASTEXITCODE-ne 0){ Fail "CTRL-072 queue qualification update failed." }

Write-Host "`nPASS: Wave 2C.1b qualification complete. No promotion performed." -ForegroundColor Green
