[CmdletBinding()]
param(
    [string]$EMSPath="C:\temp\standars\ems",
    [switch]$Promote
)

$ErrorActionPreference="Stop"
function Fail([string]$m){throw "WAVE 2C.1c BLOCKED: $m"}

$branch=(git -C $EMSPath branch --show-current).Trim()
if($branch-ne"feature/wave2c-remediation"){
    Fail "Expected feature/wave2c-remediation; current=$branch"
}

if(-not $Promote){
    Write-Host "Promotion not requested." -ForegroundColor Yellow
    Write-Host "Review Wave 2C.1b evidence first, then run:"
    Write-Host "  .\scripts\Run-Wave2C1c-CTRL072.ps1 -Promote"
    exit 0
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
if(-not $py){Fail "No usable Python interpreter found."}

$spec=Join-Path $EMSPath "registry\wave2c1c_ctrl072_promotion_spec.json"
$out=Join-Path $EMSPath "generated\wave2c\ctrl072-promotion"
$queue=Join-Path $EMSPath "generated\wave2c\remediation_queue.csv"
New-Item -ItemType Directory -Path $out -Force|Out-Null

Write-Host "=== Wave 2C.1c explicit CTRL-072 promotion ===" -ForegroundColor Cyan

& $py (Join-Path $EMSPath "scripts\Promote-Wave2C1c-CTRL072.py") `
    --ems-root $EMSPath `
    --spec $spec `
    --outdir $out

if($LASTEXITCODE-ne 0){Fail "CTRL-072 promotion failed."}

Write-Host "`n=== Validate promotion and remediation population ===" -ForegroundColor Cyan

& $py (Join-Path $EMSPath "scripts\Validate-Wave2C1c-CTRL072.py") `
    --ems-root $EMSPath `
    --record (Join-Path $out "promotion_record.json") `
    --queue $queue `
    --report (Join-Path $out "validation_report.json")

if($LASTEXITCODE-ne 0){Fail "CTRL-072 promotion validation failed."}

Write-Host "`n=== Rerun higher-scope / inheritance evaluation ===" -ForegroundColor Cyan

$inheritance=Join-Path $EMSPath "scripts\Run-Wave2B1-Inheritance.ps1"
if(Test-Path $inheritance){
    & $inheritance
    if($LASTEXITCODE-ne 0){Fail "Higher-scope inheritance rerun failed."}
}else{
    Write-Host "Run-Wave2B1-Inheritance.ps1 not found; inheritance rerun skipped." -ForegroundColor Yellow
}

Write-Host "`nPASS: CTRL-072 promoted and Wave 2C remediation population reduced to seven." -ForegroundColor Green
